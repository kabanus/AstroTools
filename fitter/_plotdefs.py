from plotInt     import Iplot,plt
from numpy       import array
from itertools   import izip
from fitshandler import Data
from models      import ibifit #For labeling

CHANNEL = 0
ENERGY  = 1
WAVE    = 2
keVAfac = 12.39842

class badPlotType(Exception): pass
class badZoomRange(Exception): pass

def toggleIonLabels(self,mode = None):
    if mode is None:
        self.labelions = 1 if not self.labelions else 0
    else: self.labelions = mode
    self.plot(user = False)

def initplot(self):
    Iplot.init()
    loadIonPositions(self)

def loadIonPositions(self):
    ions = ibifit(ncut=1).ions
    self.ionlocations = sorted(sum([[[t[0],ion+a] 
        for a,t in zip(('$\\alpha$','$\\beta$','$\\gamma$'),ions[ion].l + ions[ion].e)]
            for ion in ions],[]))

def zoomto(self, xstart = None, xstop = None, ystart = None, ystop = None):
    self.xstart = xstart
    self.xstop  = xstop
    self.ystart = ystart
    self.ystop  = ystop
    Iplot.x.resize(self.xstart,self.xstop)
    Iplot.y.resize(self.ystart,self.ystop)
    self.plot()

def rebin(self, count):
    self.binfactor = count
    self.plot(user = False, keepannotations = True)

def labelAxis(self,axis,label):
    if axis == 'y':
        self.axisOverride[1] = label
    if axis == 'x':
        self.axisOverride[0] = label

def unlabelAxis(self):
    self.axisOverride = [None,None]

def setplot(self, plotType):
    if plotType not in [self.ENERGY, self.CHANNEL, self.WAVE]: 
        raise self.badPlotType(plotType)
    self.ptype = plotType
    self.ionlabs.sort(key = lambda x: x[plotType])
    self.plot(user = False)

def _embedz(z,ptype):
    if ptype == WAVE:
        exec('shift = lambda x: x/(1.0+'+str(z)+')')
    elif ptype == ENERGY:
        exec('shift = lambda x: x*(1.0+'+str(z)+')')
    else:
        shift = None
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

_writePlot = lambda table: "\n".join((" ".join((str(x) for x in line)) for line in table))
def _plotOrSave(save = None,model = None, data = None):
    if save is None:
        if data is not None:
            Iplot.plotCurves(data,stepx = 0,scatter = True,s=1)
        if model is not None:
            Iplot.plotCurves(model,chain=True)
    else:
        fd = open(save,'w')
        table = []
        if data is not None: 
            if model is not None:
                fd.write(_writePlot((d+m[1:] for d,m in zip(data,model))))
            else:
                fd.write(_writePlot(data))
        if model is not None: 
                fd.write(_writePlot(model))
        fd.close()

def plot(self, save = None, user = True, keepannotations = False):
    Iplot.clearPlots(keepannotations=keepannotations)
    model = None
    if not user and self.plotmodel:
        model = self.plotmodel
    else: self.plotmodel = False

    area = self.area
    if not self.area.any():
        area = 1
    if model is None:
        plots = [self.data.getPlot(self.binfactor,area)]
        if len(self.result) == len(self.data.channels):
            plots.append(zip(Data.ndrebin(self.data.channels,self.binfactor),Data.rebin(self.result,self.binfactor,scale = lambda x=area:x)))
        for i in range(len(plots)):
            if self.ptype == self.ENERGY:
                plots[i] = self.resp.energy(plots[i])
            if self.ptype == self.WAVE:
                plots[i] = self.resp.wl(plots[i])
            if self.dataz != None:
                plots[i] = _shiftlist(plots[i],self.dataz,self.ptype)
        if self.labelions:
            plots[0] = list(plots[0])
        if len(plots) == 1:
            _plotOrSave(save,data=plots[0])
        else:
            _plotOrSave(save,data=plots[0],model=plots[1])
    else:
        if len(model[0]) > 2:
            if self.ptype == self.WAVE:   model = list(self.resp.wl(model,True))
            if self.ptype == self.ENERGY: model = list(self.resp.energy(model,True))
        else:
            self.ptype = self.ENERGY
        _plotOrSave(save,model=model)
    if save is not None: return

    if self.axisOverride.count(None) < 2:
        Iplot.x.label(str(self.axisOverride[0]))
        Iplot.y.label(str(self.axisOverride[1]))
    else:
        _labelaxes(self,model)

    if self.axisz != None:
        Iplot.secondAxis(_embedz(self.axisz,self.ptype))

    y = self.ystart
    if self.ystart == None: y = 0
    Iplot.x.resize(self.xstart,self.xstop)
    Iplot.y.resize(y,self.ystop)
     
    if not keepannotations and self.labelions > 0:
        labels = []
        posits = []
        ymax   = Iplot.y.get_bounds()[1]
        yindex = 1+(self.ptype!=self.CHANNEL)
        start,stop = Iplot.x.get_bounds()
        totaloffset = (0,0)
        for label in self.ionlabs:
            if label[self.ptype] > stop : break
            if label[self.ptype] < start or label[3] < 0: continue
            xindex = label[3]//self.binfactor
            if plots[0][xindex][yindex+1]  == float('inf'): continue
            labels.append(label[-1])
            yoffset = plots[0][xindex][yindex+1]
            if totaloffset[1] < yoffset*5: totaloffset = (0,5*yoffset)
            posits.append((label[self.ptype],min(plots[0][xindex][yindex]+yoffset,ymax)))
        if labels:
            Iplot.annotate(labels,posits,slide=(1,1),offset=totaloffset)

