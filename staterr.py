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

class Error(object):
    def __init__(self,score,epsilon = 0.005,v0 = 0.3, goal = 2.76, maxiter = 1000):
        #epsilon is allowed deviation from '1' when comparing chisq
        self.score = score
        self.eps   = epsilon
        self.v0    = v0
        #90% confidence interval
        self.goal  = goal
        self.miter = maxiter

    def __call__(self, initial,minimum = float('-Inf'), maximum = float('+Inf')):
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
       
        while abs(oldchi-bestchi) < self.goal and self.init + v0*t >= self.min and self.init + v0*t <= self.max:
            tmp = self.score(self.init + v0*t)
            if tmp < bestchi:
                raise newBestFitFound(self.init+v0*t,tmp)
            if tmp == oldchi: 
                limit -= 1
            else: 
                oldchi = tmp
                limit  = 10
            if not limit:
                if self.min == 0 and self.init+v0*(t) < self.eps: return 0
                if not attempts: 
                    raise errorNotConverging((self.init+v0*t,tmp),(self.init,bestchi))
                limit = 10
                attempts -= 1
                v0 *= 2
            t += 1
            if not maxiter:
                raise insensitiveToParameter((self.init+v0*t,tmp),(self.init,bestchi))
            maxiter -= 1

        if self.init + v0*t <= self.min:
            return self.min
        if self.init + v0*t >= self.max:
            return self.max
        return self.init + v0*(t-1)

