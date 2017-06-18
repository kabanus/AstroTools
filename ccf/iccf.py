#!/usr/bin/python
#Class to run interactive CCF calculations.
#Uses the CCF and interpolation module. 
import sys 
sys.path.append('/home/uperetz/sources/py-modules')
from ccfdefs import PICCF
from interpolations import Curve
from plotInt import plt, Iplot
from binpeak import Phistogram
import randomizers
import code

class ICCF:
    def __init__( self, LC1 = None, LC2  = None ):
        LCs = []
        names = ("First","Second")
        old = None
        for curve,i in zip((LC1,LC2),(0,1)):
            while True:
                try:
                    if curve: LCfile = curve
                    else: 
                        if i and not LC1 and not sys.stdin.isatty(): 
                            print("-I- Only got first curve!")
                        LCfile = str(input('-->' + names[i] + ' light curve: '))
                        if not sys.stdin.isatty():
                            print(("Getting curve from file: " + LCfile)) 
                    LC = Curve([[float(x) for x in y.split(" ")] 
                                for y in open(LCfile).read().strip('\n').split("\n")],3)
                    LCs.append(sorted(LC,key = lambda x: x[0]))
                    break 
                except KeyboardInterrupt:
                    raise
                except (IOError, Curve.LengthError) as e:
                    if not sys.stdin.isatty(): sys.stdin = open("/dev/tty") 
                    print(("-E- Got error: %s"%e))
                    print(("-E- Bad LC file. Please make sure file exists and has " +
                          "3 space delimited floating point columns."))
                    curve = None
                    raise
        self.LCS = LCs
    
    #Generate multiple CCFs randomly sampled from the same curves.
    #This is used to create the 'lagerror'. k is size of sample.
    #The default to sample randomizer is 90% of points.
    def ccfSample(self, k = 10):
        self.sample = []
        for _ in range(k):
            firstLC = randomizers.points(randomizers.sampleWithRepeat(self.LCS[0]))
            seconLC = randomizers.points(randomizers.sampleWithRepeat(self.LCS[1]))
            self.sample.append(PICCF(firstLC,seconLC))

    def plotSmoothCCF(self, width=10):
        Iplot.clearPlots()
        try:
            test = self.ccfTable
        except AttributeError:
            self.mkCCFTable()
        Iplot.plotCurves(Phistogram.smooth(self.ccfTable,width),autosize=False)
    
    #This is what calculates the actual lag. Takes the sample. 
    def calcError(self, start, end, binsize, peakError = Phistogram.gaussPeakError):
        Phistogram.binsize = binsize
        self.peaks = [] 
        try:
            for table in self.tables:
                st = 0
                en = len(table)
                while table[st  ][0] < start: st += 1
                while table[en-1][0] > end:   en -= 1
                self.peaks.append(max(table[st:en],key = lambda x: x[1]))
                self.peaks.sort()

                self.errors = peakError(self.peaks)
            return self.errors
        except AttributeError:
            print("-E- Tables not created yet!")

    def makeTables( self, step = None ):
        try: self.tables = [x.calcTable(step) for x in self.sample]
        except AttributeError:
            print("-I- No sample created, generating using defaults.")
            self.ccfSample()
            self.tables = [x.calcTable(step) for x in self.sample]

    @staticmethod
    def help():
        print("===================================================================")
        print("-I- This is an interactive class for calculating correlations.")
        print("")
        print("-I- Use Iccf=ICCF([lc1,lc2]) to read in the light  curves and")
        print("-I- begin work. If arguments are not provided you will be ask-")
        print("-I- -ed for them manually.")
        print("-I- ")
        print("-I- You can then use Iccf.function() for:")
        print("-I- ccfSample       = Generates a random sample of k (default 10) c-")
        print("-I-                   -cfs")
        print("-I- makeTables      = Generates tables from sample in Iccf.tables.")
        print("-I- calcError       = Generate a list of peaks, sorted in Iccf.peak-")
        print("-I-                   -s. Next group similar peaks  from  different ")
        print("-I-                   tables, and generate an error using peakError ")
        print("-I-                   argument, defaulting to entire tau range. The ")
        print("-I-                   amount of agreeing tables is also given.")
        print("-I-                   Note this function will generate the tables if") 
        print("-I-                   not done so already, with  default  step. This")  
        print("-I-                   step is maxTime/maxlen(curve1,curve2).") 
        print("-I- help            = Your looking at it.")
        print("-I- plotMyCurves    = Plot generated tables. Accepts a boolean indi-")
        print("-I-                   -cating reflection (defaults to True.)")
        print("-I- getCCF          = Return original CCF.") 
        print("-I- mkCCFTable      = Generate points for CCF in ccfTable.") 
        print("-I- plotSmoothCCF   = Use to determine width for peak locator.")
        print("-I- exportAllPlots  = Save all attributes as plots of type <type>, wh-") 
        print("-I-                   -ich defaults to 'ps'. 'force' will create all.")
        print("-I-                   list is: LCs, entire sample, all peaks, piccf.")
        print("-I- This module contains also imports the classes Phistogram and Iplot, use Phistogram/Iplot.help()")
        print("-I- for additional helpful commands.")
        print("===================================================================")

    def getCCF(self):
        self.ccf = PICCF(*self.LCS)
        return self.ccf

    def mkCCFTable(self, step = None):
        try: self.ccfTable = self.ccf.calcTable(step)
        except AttributeError:
            self.getCCF()
            self.ccfTable = self.ccf.calcTable(step)

    def exportPlot(self, arg, maker = lambda: -1, ptype='ps', mparams = [], ylab="",xlab="" ):
        Iplot.clearPlots()
        Iplot.x.label(xlab)
        Iplot.y.label(ylab)
        try:
            try:
                Iplot.plotCurves(*self.__dict__[arg],autosize=False)
            except KeyError:
                if type(mparams) is not list: mparams = [mparams]
                if maker(*mparams) == -1: return
                Iplot.plotCurves(*self.__dict__[arg],autosize=False)
        except TypeError:
            Iplot.plotCurves(self.__dict__[arg],autosize=False)
        Iplot.axes.yaxis.grid()
        plt.savefig(arg + '.' + ptype,bbox_inches=0)

    def exportAllPlots(self, force=True, ptype='ps', **kwargs):
        if force == 'help' or force == '-help' or force == '-h':
            print('-I- exportAllPlots(force make, image type, errorp=(start,end,binsize), [tablep=step, ccfp=step])')
            return
        try:
            if len(kwargs['errorp']) < 3:
                raise KeyError() 
        except KeyError:
                print('-E- Must provide at least 3 error paramters: errorp=(start,end,binsize).')
                return

        makers = (None,None,None,None) 
        if force:
            makers = (self.makeTables, lambda: -1, self.calcError,self.mkCCFTable)
            try: params = [kwargs['tablep'],[],kwargs['errorp']] 
            except KeyError: params = [[],[],kwargs['errorp']]
            try: params.append(kwargs['ccfp'])
            except KeyError: params.append([])

        plt.ioff()
        self.exportPlot('tables'  ,makers[0],ptype,params[0],xlab='Day offset',ylab='$\\tau$')
        self.exportPlot('LCS'     ,makers[1],ptype,params[1],xlab='JD',ylab='Flux [au]')
        #Stupidly the axis do not refresh for smaller number
        self.exportPlot('ccfTable',makers[3],ptype,params[3],xlab='Day offset',ylab='$\\tau$')
        self.exportPlot('ccfTable',makers[3],ptype,params[3],xlab='Day offset',ylab='$\\tau$')
        try: Iplot.plotCurves(self.peaks,autosize=False,scatter=True)
        except AttributeError: 
            self.calcError(*params[2])
            Iplot.plotCurves(self.peaks,autosize=False,scatter=True)
        Iplot.plotCurves(*self.tables,autosize=False)
        Iplot.x.label ='Day offset'
        Iplot.y.label ='$\\tau$'
        plt.savefig('PeaksOnSample.'+ptype)
        Iplot.plotCurves(self.peaks,autosize=False,scatter=True)
        Iplot.plotCurves(self.ccfTable,autosize=False)
        plt.xlabel('Day offset')
        plt.ylabel('$\\tau$')
        plt.savefig('PeaksOnCCF.'+ptype)
        Iplot.clearPlots()
        Iplot.plotCurves(Phistogram.rebin(self.peaks),autosize=False,histogram=True)
        plt.xlabel('Day offset')
        plt.ylabel('Amount in sample')
        plt.savefig('ccpd.'+ptype)
        Iplot.clearPlots()
        plt.ion()
    
    def plotCCPD(self):
        Iplot.clearPlots()
        Iplot.plotCurves(Phistogram.rebin(self.peaks),autosize=False,scatter=True)

    def plotMyCurves(self):
        Iplot.plotCurves(*self.tables,autosize=False)

INTERACT = False
if not sys.stdin.isatty():
    try:
        param = input()
        while param != '':
            if param == "force_interact":
               INTERACT = True
            else:
                sys.argv.append(param)
            param = input()
    except EOFError: pass

#Non-interactive run
Iplot.init()
err = False
if sys.argv[0]:
    print("===================================================================")
    try:
        try: Iccf = ICCF(sys.argv[1],sys.argv[2])
        except IndexError: 
            try: 
                Iccf = ICCF(sys.argv[1])
                sys.argv.pop(0)
            except IndexError: 
                Iccf = ICCF()
    except BaseException as e:
        print(("\n\n-E- Failed to create iccf object, please do so yourself (see help). To see help use ICCF.help() - failed with error:\n-E- '" + str(e) +"'"))
        print("-I- Usage: iccf.py [LC1 LC2 [PeakStart PeakEnd binsize [samplesize] [tablestep]]]")
        err = True
    else:
        print("-I- ICCF object created in Iccf. Use Iccf.help() to get started.")
    print("===================================================================")
    if 'force_interact' in sys.argv:
        sys.argv.pop(sys.argv.index('force_interact'))
        INTERACT = True
    if not err and len(sys.argv) > 5:
        try: Iccf.ccfSample(int(sys.argv[6]))
        except IndexError: Iccf.ccfSample()
        try: Iccf.makeTables(float(sys.argv[7]))
        except IndexError: Iccf.makeTables()
        errp = [float(arg) for arg in sys.argv[3:6]]
        Best,sigma,length = Iccf.calcError(*errp)
        print('-I- Result:', end=' ')
        print('-I- Best guess:',Best)
        print('-I- Confidence interval:',sigma)
        print('-I- Number of bins used:',length)
        Iccf.exportAllPlots(errorp=errp,ptype='pdf')
    else:
        INTERACT = True
    if (len(sys.argv) <= 5 and sys.stdin.isatty()) or INTERACT:
        if INTERACT: sys.stdin = open("/dev/tty")
        code.interact(local=locals())

