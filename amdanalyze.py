from scipy.optimize import minimize
from numpy import float64,array,zeros,concatenate,delete
from numpy import append as ndappend
from utils import RomanConversion
from collections import defaultdict
from randomizers import points as rpoints
from plotInt import Iplot
import staterr
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
    def __init__(self, table, params = None):
        self._error = None
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
            xi = self.xif(xiline[self.ind['ion_run']])
            for ion in self.ind:
                if ion in ('ion_run','delta_r','x_e','n_p','frac_heat_error'): continue
                try: 
                    elem,charge = ion.split('_')
                except ValueError: continue
                self.fractions[xi][elem][charge] = xiline[self.ind[ion]]
        self.fractions = dict(((k,dict(v)) for k,v in self.fractions.items()))
        self.xiOrder   = array(sorted(self.fractions))
        if params is not None: self.readParams(params)
               
    def readParams(self, fname):
        self.errors = defaultdict(dict)
        self.data   = defaultdict(dict)
        for line in open(fname):
            line = re.split('\s+',line.strip())
            if len(line) <= 4: continue
            try: 
                ion = self.getIon(line[1])
                component = int(line[0])
            except KeyError: continue
            self.data[component][ion] = float(line[3])
            exec('self.errors[component][ion] = abs(array('+line[4]+')).mean()') in locals(),globals()
        self.errors = dict(self.errors)
        self.data   = dict(self.data)
        self.params = dict()
        for component in self.data:
            self.params[component] = defaultdict(dict)
            for eIon in self.data[component]:
                elem,ion = self.getIon(eIon,split=True)
                self.params[component][elem][ion] = self.data[component][eIon]
            self.params[component] = dict(self.params[component])
        self.rebin()


    def rebin(self, epsilon = 1e-2,amount = None,fixedGrid = None,outerBin = None, boundary = 0):
        self.nhMaps = dict()
        self._coeff = dict()
        self.xilist = dict()
        for component in self.data:
            self.nhMaps[component] = dict()
            self._coeff[component] = dict()
            self.xilist[component] = set()
            for ion in self.data[component]:
                elem,charge = self.getIon(ion,split=True)
                self._coeff[component][ion] = list()
                self.nhMaps[component][ion] = list()
                xis = fixedGrid if fixedGrid else self.relaventXis(ion,epsilon,amount)
                for xi in xis: 
                    self._coeff[component][ion].append(abundances[elem]*self.fractions[xi][elem][charge])
                    self.nhMaps[component][ion].append(xi)
                    self.xilist[component].add(xi)

        try: rbound,lbound = boundary 
        except TypeError: rbound = lbound = boundary
        self._cMat   = dict()
        self._rVec   = dict()
        self._eVec   = dict()
        self.dxilist = dict()
        for c in self.nhMaps:
            self.xilist[c] = sorted(self.xilist[c])
            if outerBin is None:
                sBin = 2*self.xilist[c][0]-self.xilist[c][1]
                fBin = 2*self.xilist[c][-1]-self.xilist[c][-2]
            else:
                try: sBin,fBin = outerBin
                except TypeError: sBin = fBin = outerBin
            self.xilist[c] = [sBin] + self.xilist[c] + [fBin]
            self.dxilist[c]= array([0] + [(self.xilist[c][i+1]-self.xilist[c][i-1])/2.0 
                            for i in range(1,len(self.xilist[c])-1)] + [0])
            self._cMat[c]  = zeros(shape=(len([_ for v in self.nhMaps[c].values() if v]),len(self.xilist[c])))
            self._rVec[c]  = list()
            self._eVec[c]  = list()
            row = 0           
            for ion in self.nhMaps[c]:
                if not self.nhMaps[c][ion]: continue
                self.nhMaps[c][ion] = array(map(lambda x: self.xilist[c].index(x),self.nhMaps[c][ion]))
                self._coeff[c][ion] = array(self._coeff[c][ion])
                self._cMat[c][row,self.nhMaps[c][ion]] = self._coeff[c][ion]
                self._rVec[c].append(self.data[c][ion])
                self._eVec[c].append(self.errors[c][ion])
                row += 1
            self._rVec[c] = array(self._rVec[c])
            self._eVec[c] = array(self._eVec[c])
               
    def contributions(self,component,ion=None,xiMin=None,xiMax=None):
        c = component
        ions = self.data[c].keys() if ion is None else [ion]
        header = ion is None
        if header:
            print "%-8s %-4s %-8s %-8s %-8s %-8s"%('ion','xi','NI','Fraction','Abund','Product')
        for ion in ions:
            ion = self.getIon(ion)           
            try:
                if not header: 
                    print ion,'contributions:'
                    print "%-4s %-8s %-8s %-8s %-8s"%('xi','NI','Fraction','Abund','Product')                   
                for ind in self.nhMaps[c][ion]:
                    xi = self.xilist[c][ind]
                    if (xiMin is None or xi >= xiMin) and (xiMax is None or xi <= xiMax):
                        elem,charge = self.getIon(ion,split=True)
                        if header: print '%-8s'%(ion),
                        print "%.2f %.2e %.2e %.2e %.2e"%(
                                        xi,self.data[c][ion],self.fractions[xi][elem][charge],abundances[elem],
                                        self.fractions[xi][elem][charge]*abundances[elem])
            except KeyError: 
                if not header: print None
    
    def relaventXis(self,ion,epsilon,amount):
        elem,charge = self.getIon(ion,split=True)
        res = []
        count = 0
        pxi = self.probableXi(ion)
        for xi in self.xiOrder:
            if self.fractions[xi][elem][charge] > epsilon:
                if xi == pxi: i = count
                res.append(xi)
                count += 1
        if amount is not None:
            return res[(i-amount if i-amount > 0 else 0):(i+amount+1 if pxi+amount < len(res) else len(res))]
        return res

    def AMDs(self,component,niter=3,marker='',**kwargs):
        c = component
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

    def estimateNH(self,c,index,val,nh,**kwargs):
        if val < 0: return float('inf')
        contr = self._cMat[c][:,index+1].dot(val*self.dxilist[c][index+1])
        Ocmat = self._cMat[c].copy()
        Odxi  = self.dxilist[c].copy()
        Oxi   = self.xilist[c][:]
        nh    = delete(nh,index)
        self._cMat[c]   = delete(self._cMat[c],index+1,axis=1)
        self.dxilist[c] = delete(self.dxilist[c],index+1)
        self.xilist[c]  = delete(self.xilist[c],index+1)
        try:
            nh = self.AMD(c,guess = nh, add = contr,**kwargs)
        finally:
            self._cMat[c]   = Ocmat
            self.dxilist[c] = Odxi
            self.xilist[c]  = Oxi
        return self._last['fun']
    
    def error(self, *indices):
        errors = []
        for index in indices:
            last    = self._last
            lasterr = self._error
            errCalc = self._error(index)
            try:
                res = errCalc(self._last.x[index],minimum=0)
            except staterr.newBestFitFound as e:
                print "New best fit found:",e
                res = concatenate((self._last.x[:index],array((e.new,)), self._last.x[index:]))
            finally:
                self._last  = last
                self._error = lasterr
            errors.append(res)
        return errors if len(errors) > 1 else errors[0]
        
    def AMDQuality(self,nh,c,estimate = None,add = None):
        nh = concatenate(([0],nh,[0]))
        predicted  = self._cMat[c].dot(nh*self.dxilist[c])
        if add is not None: predicted += add
        objective = predicted -self._rVec[c]
        objNormed = objective/self._eVec[c]
        res = objNormed.dot(objNormed)
        if estimate is not None:
            if estimate == 0:
                return predicted
            if estimate == 1:
                return objective
            return objNormed
        return res

    def AMD(self,component, guess = None,plot = False,onlyElem = None,filterElems = [],
            maxiter = 1000, add = None, errors = None, verbose = True):
        c = component
        if guess is None:
            guess = [1 for _ in range(len(self.xilist[c])-2)]
        if isinstance(filterElems,str): filterElems = (filterElems,)
        if onlyElem in filterElems:
            raise TypeError("Can't provide onlyElem and also filter it!")

        useOnly = set()
        for ion in self._coeff[c]:
            elem,_ = self.getIon(ion, split = True)
            if elem == onlyElem: useOnly.add(ion)
            if onlyElem is None and elem not in filterElems: useOnly.add(ion)
        if not useOnly:  useOnly = None

        bounds      = [(0,None) for _ in range(len(guess))]
        result      = minimize(self.AMDQuality,guess,args=(c,None,add),bounds=bounds,method='slsqp',options={'maxiter':maxiter})
        result.x[result.x < 0] = 0
        self._last  = result
        self._error = lambda index: staterr.Error(lambda v,c=c,i=index,nh=result.x,f=self: f.estimateNH(c,i,v,nh,verbose = False))
        if result.success:
            NH = result.x
            if plot:
                toplot = concatenate((array(self.xilist[c][1:-1]).reshape(-1,1),(self.dxilist[c][1:-1]/2.0).reshape(-1,1),
                                      NH.reshape(-1,1),zeros(shape=(len(NH),1))),axis=1)
                if errors is not None:
                    toplot[:,-1] = array([(e[1]-e[0])/len(e) for e in errors])
                Iplot.init()
                Iplot.plotCurves(toplot,marker='o')
                Iplot.ylog(True)
                Iplot.x.label('log $\\xi$')
                Iplot.y.label('$N_H$ $10^{18}$ cm$^2$')
            dof = len(self._rVec[c])-len(guess)
            red = self._last['fun']/dof
            self._last.dof  = dof
            self._last.bins = len(self._rVec[c])
            self._last.pars = len(guess)
            if verbose: 
                print u"{0} parameters, {1} bins, {2} d.o.f, \u03C7\u00B2 = {3},and reduced {4}".format(
                    len(guess),len(self._rVec[c]),dof,self._last['fun'],red).encode('utf8')
            return NH
        if verbose: 
            print 'Failed with '+ result.message
            return None
        raise ValueError("Failed with " + result.message)

    def AMDEst(self,*components):
        Iplot.init()
        legend = []
        for component in components:
            c = component
            e = lambda ion: elem+'_'+ion
            for elem in self.params[c]:
                legend.append(elem)
                curve = sorted([(self.probableXi(e(ion)),
                                    self.NH(e(ion),self.probableXi(e(ion)),self.params[c][elem][ion]))
                            for ion in self.params[c][elem]])

                Iplot.plotCurves(curve,chain=True,marker='o')
        Iplot.ylog(True)
        Iplot.legend(*legend, bbox_to_anchor=(1.1,1.1))
        Iplot.y.label('log $N_H 10^{18}$ cm$^2$')
        Iplot.x.label('log $\\xi$')
    
    def NI(self,ion,xi,NH):
        elem,charge = self.getIon(ion,split=True)
        return NH*self.fractions[xi][elem][charge]*abundances[elem]

    def NH(self,ion,xi,NI):
        elem,charge = self.getIon(ion,split=True)
        if type(charge) is int: charge = RomanConversion.toRoman(charge).lower()
        return NI/(self.fractions[xi][elem][charge]*abundances[elem])
   
    def probableXi(self,ion):
        elem,charge = self.getIon(ion,split=True)
        return max(((self.fractions[xi][elem][charge],xi)
                        for xi in self.fractions))[1]
  
    def plotModel(self,elem):
        charges = defaultdict(list) 
        for xi in self.fractions:
            for charge in self.fractions[xi][elem]:
                val = self.fractions[xi][elem][charge]
                charges[charge].append((xi,val))
        Iplot.init()
        for charge in charges:
            Iplot.plotCurves(sorted(charges[charge]),chain = True)
        height = 0.45
        for charge in charges:
            xi = self.probableXi(self.writeIon(elem,charge))
            height = self.fractions[xi][elem][charge]
            Iplot.annotate((charge,),((xi,height),),slide=(1,1))
        Iplot.x.label('log $\\xi$')
        Iplot.y.label('Ion Fraction')
        Iplot.title(elem.title())
    
    def getIon(self,ion,split = False):
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
        return (elem,charge) if split else ion

    def xif(self,xi):
        return float(xi.split('_')[1])

    def writeIon(self,elem,charge):
        return elem + '_' + charge
