from scipy.optimize import minimize
from numpy import float64,array,isinf
from numpy import append as ndappend
from utils import RomanConversion
from collections import defaultdict
from randomizers import points as rpoints
from plotInt import Iplot
import re

abundances = {
'he' : 8.51e-02,
'li' : 1.12e-11,
'be' : 2.40e-11,
'b'  : 5.01e-10,
'c'  : 2.69e-04,
'n'  : 6.76e-05,
'o'  : 4.90e-04,
'f'  : 3.63e-08,
'ne' : 8.51e-05,
'na' : 1.74e-06,
'mg' : 3.98e-05,
'al' : 2.82e-06,
'si' : 3.24e-05,
'p'  : 2.57e-07,
's'  : 1.32e-05,
'cl' : 3.16e-07,
'ar' : 2.51e-06,
'k'  : 1.07e-07,
'ca' : 2.19e-06,
'sc' : 1.41e-09,
'ti' : 8.91e-08,
'v'  : 8.51e-09,
'cr' : 4.37e-07,
'mn' : 2.69e-07,
'fe' : 3.16e-05,
'co' : 9.77e-08,
'ni' : 1.66e-06,
'cu' : 1.55e-08,
'zn' : 3.63e-08
}

class AMD(object):
    def __init__(self, table):
        data = []
        self._running_component = 0
        header = False
        for line in open(table):
            try:
                line = line.split()
                line = [line[0]] + [float64(x) for x in line[1:]]
            except ValueError:
                if not header:
                    self.ind = dict([(key.strip(),index) for index,key in enumerate(line)])
                    header = True
                    continue
                raise IOError('Bad xi table, more than pne header line!')
            data.append(line)
            
        self.fractions = defaultdict(lambda: defaultdict(dict))
        for xiline in data:
            xi = xiline[self.ind['ion_run']]
            for ion in self.ind:
                if ion in ('ion_run','delta_r','x_e','n_p','frac_heat_error'): continue
                try: 
                    elem,charge = ion.split('_')
                except ValueError: continue
                if charge =='p': print ion
                self.fractions[xi][elem][charge] = xiline[self.ind[ion]]
        self.fractions = dict(self.fractions)
        self.xiOrder   = sorted(self.fractions,key = self.xif)
        self.xiOrderF  = array([self.xif(xi) for xi in self.xiOrder])
               
    def readParams(self, fname):
        self.params = defaultdict(lambda: defaultdict(dict))
        self.errors = defaultdict(lambda: defaultdict(dict))
        for line in open(fname):
            line = re.split('\s+',line.strip())
            if len(line) <= 4: continue
            try: 
                (elem,charge), = self.getIons(line[1],split = True)
                component = line[0]
            except KeyError: continue
            self.params[component][elem][charge] = float(line[3])
            exec('self.errors[component][elem][charge] = '+line[4]) in locals()
        self.params = dict((k,dict(v)) for k,v in self.params.items())
        self.errors = dict((k,dict(v)) for k,v in self.errors.items())

        self.coefficients = dict()
        self.resVector    = dict()
        self.errVector    = dict()
        self.abundMap     = dict()
        self.abundMapN    = dict()
        for comp in self.params:
            self.coefficients[comp] = list()
            self.resVector[comp]    = list()
            self.errVector[comp]    = list()
            self.abundMap[comp]     = list()
            self.abundMapN[comp]    = list()
            abundCounter = 0
            for elem in self.params[comp]:
                self.abundMapN[comp].append(elem)
                for ion in self.params[comp][elem]:
                    self.coefficients[comp].append([(abundances[elem]*self.fractions[xi][elem][ion]) for xi in self.xiOrder])
                    self.resVector[comp].append(self.params[comp][elem][ion])
                    self.errVector[comp].append(self.errors[comp][elem][ion])
                    self.abundMap[comp].append(abundCounter)
                abundCounter += 1
        for c in self.coefficients: 
            a                    = array(self.coefficients[c])
            a[isinf(a)]          = 0
            self.coefficients[c] = a
            self.resVector[c]    = array(self.resVector[c])
            self.errVector[c]    = abs(array(self.errVector[c])).mean(axis=1)

        self._coeff  = dict() 
        self._xi     = dict()
        for comp in self.coefficients:
            self.rebinComp(comp)

    def rebinComp(self,comp,**kwargs):
        comp = str(comp)
        self.rebinXi(comp,**kwargs)
        self.redistributeCoefficients(comp,**kwargs)

    def _prepRebin(self,component,xiMin,xiMax,binSize = None):
        c = str(component)
        if binSize: binSize = int(round(binSize/(self.xiOrderF[1]-self.xiOrderF[0])))
        xiMax   = len(self.xiOrderF)-1 if xiMax is None else abs(self.xiOrderF-xiMax).argmin()
        xiMin   = 0                    if xiMin is None else abs(self.xiOrderF-xiMin).argmin()
        sh      = len(self.xiOrderF[xiMin:xiMax+1])
        L       = sh//binSize if binSize else len(self.resVector[component])
        bins    = binSize     if binSize else sh//L 
        extra   = sh-L*bins
        if extra >= L and extra > bins: raise ValueError("Bad bin size")
        return c,bins,extra,xiMin,xiMax

    def rebinXi(self,component,xiMin = None, xiMax = None, binSize = None):
        c,bins,extra,xiMin,xiMax = self._prepRebin(component,xiMin,xiMax,binSize)
        vec = self.xiOrderF[xiMin:xiMax+1]
        if extra > bins: 
            start = vec[:extra*(bins+1)].reshape(-1,bins+1).mean(axis=1) if extra else array(())
            final = vec[extra*(bins+1):]
        else:
            start = vec[:extra].mean(axis=0) if extra else array(())
            final = vec[extra:]
        self._xi[c] = ndappend(start,final.reshape(-1,bins).mean(axis=1)) if final.any() else start

    def redistributeCoefficients(self,component,xiMin = None, xiMax = None, binSize = None, distribution = None):
        c,bins,extra,xiMin,xiMax = self._prepRebin(component,xiMin,xiMax,binSize)
        arr   = self.coefficients[c][:,xiMin:xiMax+1]
        L     = len(self.resVector[component])
        if distribution is None: distribution = array([1 for _ in range(len(self.coefficients[c]))])
        if extra > bins: 
            start = arr[:,:extra*(bins+1)].reshape(L,-1,bins+1).sum(axis=2) if extra else array(()).reshape(L,0)
            final = arr[:,extra*(bins+1):]
        else:
            start = arr[:,:extra].sum(axis=1).reshape(L,1) if extra else array(()).reshape(L,0)
            final = arr[:,extra:]
        self._coeff[c] = ndappend(start,final.reshape(L,-1,bins).sum(axis=2),axis=1) if final.any() else start

    def AMDs(self,component,niter=3,marker='',**kwargs):
        c = str(component)
        kwargs['plot'] = False
        AMDS = [
            self.AMD(component,resV = array(rpoints(self.resVector[c],self.errVector[c])),**kwargs)
                for _ in range(niter)
        ]
        Iplot.init()
        Iplot.plotCurves(*AMDS,marker=marker)
        Iplot.ylog()
        Iplot.x.label('log $\\xi$')
        Iplot.y.label('$N_H$ $10^{18}$ cm$^2$')

    def AMDQuality(self,AMDlist,component,abundances=None,estimate = None):
        c = str(component)
        AMDArray = AMDlist
        if abundances:
            try: 
                AMDArray, abundances = AMDlist[:-abundances], AMDlist[-abundances:]
                abundArray = map(lambda x: abundances[x], self.abundMap[c])
            except TypeError:
                abundArray = map(lambda x: abundances[self.abundMapN[c][x]], self.abundMap[c])
        else: abundArray = [1 for _ in range(len(abundMap[c]))]
        est = self._coeff[c].dot(AMDArray)*abundArray
        objective = (est - self.resVector[c])/self.errVector[c]
        if estimate is not None: 
            if   estimate == 0: 
                return est
            elif estimate == 1:
                return est - self.resVector[c]
            elif estimate == 2:
                return (est - self.resVector[c])/self.resVector[c]
            return objective  

        return objective.dot(objective)

    def AMD(self,component, guess = None,plot = False, fitAbunds = True):
        c = str(component)
        a = len(set(self.abundMap[c])) if fitAbunds else None
        if guess is None:
            guess = [1 for _ in range(len(self._coeff[c][0]))]
            if fitAbunds: guess += [1e-4 for _ in range(a)]

        result = minimize(self.AMDQuality,guess,args=(c,a),bounds=[(0,None) for _ in range(len(guess))],method='slsqp',options={'maxiter':1000})
        self._last = result        
        if result.success:
            abunds = None
            NH = result.x
            if fitAbunds: NH, abunds = result.x[:-a], result.x[-a:]
            if plot:
                toplot = ndappend(self._xi[c].reshape(-1,1),NH.reshape(-1,1),axis=1)
                Iplot.init()
                Iplot.plotCurves(toplot,marker='o')
                Iplot.ylog()
                Iplot.x.label('log $\\xi$')
                Iplot.y.label('$N_H$ $10^{18}$ cm$^2$')
            dof = len(self.resVector[c])-len(guess)
            red = self._last['fun']/dof
            self._last.dof  = dof
            self._last.bins = len(self.resVector[c])
            self._last.pars = len(guess)
            print u"{0} parameters, {1} bins, {2} d.o.f, \u03C7\u00B2 = {3},and reduced {4}".format(
                len(guess),len(self.resVector[c]),dof,self._last['fun'],red)
            return NH,dict(zip(self.abundMapN[c],abunds))
        print 'Failed with '+ result.message
        return (None,None)

    def AMDEst(self,*components,**kwargs):
        Iplot.init()
        plotDict = defaultdict(int)
        legend = []
        result = []
        for component in components:
            c = str(component)
            legend.append('Component '+c)
            for elem in self.params[c]:
                for ion in self.params[c][elem]:
                    eIon = elem+'_'+ion
                    Xi = self.probableXi(eIon)
                    plotDict[self.xif(Xi)] += self.NH(eIon,Xi,self.params[c][elem][ion])
            result.append(sorted(plotDict.items()))
            Iplot.plotCurves(result[-1],chain=True,marker='o')
        try: legend = kwargs['labels']
        except KeyError: pass
        Iplot.legend(*legend, bbox_to_anchor=(1.1,1.1))
        Iplot.ylog()
        Iplot.y.label('log $N_H 10^{18} cm^2$')
        Iplot.x.label('log $\\xi$')
        if len(result) == 1: return result[0]
        return result

    def ionAMDEst(self,*components):
        Iplot.init()
        legend = []
        for component in components:
            c = str(component)
            e = lambda ion: elem+'_'+ion
            for elem in self.params[c]:
                legend.append(elem)
                curve = sorted([(self.xif(self.probableXi(e(ion))),
                                    self.NH(e(ion),self.probableXi(e(ion)),self.params[c][elem][ion]))
                            for ion in self.params[c][elem]])

                Iplot.plotCurves(curve,chain=True,marker='o')
        Iplot.ylog()
        Iplot.legend(*legend, bbox_to_anchor=(1.1,1.1))
        Iplot.y.label('d $N_H$')
        Iplot.x.label('log $\\xi$')
    
    def NI(self,ion,xi,NH):
        xi = self.getXi(xi)
        (elem,charge), = self.getIons(ion,split=True)
        return NH*self.fractions[xi][elem][charge]*abundances[elem]

    def NH(self,ion,xi,NI):
        xi = self.getXi(xi)
        (elem,charge), = self.getIons(ion,split=True)
        if type(charge) is int: charge = RomanConversion.toRoman(charge).lower()
        return NI/(self.fractions[xi][elem][charge]*abundances[elem])
   
    def probableXi(self,ion):
        (elem,charge), = self.getIons(ion,split=True)
        return max(((self.fractions[xi][elem][charge],xi)
                        for xi in self.fractions))[1]
  
    def plotModel(self,elem):
        charges = defaultdict(list) 
        for xi in self.fractions:
            for charge in self.fractions[xi][elem]:
                fxi = self.xif(xi)
                val = self.fractions[xi][elem][charge]
                charges[charge].append((fxi,val))
        Iplot.init()
        for charge in charges:
            Iplot.plotCurves(sorted(charges[charge]),chain = True)
        height = 0.45
        for charge in charges:
            xi = self.probableXi(self.writeIon(elem,charge))
            height = self.fractions[xi][elem][charge]
            fxi = self.xif(xi)
            Iplot.annotate((charge,),((fxi,height),),slide=(1,1))
        Iplot.x.label('log $\\xi$')
        Iplot.y.label('Ion Fraction')
        Iplot.title(elem.title())
    
    def getIons(self,*ions, **kwargs):
        try: split = kwargs['split']
        except KeyError: split = False
        for ion in ions:
            if ion not in self.ind or split == True:
                try:
                    try:
                        elem,charge = ion.split('_')
                    except ValueError:
                        elem,charge,_ = re.split('([0-9]+)',ion)
                        charge = RomanConversion.toRoman(int(charge)+1).lower()
                    ion    = self.writeIon(elem,charge)
                    if ion not in self.ind: raise ValueError
                except ValueError:
                    raise KeyError('No such Ion ('+ion+')!')
            yield (elem,charge) if split else ion

    def getXi(self,xi):
        try: 
            xi = "%.1f"%xi
            return 'logxi_'+xi
        except TypeError: pass
        return xi

    def xif(self,xi):
        return float(xi.split('_')[1])

    def writeIon(self,elem,charge):
        return elem + '_' + charge

