from plotInt import Iplot

CHANNEL = 0
ENERGY  = 1
WAVE    = 2

class badPlotType(Exception): pass
class badZoomRange(Exception): pass

def initplot(self):
    Iplot.init()

def zoomto(self, xstart = None, xstop = None, ystart = None, ystop = None):
    self.xstart = xstart
    self.xstop  = xstop
    self.ystart = ystart
    self.ystop  = ystop
    self.plot()

def rebin(self, count):
    self.binfactor = count
    self.plot()

def setplot(self, plotType):
    if plotType not in [self.ENERGY, self.CHANNEL, self.WAVE]: 
        raise self.badPlotType(plotType)
    self.ptype = plotType
    self.plot()

_writePlot = lambda self,table: "\n".join((" ".join((str(x) for x in line)) for line in table))
def _plotOrSave(save,*args):
    if save == None:
        Iplot.plotCurves(*args)
    else:
        fd = open(save,'w')
        fd.write('#Data\n')
        fd.write(_writePlot(args[-1]))
        if len(args) > 3:
            fd.write('\n#Model\n')
            fd.write(_writePlot(args[1]))
        fd.close()

def _embedz(z,ptype):
    if ptype == WAVE:
        exec('shift = lambda x: x/(1.0+'+str(z)+')')
    elif ptype == ENERGY:
        exec('shift = lambda x: x*(1.0+'+str(z)+')')
    else:
        shift = lambda x: ''
    return shift

def shift(self,z,data = False):
    if not data:
        self.axisz = z
    else:
        self.dataz = z
    self.plot()

def removeShift(self,data = False):
    if not data:
        self.axisz = None
        Iplot.hideSecondAxis()
    else:
        self.dataz = None
    self.plot()

def _shiftlist(l,z,ptype):
    shift = _embedz(z,ptype)
    return ([shift(x[0])]+x[1:] if shift(x[0]) != '' else x for x in l)

def _labelaxes(self):
    if self.ptype == self.CHANNEL:
        Iplot.x.label('Channel')
        Iplot.y.label('ph s$^{-1}$ channel$^{-1}$')
    if self.ptype == self.ENERGY:
        Iplot.x.label('keV')
        Iplot.y.label('ph s$^{-1}$ keV$^{-1}$')
    if self.ptype == self.WAVE:
        Iplot.x.label('$\AA$')
        Iplot.y.label('ph s$^{-1}$ $\AA^{-1}$')

def plot(self, save = None):
    Iplot.clearPlots()
    plots = [self.data.rebin(self.binfactor)]
    if len(self.result) == len(self.data.channels):
        plots.append(self.data.rebin(self.binfactor,self.result))
    for i in range(len(plots)):
        if self.ptype == self.ENERGY:
            plots[i] = self.resp.energy(plots[i])
        if self.ptype == self.WAVE:
            plots[i] = self.resp.wl(plots[i])
        if self.dataz != None:
            plots[i] = _shiftlist(plots[i],self.dataz,self.ptype)

    if len(plots) == 1:    
        _plotOrSave(save,(),'scatter',list(plots[0]))
    else:
        _plotOrSave(save,(),list(plots[1]),'scatter',list(plots[0]))
    if save != None: return

    _labelaxes(self)

    if self.axisz != None:
        Iplot.secondAxis(_embedz(self.axisz,self.ptype))

    y = self.ystart
    if self.ystart == None: y = 0
    Iplot.x.resize(self.xstart,self.xstop)
    Iplot.y.resize(y,self.ystop)
    
