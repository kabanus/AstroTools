

class errorNotConverging(Exception): pass
class newBestFitFound(Exception): pass

def error(self, index, param, epsilon = 0.05, v0 = 0.3):
    self.errorlog = []
    return (oneSidedError(self,index,param,-1,epsilon,v0),
            oneSidedError(self,index,param, 1,epsilon,v0))

def append_stage(self,iparam,count = 0):
    self.errorlog.append(' : '.join(("%3d"%count,"%10s"%str(iparam), "%.3e"%self.current[iparam],
                                     "%.3e"%self.chisq(),"%.3e"%self.reduced_chisq())))

#epsilon is allowed deviation from '1' when comparing chisq
def oneSidedError(self, index, param, direction, epsilon,v0):
    iparam  = (index,param)
    thawed  = iparam in self.getThawed()
    self.thaw(iparam)
    save    = dict(zip(self.getThawed(),self.initArgs()))
    self.freeze(iparam)
    bestchi = self.chisq()
    initial = self.current[iparam]
    needfit = self.current.getThawed()
    #90% confidence interval
    goal = 2.76
   
    restore = True
    try:
        self.errorlog.append('Sliding from best fit:')
        run_away(self,initial,needfit,bestchi,thawed,iparam,save,direction,v0)
        append_stage(self,iparam)
        self.errorlog.append('Finding edge:') 
        binary_find_chisq(self,initial,needfit,bestchi,thawed,iparam,epsilon,goal)
    except newBestFitFound:
        restore = False
        raise
    finally:
        if restore:
            result = self.current[iparam]
            self.calc(save)
            if thawed: self.thaw(iparam)
    self.errorlog.append('Completed normally') 
    return result - self.current[iparam]

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
        append_stage(self,iparam, limit)
        if current < bestchi:
            if thawed: self.thaw(iparam)
            raise self.newBestFitFound()
        if abs(current-bestchi) < goal:
            backp = self.current[iparam]
        else:
            frontp = self.current[iparam]
        if ofrontp == frontp:
            limit -= 1
        else: ofrontp = frontp
        if not limit:
            self.setp({iparam:frontp})
            return 
   

def run_away(self,initial,needfit,bestchi,thawed,iparam,save,direction,v0):
    limit   = 10
    oldchi  = bestchi
    v0     *= direction * (initial if initial else 1)
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

