from scipy.optimize import curve_fit
from numpy import inf
class convergenceError(Exception):
    def __init__(self,curr,best):
        Exception.__init__(self)
        self.best = best
        self.curr = curr
    def __str__(self):
        return (Exception.__str__(self)+"Current: " + ":".join((str(x) for x in self.curr)) + 
                                        " Best: "   + ":".join((str(x) for x in self.best)))
class errorNotConverging(convergenceError): pass
class insensitiveToParameter(convergenceError): pass

class newBestFitFound(Exception):
    def __init__(self,new,score):
        Exception.__init__(self)
        self.new   = new
        self.score = score
    def __str__(self):
        return Exception.__str__(self)+"Param = " + str(self.new) + " Score = " + str(self.score)

class Statistic:
    def __init__(self,x,y,dy,model,bounds={},debug=False,**pdict):
        self.x     = x
        self.y     = y
        self.dy    = dy
        self.model = model
        self.args  = pdict
        self.bounds= bounds
        for param in self.args:
            if param not in bounds:
                self.bounds[param] = (-inf,inf)
            else:
                try: self.bounds[param][0]
                except TypeError:
                    self.bounds[param] = (self.bounds[param],inf)
        self.debug=debug
    def setp(self,pname):
        self.param = pname
        
        self.current = self.args.copy()
        self.current.pop(pname)

        self.boundlist = [[],[]]
        for k in self.current:
            self.boundlist[0].append(self.bounds[k][0])
            self.boundlist[1].append(self.bounds[k][1])
    def convergeStatParam(self,pname,verbose=True,iter=inf):
        self.setp(pname)
        err = Error(self)
        while iter:
            try:
                result = err(self.args[pname],minimum=self.bounds[pname][0],maximum=self.bounds[pname][1])
                break
            except newBestFitFound as best:
                if verbose:
                    print("-I- New best fit found:",pname,"=",best.new,
                        ','.join('{} = {}'.format(k,v) for k,v in zip(self.current.keys(),self.best)))
                for key,val in zip(self.current.keys(),self.best):
                    self.args[key] = val
                    self.current[key] = val
                self.args[pname] = best.new
                iter-=1
            except errorNotConverging as e:
                if verbose:
                    print("-E- Failed to converge on","'"+pname+"'")
                raise
        else:
            raise convergenceError(self.value,self.score(self.last[0][0]))
        return result

    def calc(self,x,*args):
        for key,val in zip(self.current.keys(),args):
            self.current[key] = val
        return self.model(x,**self.current,**{self.param: self.value})
    def __call__(self,value):
        self.value = value
        self.best,self.cov = curve_fit(self.calc,self.x,self.y,sigma=self.dy,
               p0=list(self.current.values()),bounds=self.boundlist)
        score = self.score(self.calc(self.x,*self.current.values()))
        if self.debug:
            print("FIT: {} = {}\n".format(self.param,self.value)+'\n'.join("    {} = {}".format(k,v) 
                        for k,v in zip(self.current.keys(),self.best)))
            print("    Score = {}".format(score))
        return score


class Chisq(Statistic):
    def __init__(self,*args,**kwargs):
        Statistic.__init__(self,*args,**kwargs)
    def score(self,my):
        chi = ((my-self.y)/self.dy)
        return chi.dot(chi)
       
class Error(object):
    def __init__(self,score,epsilon = 0.005,v0 = 0.3, goal = 2.76, maxiter = 1000,stopeps=1E-10):
        #epsilon is allowed deviation from '1' when comparing chisq
        self.score = score
        self.eps   = epsilon
        self.v0    = v0
        #90% confidence interval
        self.goal  = goal
        self.miter = maxiter
        self.seps  = stopeps

    def __call__(self, initial,minimum = -inf, maximum = inf):
        self.min  = minimum
        self.max  = maximum
        self.init = initial
        return self.oneSided(-1),self.oneSided(1)
    
    def oneSided(self,direction):
        bestchi = self.score(self.init)
       
        result = self.run_away(bestchi,direction)
        if abs(self.score(result) - bestchi) > 2.76:
            result = self.binary_find_chisq(result,bestchi)
        return result - self.init
    
    def binary_find_chisq(self,currentp,bestchi):
        current = self.score(currentp)
        frontp  = currentp
        backp   = self.init
        limit   = 15
        ofrontp = frontp
        while abs(abs(current - bestchi)-self.goal) > self.eps and backp != frontp:
            currentp = (frontp+backp)/2.0
            current  = self.score(currentp)
            if current < bestchi:
                raise newBestFitFound(currentp,current)
            if abs(current-bestchi) < self.goal:
                backp = currentp
            else:
                frontp = currentp
            if ofrontp == frontp:
                limit -= 1
            else: ofrontp = frontp
            if not limit:
                return frontp
        return currentp
       
    
    def run_away(self,bestchi,direction):
        limit   = 10
        attempts= 10
        oldchi  = bestchi
        v0      = self.v0 * direction * (self.init if self.init else 1)
        t       = 1
        maxiter = self.miter
        runs    = 1
    
        now = self.init+v0*t
        while (abs(oldchi-bestchi) < self.goal and 
               now > self.min  and now < self.max):
            tmp = self.score(now)
            if tmp < bestchi:
                raise newBestFitFound(now,tmp)
            attempts -= 1
            runs     += 1
            if tmp == oldchi: 
                limit -= 1
            else: 
                oldchi = tmp
                limit  = 10
            if not limit:
                if self.min == 0 and self.init+v0*(t) < self.seps: return 0
                raise insensitiveToParameter((self.init+v0*t,tmp),(self.init,bestchi))
            if not attempts:
                v0 *= 2**runs
                attempts = 10
            t += 1
            if not maxiter:
                raise errorNotConverging((self.init+v0*t,tmp),(self.init,bestchi))
            maxiter -= 1
            now = self.init + v0*t

        if self.init + v0*t <= self.min:
            return self.min
        if self.init + v0*t >= self.max:
            return self.max
        return self.init + v0*(t-1)

