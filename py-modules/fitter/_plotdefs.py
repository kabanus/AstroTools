from plotInt import Iplot

class badPlotType(Exception): pass
class badZoomRange(Exception): pass

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
    if plotType not in [self.ENERGY, self.CHANNEL, self.WAVE]: raise self.badPlotType(plotType)
    self.ptype = plotType
    self.plot()

_writePlot = lambda self,table: "\n".join((" ".join((str(x) for x in line)) for line in table))
def _plotOrSave(self, save,*args):
    if save == None:
        Iplot.plotCurves(*args)
    else:
        fd = open(save,'w')
        fd.write('#Data\n')
        fd.write(self._writePlot(args[-1]))
        if len(args) > 3:
            fd.write('\n#Model\n')
            fd.write(self._writePlot(args[1]))
        fd.close()

def plot(self, save = None):
    Iplot.clearPlots()
    dataPlot = self.data.rebin(self.binfactor)
    if len(self.result) != len(self.data.channels):
        if self.ptype == self.ENERGY:
            dataPlot = self.resp.energy(dataPlot)
        if self.ptype == self.WAVE:
            dataPlot = self.resp.wl(dataPlot)
        self._plotOrSave(save,(),'scatter',list(dataPlot))
    else:
        resultPlot = self.data.rebin(self.binfactor,self.result)
        if self.ptype == self.ENERGY:
            dataPlot = self.resp.energy(dataPlot)
            resultPlot = self.resp.energy(resultPlot)
        if self.ptype == self.WAVE:
            dataPlot = self.resp.wl(dataPlot)
            resultPlot = self.resp.wl(resultPlot)
        self._plotOrSave(save,(),list(resultPlot),'scatter',list(dataPlot))
    if save  != None: return

    if self.ptype == self.CHANNEL:
        Iplot.x.label('Channel')
        Iplot.y.label('ph s$^{-1}$ channel$^{-1}$')
    if self.ptype == self.ENERGY:
        Iplot.x.label('keV')
        Iplot.y.label('ph s$^{-1}$ keV$^{-1}$')
    if self.ptype == self.WAVE:
        Iplot.x.label('$\AA$')
        Iplot.y.label('ph s$^{-1}$ $\AA^{-1}$')

    Iplot.x.resize(self.xstart,self.xstop)
    Iplot.y.resize(self.ystart,self.ystop)
    
