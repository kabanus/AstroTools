from plotInt import Iplot
from fitshandler import Response,Data
from scipy.optimize import curve_fit
from itertools import izip

CHANNEL = 0
ENERGY  = 1
WAVE    = 2

class Fitter(object):
    class badPlotType(Exception): pass
    class NotAModel(Exception): pass
    class badZoomRange(Exception): pass
    class dataResponseMismatch(Exception): pass
    class noIgnoreBeforeLoad(Exception): pass
    class errorNotConverging(Exception): pass
    class newBestFitFound(Exception): pass

    def __init__(self, data = None, resp = None):
        self.ptype     = CHANNEL
        self.models    = []
        self.current   = None
        self.binfactor = 1
        self.result    = []
        self.xstart    = None
        self.xstop     = None
        self.ystart    = None
        self.ystop     = None
        if data is not None:
            self.loadData(data)
        if resp is not None:
            self.loadResp(resp)

    def loadResp(self,resp):
        self.resp = Response(resp)
        self.checkLoaded()
        self.resp_file = resp

    def loadData(self,data):
        self.data  = Data(data)
        if self.data.resp != None:
            self.loadResp(self.data.resp)
        self.checkLoaded()
        self.plot()
        self.data_file = data

    def checkLoaded(self):
        try: 
            if len(self.data.channels) != len(self.resp.matrix):
                raise self.dataResponseMismatch(len(self.data.channels),len(self.resp.matrix))
        except AttributeError: pass
  
    def ignore(self, minX, maxX):
        try:
            self.checkLoaded()
            for fitshandler in (self.data,self.resp):
                #Need to reset generator
                if self.ptype == CHANNEL: channels = range(minX,maxX+1)
                if self.ptype == ENERGY : channels = self.resp.energy(ignore = (minX, maxX))
                if self.ptype == WAVE: channels    = self.resp.energy(forwl = True, ignore = (minX, maxX))
                fitshandler.ignore(channels)
            self.plot()
        except AttributeError:
            raise self.noIgnoreBeforeLoad()
    def zoomto(self, xstart = None, xstop = None, ystart = None, ystop = None):
        self.xstart = xstart
        self.xstop  = xstop
        self.ystart = ystart
        self.ystop  = ystop
        self.plot()
    def reset(self, zoom = True, ignore = True):
        if zoom:
            self.xstart = None
            self.xstop  = None
            self.ystart = None
            self.ystop  = None
        if ignore:
            for fitshandler in (self.data,self.resp):
                try:
                    fitshandler.reset()
                except AttributeError: pass
                self.plot()
        self.plot()

    def chisq(self):
        return sum(((self.data.cts[i]-self.result[i])**2/self.data.errors[i]**2 for i in range(len(self.data.channels))))

    def reduced_chisq(self):
        return self.chisq()/(len(self.data.channels)-len(self.getThawed()))

    def append(self, *args):
        for model in args:
            try:
                model._calculate
                model.freeze
                model.thaw
                model.calculate
                model.setp
                self.models.append(model)
            except AttributeError: raise self.NotAModel(model,model.__class__)
        if len(self.models):
            self.activate()

    def delete(self,index):
        #Prevent bad name access
        self.models[index] = None

    def activate(self, index = -1):
        self.current = self.models[index]
        self.currentindex = index

    def nameModel(self, index,name):
        setattr(self,name,lambda: self.activate(index))

    def transmit(self, table):
        self.data.transmit(table)
        self.plot()
        self.transmit_file = table

    def energies(self):
        return self.resp.ebinAvg

    def tofit(self, elist, *args):
        res = self.current.tofit(elist,*args)
        return self.resp.convolve_channels(res)

    def fit(self):
        model = self.current
        args  = self.initArgs()
       
        bestfit,self.errs = curve_fit(self.tofit,self.energies(),self.data.cts,
                                                  p0=args,sigma=self.data.errors)
        self.stderr  = dict(izip(model.getThawed(),
                        [self.errs[j][j]**0.5 for j in range(len(self.errs))]))
       
        self.calc(dict(izip(model.getThawed(),bestfit)))

    def thaw(self, *params):
        self.current.thaw(*params)
    def getThawed(self):
        return self.current.getThawed()
    def initArgs(self):
        return self.current.initArgs()
    def freeze(self, *params):
        self.current.freeze(*params)
    def setp(self,pDict):
        self.current.setp(pDict)
    def calc(self,pDict = {}):
        self.setp(pDict)
        self.result = self.tofit(self.energies())
        self.plot()

    def rebin(self, count):
        self.binfactor = count
        self.plot()

    def setplot(self, plotType):
        if plotType not in [ENERGY, CHANNEL, WAVE]: raise self.badPlotType(plotType)
        self.ptype = plotType
        self.plot()

    def error(self, index, param, epsilon = 0.05, acceleration = 0.3):
        return (self.oneSidedError(index,param,-1,epsilon,acceleration),
                self.oneSidedError(index,param, 1,epsilon,acceleration))

    #epsilon is allowed deviation from '1' when comparing chisq
    def oneSidedError(self, index, param, direction, epsilon, acceleration):
        iparam  = (index,param)
        thawed  = iparam in self.getThawed()
        self.thaw(iparam)
        save    = dict(izip(self.getThawed(),self.initArgs()))
        self.freeze(iparam)
        bestchi = self.chisq()
        backp   = self.current[iparam]
        needfit = self.current.getThawed()
        limit = 10
        oldchi = bestchi
        while abs(oldchi-bestchi) < 1.0: 
            if not self.current[iparam]: 
                self.setp({iparam: direction*0.001})
                if not self.current[iparam]: break
            next_calculation = self.current[iparam]*(1+direction*acceleration)
            self.setp({iparam:next_calculation})
            #Check model limiter
            if self.current[iparam] != next_calculation: break
            self.calc()
            if needfit: self.fit()
            tmp = self.chisq()
            if tmp < bestchi:
                if thawed: self.thaw(iparam)
                raise self.newBestFitFound()
            if tmp == oldchi: 
                limit -= 1
            else: oldchi = tmp
            if not limit: 
                if thawed: self.thaw(iparam)
                self.calc(save)
                raise self.errorNotConverging()

        current = self.chisq()
        frontp  = self.current[iparam]
        while abs(abs(current - bestchi)-1) > epsilon and backp != frontp:
            next_calculation = (frontp+backp)/2.0
            self.setp({iparam:next_calculation})
            #Check model limiter
            if self.current[iparam] != next_calculation: break
            self.calc()
            if needfit: self.fit()
            current = self.chisq()
            if current < bestchi:
                if thawed: self.thaw(iparam)
                raise self.newBestFitFound()
            if abs(current-bestchi) < 1:
                backp = self.current[iparam]
            else:
                frontp = self.current[iparam]
       
        result = self.current[iparam]
        self.calc(save)
        if thawed: self.thaw(iparam)
        return result - self.current[iparam]

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
            if self.ptype == ENERGY:
                dataPlot = self.resp.energy(dataPlot)
            if self.ptype == WAVE:
                dataPlot = self.resp.wl(dataPlot)
            self._plotOrSave(save,(),'scatter',list(dataPlot))
        else:
            resultPlot = self.data.rebin(self.binfactor,self.result)
            if self.ptype == ENERGY:
                dataPlot = self.resp.energy(dataPlot)
                resultPlot = self.resp.energy(resultPlot)
            if self.ptype == WAVE:
                dataPlot = self.resp.wl(dataPlot)
                resultPlot = self.resp.wl(resultPlot)
            self._plotOrSave(save,(),list(resultPlot),'scatter',list(dataPlot))
        if save  != None: return

        if self.ptype == CHANNEL:
            Iplot.x.label('Channel')
            Iplot.y.label('ph s$^{-1}$ channel$^{-1}$')
        if self.ptype == ENERGY:
            Iplot.x.label('keV')
            Iplot.y.label('ph s$^{-1}$ keV$^{-1}$')
        if self.ptype == WAVE:
            Iplot.x.label('$\AA$')
            Iplot.y.label('ph s$^{-1}$ $\AA^{-1}$')

        Iplot.x.resize(self.xstart,self.xstop)
        Iplot.y.resize(self.ystart,self.ystop)
        
