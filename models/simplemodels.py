
from model import _singleModel,modelExport
from collections import OrderedDict
from interpolations import linear

keVAfac = 12.39842
class simple(_singleModel):
    def __init__(self):
        _singleModel.__init__(self)
    def _calculate(self,atrange):
        return self(atrange)

class Function(simple):
    class paramsMustBeDict(Exception): pass
    def __init__(self,expression, params):
        simple.__init__(self)
        #Check
        try:
            params.keys()
        except AttributeError:
            raise self.paramsMustBeDict()
        self.params = params
        self.expression = expression
        exec('self.func = lambda x,'+','.join(params.keys())+': '+expression)
   
    def __call__(self,x):
        return self.func(x,**self.params)

#Pure lambda, overwrite __str__
@modelExport
class function(Function):
    description = 'Analytic function of energy'
    def __init__(self,expression,params):
        Function.__init__(self,expression,params)
    def __str__(self):
        return 'function("'+self.expression+'",'+str(self.params)+')'

@modelExport
class powerlaw(Function):
    description = 'Energy powerlaw'
    def __init__(self):
        Function.__init__(self,"K*x**-a",{'K':1,'a':2})

@modelExport
class alorentz(Function):
    description = "Lorentzian centered in Angstrom"
    def __init__(self):
        Function.__init__(self,"norm/(pi*g*(1+((keVAfac/x-center)/g)**2))",{'norm':0,'g':1,'center':1})

class bbody(Function):
    description = 'Blackbody'
    def __init__(self):
        dE = str(0.03)
        Function.__init__(self,"(N*8.0525*x**2*"+dE+")/(kT**4*(exp(x/kT)-1))",{'N':1,'kT':0.5})

@modelExport
class Table(simple):
    description = 'Single table (no fit)'
    def __init__(self,table):
        simple.__init__(self)
        try: 
            self.fname = table
            table = [[float(x) for x in line.split()] for line in open(table)]
        except IOError: pass
        self.interpolation = linear(table)
        self.data = table
    
    def __call__(self,energies):
        for energy in energies:
            try:
                yield self.interpolation(energy)[1]
            except self.interpolation.outOfRange: yield 0

    def __str__(self):
        try: return 'Table("'+self.fname+'")'
        except:
            return 'Table<object>'

class Tables(simple):
    def __init__(self,params,tablehash):
        self.params = params
        self.phash  = {} 

        for params, table in tablehash:
            if len(params) != len(self.params):
                raise Exception("Param number mismatch!")
           
            chash = self.phash
            for param in params:
                try:
                    chash = chash[param]
                except KeyError: 
                    chash[param] = {}
                    chash = chash[param]
            chash['table'] = table
        self.phash = self._sortParams(self.phash)

    def _sortParams(self,dic):
        try: return dic['table']
        except: pass
        res = OrderedDict(sorted(dic.items()))
        for p in res:
            res[p] = self._sortParams(res[p])
        return res

    def pget(self, chash, *args):
        if not len(args):
            return chash

        return self.pget(chash[args.pop(0)],args)


