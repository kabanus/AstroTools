from itertools import izip

class errorNotConverging(Exception): pass
class newBestFitFound(Exception): pass

def error(self, index, param, epsilon = 0.05, v0 = 0.3):
    return (oneSidedError(self,index,param,-1,epsilon,v0),
            oneSidedError(self,index,param, 1,epsilon,v0))

#epsilon is allowed deviation from '1' when comparing chisq
def oneSidedError(self, index, param, direction, epsilon,v0):
    iparam  = (index,param)
    thawed  = iparam in self.getThawed()
    self.thaw(iparam)
    save    = dict(izip(self.getThawed(),self.initArgs()))
    self.freeze(iparam)
    bestchi = self.chisq()
    initial = self.current[iparam]
    needfit = self.current.getThawed()
    #90% confidence interval
    goal = 2.76

    run_away(self,initial,needfit,bestchi,thawed,iparam,save,direction,v0)
    binary_find_chisq(self,initial,needfit,bestchi,thawed,iparam,epsilon,goal)
    slide_away(self,iparam,needfit,bestchi,direction,epsilon,goal,save,thawed,v0)

    result = self.current[iparam]
    self.calc(save)
    if thawed: self.thaw(iparam)
    return result - self.current[iparam]

def slide_away(self,iparam,needfit,bestchi,direction,epsilon,goal,save,thawed,v0):
    t       = 1 
    #Run slower
    v0     *= direction*self.current[iparam]*0.1
    limit   = 10

    #Do
    while True:
        prev    = self.current[iparam]
        if not insert_and_continue(self,iparam,self.current[iparam]+v0*t): break
        self.calc()
        if needfit: self.fit()
        current = self.chisq()

        if not limit: 
            if thawed: self.thaw(iparam)
            self.calc(save)
            raise self.errorNotConverging()
        limit -= 1
    #While
        if abs(abs(current-bestchi)-goal) >= epsilon: break

    self.setp({iparam:prev})

def binary_find_chisq(self,initial,needfit,bestchi,thawed,iparam,epsilon,goal):
    current = self.chisq()
    frontp  = self.current[iparam]
    backp   = initial
    limit   = 15
    ofrontp = frontp
    while abs(abs(current - bestchi)-goal) > epsilon and backp != frontp:
        if not insert_and_continue(self,iparam,(frontp+backp)/2.0): break
        self.calc()
        if needfit: self.fit()
        current = self.chisq()
        if current < bestchi:
            if thawed: self.thaw(iparam)
            raise self.newBestFitFound()
        if abs(current-bestchi) < goal:
            backp = self.current[iparam]
        else:
            frontp = self.current[iparam]
        if ofrontp == frontp:
            limit -= 1
        else: ofrontp == frontp
        if not limit:
            self.setp({iparam:frontp})
            return 
   

def run_away(self,initial,needfit,bestchi,thawed,iparam,save,direction,v0):
    limit   = 10
    oldchi  = bestchi
    v0     *= direction * initial
    t       = 1

    while abs(oldchi-bestchi) < 2.76:
        if not insert_and_continue(self,iparam,self.current[iparam]+v0*t): break
        self.calc()
        if needfit: self.fit()
        tmp = self.chisq()
        if tmp < bestchi:
            if thawed: self.thaw(iparam)
            raise self.newBestFitFound()
        if tmp == oldchi: 
            limit -= 1
        else: 
            oldchi = tmp
            limit  = 10
        if not limit: 
            if thawed: self.thaw(iparam)
            self.calc(save)
            raise self.errorNotConverging()
        t += 1

#Check if model limits the parameter in the direction
def insert_and_continue(self,iparam,what):
    self.setp({iparam:what})
    if self.current[(iparam)] != what: return False
    return True

