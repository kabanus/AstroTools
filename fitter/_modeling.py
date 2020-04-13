from scipy.optimize import curve_fit
from numpy import log, isnan


class NotAModel(Exception):
    pass


def chisq(self, result=None):
    if result is None:
        result = self.result
    return ((self.data.cts(row=True)-result)**2/self.data.errors(row=True)**2).sum()


def cstat(self, result):
    if result is None:
        result = self.result
    data = self.data.counts
    result = result*self.data.exposure
    C = result+data*(log(data)-log(result)-1)
    return 2*C[~isnan(C)].sum()


def reduced_chisq(self):
    return self.chisq(self.result)/(len(self.data.channels)-len(self.getThawed()))


def append(self, *args):
    for model in args:
        try:
            model._calculate
            model.freeze
            model.thaw
            model.calculate
            model.setp
            self.models.append(model)
        except AttributeError:
            raise self.NotAModel(model, model.__class__)
    if len(self.models):
        self.activate()


def delete(self, index):
    # Prevent bad name access
    self.models[index] = None


def activate(self, index=-1):
    self.current = self.models[index]
    self.currentindex = index


def nameModel(self, index, name):
    setattr(self, name, lambda: self.activate(index))


def energies(self):
    return self.resp.ebinAvg


def tofit(self, elist, *args):
    res = self.current.tofit(elist, *args)
    return self.resp.convolve_channels(res)


def toMinimize(self, args):
    s = self.stat(self.tofit(self.energies(), *args))
    return s


def fit(self):
    model = self.current
    args = self.initArgs()

    bestfit, self.errs = curve_fit(self.tofit, self.energies(), self.data.cts(row=True), p0=args,
                                   sigma=self.data.errors(row=True), absolute_sigma=True, epsfcn=self.eps)
    self.stderr = dict(zip(model.getThawed(), [self.errs[j][j]**0.5 for j in range(len(self.errs))]))
    # ftol = 2.220446049250313e-09
    # bestfit = minimize(self.toMinimize,args,method="L-BFGS-B",options={'ftol':ftol})
    # if not bestfit.success:
    #     raise ValueError("-E- Failed fit with: "+bestfit.message.decode('unicode-escape'))
    # self.stderr = dict(zip(model.getThawed(),sqrt(abs(max(1,bestfit.fun)*ftol*diag(bestfit.hess_inv.todense())))))
    # self.calc(dict(zip(model.getThawed(),bestfit.x)))
    self.calc(dict(zip(model.getThawed(), bestfit)))
