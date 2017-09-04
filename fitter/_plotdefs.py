from plotInt     import Iplot,plt
from numpy       import array, concatenate
from numpy       import append as ndappend

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
    ions = ibifit(ncut=3).ions
    suffix = ['$\\alpha$','$\\beta$','$\\gamma$']
    self.ionlocations = sorted(sum([[[t[0],ion+a,i] if i > 0.5 else [1000*keVAfac/t[0],ion,i]
        for i,a,t in zip(list(range(1,len(ions[ion].l)+1)) + [0.5,]*len(ions[ion].e),
                         suffix[:len(ions[ion].l)]   + ['' ,]*len(ions[ion].e),
                         ions[ion].l                 + ions[ion].e)]
            for ion in ions],[]))

def toggleLog(self,axis):
    if axis == 0: Iplot.xlog()
    if axis == 1: Iplot.ylog()

def zoomto(self, xstart = None, xstop = None, ystart = 0, ystop = None):
    self.xstart = xstart
    self.xstop  = xstop
    self.ystart = ystart
    self.ystop  = ystop
    Iplot.x.resize(self.xstart,self.xstop)
    Iplot.y.resize(self.ystart,self.ystop)

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

def setplot(self, plotType,plot = False):
    if plotType not in [self.ENERGY, self.CHANNEL, self.WAVE]: 
        raise self.badPlotType(plotType)
    if plotType != self.ptype:
        self.reset(ignore=False)
    self.ptype = plotType
    try: self.ionlabs.sort(key = lambda x: x[plotType])
    except AttributeError: pass
    self.plot(user = False)
    shifter = _embedz(self.axisz,self.ptype)
    if shifter is not None: Iplot.secondAxis(shifter)
    else: Iplot.hideSecondAxis()
    if plot:
        self.plot(user=False)

def _embedz(z,ptype):
    if z is None: return None
    if ptype == WAVE:
        shift = eval('lambda x: x/(1.0+'+str(z)+')')
    elif ptype == ENERGY:
        shift = eval('lambda x: x*(1.0+'+str(z)+')')
    else:
        shift = None
    return shift

def shift(self,z,data = False):
    plot = False
    if not data:
        self.axisz = z
        self.updateIonLabels(_embedz(-self.axisz,self.WAVE))
    else:
        self.dataz = z
        plot = True
    self.setplot(self.ptype,plot)

def removeShift(self,data = False):
    plot = False
    if not data:
        if self.axisz is None: return
        self.updateIonLabels()
        self.axisz = None
        Iplot.hideSecondAxis()
    else:
        if self.dataz is None: return
        self.dataz = None
        plot = True
    self.setplot(self.ptype,plot)

def toggle_area(self):
    if self.area.any():
            self.area = array(())
    else: self.area = self.resp.eff
    self.plot(user = False)

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
    self.plotmodel = list(zip(energies,model))
    self.plot(user = False)

def plotEff(self):
    Iplot.clearPlots()
    Iplot.plotCurves(concatenate((self.resp.ebinAvg.reshape(-1,1),self.resp.reff.reshape(-1,1)),axis=1),plotype="xy",markersize=1,marker='.')
    Iplot.x.label('KeV')
    Iplot.y.label('cm$^2$')

def plotDiv(self, other = None):
    if other != None: self.div(other)
    self.plotmodel = self.division
    self.plot(user = False)

_writePlot = lambda table: "\n".join((" ".join((str(x) for x in line)) for line in table))
def _plotOrSave(save = None,model = None, data = None):
    if save is None:
        if data is not None:
            plotype = "xdxydy" if len(data[0]) == 4 else "xydy"
            Iplot.plotCurves(data,stepx = 0,scatter = True,plotype=plotype,marker="+")
        if model is not None:
            Iplot.plotCurves(model,chain=True,plotype="xy",marker="+")
    else:
        fd = open(save,'w')
        table = []
        if data is not None: 
            if model is not None:
                fd.write(_writePlot(concatenate((data,model[:,1:]),axis=1)))
            else:
                fd.write(_writePlot(data))
        elif model is not None: 
                fd.write(_writePlot(model))
        fd.close()

def plot(self, save = None, user = True, keepannotations = False):
    Iplot.clearPlots(keepannotations=keepannotations,keepscale = True)
    model = None
    if not user and self.plotmodel:
        model = self.plotmodel
    else: self.plotmodel = False

    area = self.area
    if not self.area.any():
        area = 1
    if model is None:
        if not len(self.data.channels): return
        plots = [self.data.getPlot(self.binfactor,area)]
        if len(self.result) == len(self.data.channels):
            plots.append(ndappend(
                           Data.ndrebin(self.data.channels,self.binfactor).reshape(-1,1),
                           Data.rebin(self.result,self.binfactor,scale = lambda x=area:x).reshape(-1,1),axis=1))
        for i,plot in enumerate(plots):
            if self.ptype == self.ENERGY:
                plots[i] = self.resp.energy(plot)
            if self.ptype == self.WAVE:
                plots[i] = self.resp.wl(plot)
            if self.dataz != None:
                shifter = _embedz(self.dataz,self.ptype)
                if shifter is not None: 
                    plot[:,0] = shifter(plot[:,0])
        if len(plots) == 1:
            _plotOrSave(save,data=plots[0])
        else:
            _plotOrSave(save,data=plots[0],model=plots[1])
    else:
        if len(model[0]) > 2:
            if self.ptype == self.WAVE:   model = list(self.resp.wl(model,True))
            if self.ptype == self.ENERGY: model = list(self.resp.energy(model,True))
        else:
            if self.ptype == self.CHANNEL: self.ptype = self.ENERGY
            if self.ptype == self.WAVE:
                amodel = []
                for i in range(len(model)-1):
                    dE = abs(model[i+1][0]-model[i][0])
                    C  = model[i][1]
                    amodel.append((keVAfac/model[i][0], model[i][1]**2*C/keVAfac))
                model = amodel
        _plotOrSave(save,model=model)
    if save is not None: return

    if self.axisOverride.count(None) < 2:
        Iplot.x.label(str(self.axisOverride[0]))
        Iplot.y.label(str(self.axisOverride[1]))
    else:
        _labelaxes(self,model)

    y = self.ystart
    if self.ystart == None: y = 0
    Iplot.x.resize(self.xstart,self.xstop)
    Iplot.y.resize(y,self.ystop)
   
    if not keepannotations and self.labelions > 0:
        plots[0] = list(plots[0])
        while True:
            labels      = []
            posits      = []
            offsetfac   = 1
            ymax        = Iplot.y.get_bounds()[1]
            yindex      = 1+(self.ptype!=self.CHANNEL)
            start,stop  = Iplot.x.get_bounds()
            totaloffset = (0,0)
            ystop = float("-inf")
            for label in self.ionlabs:
                if label[-1] > self.labelions: continue
                if label[self.ptype] > stop : break
                if label[self.ptype] < start or label[3] < 0: continue
                xindex = label[3]//(self.binfactor*self.data.grouping)
                if plots[0][xindex][yindex+1]  == float('inf'): continue
                yoffset = plots[0][xindex][yindex+1]
                if yoffset*(offsetfac+1)+plots[0][xindex][yindex] >= ymax: continue
                if totaloffset[1] < offsetfac*yoffset: totaloffset = (0,offsetfac*yoffset)
                labels.append(label[-2])
                posits.append((label[self.ptype],plots[0][xindex][yindex]+yoffset))
            if labels:
                _,_,_,ystop = Iplot.annotate(labels,posits,slide=(1,1),
                                                offset=totaloffset,rotation=90)
            if ystop > ymax:
                Iplot.axes.texts = []
                Iplot.y.resize(stop=ystop)
            else: break

