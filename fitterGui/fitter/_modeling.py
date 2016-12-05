from scipy.optimize import curve_fit
from itertools      import izip

class NotAModel(Exception): pass


def chisq(self):
    try:
        return sum((self.data.cts()-self.result)**2/self.data.errors()**2)
    except ValueError:
        return float('nan')

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

def energies(self):
    return self.resp.ebinAvg

def tofit(self, elist, *args):
    res = self.current.tofit(elist,*args)
    return self.resp.convolve_channels(res)

def fit(self):
    model = self.current
    args  = self.initArgs()
  
    bestfit,self.errs = curve_fit(self.tofit,self.energies(),self.data.cts(),
                                  p0=args,sigma=self.data.errors())

    self.stderr  = dict(izip(model.getThawed(),
                    [self.errs[j][j]**0.5 for j in range(len(self.errs))]))
   
    self.calc(dict(izip(model.getThawed(),bestfit)))

