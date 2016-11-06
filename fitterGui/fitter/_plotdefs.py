from plotInt import Iplot
from numpy   import array
from itertools import izip

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
    self.plot(user = False)

def rebin(self, count):
    self.binfactor = count
    self.plot(user = False)

def setplot(self, plotType):
    if plotType not in [self.ENERGY, self.CHANNEL, self.WAVE]: 
        raise self.badPlotType(plotType)
    self.ptype = plotType
    self.plot(user = False)

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
    self.plot(user = False)

def removeShift(self,data = False):
    if not data:
        self.axisz = None
        Iplot.hideSecondAxis()
    else:
        self.dataz = None
    self.plot(user = False)

def toggle_area(self):
    if self.area.any():
            self.area = array(())
    else: self.area = self.resp.eff
    self.plot(user = False)

def _shiftlist(l,z,ptype):
    shift = _embedz(z,ptype)
    return ([shift(x[0])]+x[1:] if shift(x[0]) != '' else x for x in l)

def _labelaxes(self, model):
    add = ''
    if model or self.area.any(): add += ' cm$^{-2}$'
    if self.ptype == self.CHANNEL:
        Iplot.x.label('Channel')
        if not model or len(model[0]) == 2:
            Iplot.y.label('ph s$^{-1}$ channel$^{-1}$'+add)
    if self.ptype == self.ENERGY:
        Iplot.x.label('keV')
        if not model or len(model[0]) == 2:
            Iplot.y.label('ph s$^{-1}$ keV$^{-1}$'+add)
    if self.ptype == self.WAVE:
        Iplot.x.label('$\AA$')
        if not model or len(model[0]) == 2:
            Iplot.y.label('ph s$^{-1}$ $\AA^{-1}$'+add)

def plotModel(self,start = None,stop = None,delta = None):
    if start == None: start = self.plotmodel[0][0]
    if stop  == None: stop  = self.plotmodel[-1][0]
    if delta == None: delta = self.plotmodel[1][0]-self.plotmodel[0][0]
    energies = array(
        [start+i*delta for i in range(1+int((stop-start)/delta))])
    model = self.current.tofit(energies)
    self.plotmodel = zip(energies,model)
    self.plot(user = False)

def plotDiv(self, other = None):
    if other != None: self.div(other)
    self.plotmodel = self.division
    self.plot(user = False)

_writePlot = lambda self,table: "\n".join((" ".join((str(x) for x in line)) for line in table))
def _plotOrSave(save,*args,**kwargs):
    if save == None:
        if 'scatter' in kwargs: kwargs['s'] = 1
        kwargs['stepx'] = 0
        Iplot.plotCurves(*args,**kwargs)
    else:
        fd = open(save,'w')
        fd.write('#Data\n')
        fd.write(_writePlot(args[-1]))
        if len(args) > 3:
            fd.write('\n#Model\n')
            fd.write(_writePlot(args[1]))
        fd.close()

def plot(self, save = None, user = True):
    Iplot.clearPlots()
    model = None
    if not user and self.plotmodel:
        model = self.plotmodel
    else: self.plotmodel = False

    if model == None:
        plots = []
        plots = [self.data.rebin(self.binfactor,eff=self.area)]
        if len(self.result) == len(self.data.channels):
            plots.append(self.data.rebin(self.binfactor,self.result,eff=self.area))
        for i in range(len(plots)):
            if self.ptype == self.ENERGY:
                plots[i] = self.resp.energy(plots[i])
            if self.ptype == self.WAVE:
                plots[i] = self.resp.wl(plots[i])
            if self.dataz != None:
                plots[i] = _shiftlist(plots[i],self.dataz,self.ptype)
        if len(plots) == 1:
            _plotOrSave(save,list(plots[0]),scatter=True)
        else:
            _plotOrSave(save,list(plots[0]),scatter=True)
            _plotOrSave(save,list(plots[1]),chain=True)
    else:
        if len(model[0]) > 2:
            if self.ptype == self.WAVE:   model = list(self.resp.wl(model,True))
            if self.ptype == self.ENERGY: model = list(self.resp.energy(model,True))
        else:
            self.ptype = self.ENERGY
        _plotOrSave(save,model)
    if save != None: return
    _labelaxes(self,model)

    if self.axisz != None:
        Iplot.secondAxis(_embedz(self.axisz,self.ptype))

    y = self.ystart
    if self.ystart == None: y = 0
    Iplot.x.resize(self.xstart,self.xstop)
    Iplot.y.resize(y,self.ystop)
    
