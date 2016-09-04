class Fitter(object):
    CHANNEL = 0
    ENERGY  = 1
    WAVE    = 2

    def __init__(self, data = None, resp = None):
        self.ptype     = self.CHANNEL
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
    
    #Exceptions
    from _datadefs import dataResponseMismatch, noIgnoreBeforeLoad
    from _modeling import NotAModel
    from _error    import errorNotConverging, newBestFitFound
    from _plotdefs import badPlotType, badZoomRange

    #Methods
    from _datadefs import loadResp, loadData, checkLoaded, transmit, ignore, reset
    from _modeling import chisq,reduced_chisq,append,delete,activate,nameModel,energies,tofit,fit
    from _error    import error,oneSidedError,slide_away,binary_find_chisq,run_away,insert_and_continue
    from _plotdefs import zoomto,rebin,setplot,_plotOrSave,plot

    #Model wrappers
    def thaw(self, *params):
        self.current.thaw(*params)
    def getThawed(self):
        return self.current.getThawed()
    def getParams(self):
        return list(self.current.getParams())
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

