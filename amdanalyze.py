from scipy.optimize import minimize
from numpy import float64,isnan,inf,array,isinf
from numpy import append as ndappend
from utils import closest,RomanConversion,nwise
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
        count = defaultdict(lambda: defaultdict(float))
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
        self.xiOrder = sorted(self.fractions,key = self.xif)
               
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
        for comp in self.params:
            self.coefficients[comp] = list()
            self.resVector[comp]    = list()
            self.errVector[comp]    = list()
            for elem in self.params[comp]:
                for ion in self.params[comp][elem]:
                    self.coefficients[comp].append([(abundances[elem]*self.fractions[xi][elem][ion]) for xi in self.xiOrder])
                    self.resVector[comp].append(self.params[comp][elem][ion])
                    self.errVector[comp].append(self.errors[comp][elem][ion])
        for c in self.coefficients: 
            a                    = array(self.coefficients[c])
            a[isinf(a)]          = 0
            self.coefficients[c] = a
            self.resVector[c] = array(self.resVector[c])
            self.errVector[c] = array(self.errVector[c])

        self._coeff  = dict() 
        self._xi     = dict()
        for comp in self.coefficients:
            self._coeff[comp] = self.redistributeCoefficients(comp)
            self._xi[comp]    = self.rebinVec(comp,array([self.xif(xi) for xi in self.xiOrder]))

    def _prepRebin(self,component,sh,params = None):
        c = str(component)
        if params is None: params = len(self.coefficients[c])
        L     = params
        bins  = sh//L 
        extra = sh-L*bins 
        return c,L,bins,extra

    def rebinVec(self,component,vec, params = None):
        c,L,bins,extra = self._prepRebin(component,vec.shape[0],params)
        start = vec[:extra*(bins+1)].reshape(-1,bins+1).mean(axis=1)
        final = vec[extra*(bins+1):].reshape(-1,bins).mean(axis=1)
        return ndappend(start,final)

    def redistributeCoefficients(self,component,params = None,distribution = None):
        c,L,bins,extra = self._prepRebin(component,self.coefficients[str(component)].shape[1],params) 
        if distribution is None: distribution = array([1 for _ in range(len(self.coefficients[c]))])
        arr   = self.coefficients[c]
        start = arr[0:L,:extra*(bins+1)].reshape(L,-1,bins+1).sum(axis=2)
        final = arr[0:L,extra*(bins+1):].reshape(L,-1,bins).sum(axis=2)
        return ndappend(start,final,axis=1)

    def AMDs(self,component,niter=3,marker='',**kwargs):
        c = str(component)
        kwargs['plot'] = False
        AMDS = [
            self.AMD(component,resV = array(rpoints(self.resVector[c],self.errVector[c].mean(axis=1))),**kwargs)
                for i in range(niter)
        ]
        Iplot.init()
        Iplot.plotCurves(*AMDS,marker=marker)
        Iplot.ylog()
        Iplot.x.label('log $\\xi$')
        Iplot.y.label('$N_H$ $10^{18}$ cm$^2$')

    def AMD(self,component, guess = None,plot = False, constraint = False, resV = None):
        c = str(component)
        _resVector = self.resVector[c]
        if resV is not None:
            _resVector = resV
        
        def AMDGen(AMDarray, c = self._coeff[c], r = _resVector): 
            objective = c.dot(AMDarray) - r
            return objective.dot(objective)

        constr = {'type':'ineq','fun': lambda x: x.min()}
        if guess is None:
            guess = [1 for _ in range(len(self._coeff[c][0]))]

        if constraint:
            result = minimize(AMDGen,guess,constraints=constr,method='slsqp',options={'maxiter':1000})
        else:
            result = minimize(AMDGen,guess,bounds=[(0,None) for _ in range(len(guess))],method='slsqp',options={'maxiter':1000})
        self._last = result
        if result.success:
            result = ndappend(self._xi[c].reshape(-1,1),result.x.reshape(-1,1),axis=1)
            if plot:
                Iplot.init()
                Iplot.plotCurves(result,marker='o')
                Iplot.ylog()
                Iplot.x.label('log $\\xi$')
                Iplot.y.label('$N_H$ $10^{18}$ cm$^2$')
            return result
        print 'Failed with '+ result.message

    def AMDEst(self,*components,**kwargs):
        Iplot.init()
        plotDict = defaultdict(int)
        legend = []
        for component in components:
            c = str(component)
            legend.append('Component '+c)
            for elem in self.params[c]:
                for ion in self.params[c][elem]:
                    eIon = elem+'_'+ion
                    Xi = self.probableXi(eIon)
                    plotDict[self.xif(Xi)] += self.NH(eIon,Xi,self.params[c][elem][ion])
            Iplot.plotCurves(sorted(plotDict.items()),chain=True,marker='o')
        try: legend = kwargs['labels']
        except KeyError: pass
        Iplot.legend(*legend, bbox_to_anchor=(1.1,1.1))
        Iplot.ylog()
        Iplot.y.label('d $N_H$')
        Iplot.x.label('log $\\xi$')

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

