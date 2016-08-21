#!/usr/bin/python
#Program to calculate correlations (Partly integrated) using
#the old school methods.
#Based on Fortran programs given to me by shay. Fortran sucks.
import interpolations 

#Wraps a CCF and its swap. It does not inherit it, it contains two CCFs.
class PICCF:
    def __init__( self, first, second, interactive = False,
                  interp = interpolations.linear ):
        self.ccf1 = CCF(first, second, interactive, interp)
        self.ccf2 = CCF(second, first, interactive, interp,1)
    def __call__(self,tau):
        return (self.ccf1(tau)+self.ccf2(tau))/2.0
    def calcRange(self, step = None, start = None, final = None):
        gen1 = self.ccf1.calcRange(step,start,final)
        gen2 = self.ccf2.calcRange(step,start,final)
        for x,y in zip(gen1,gen2):
            yield [(x[i]+y[i])/2.0 for i in range(len(x))]
    def calcTable(self, step = None, start = None, final = None):
        return [x for x in self.calcRange(step,start,final)]

#Return ccf function
class CCF:
    class BadNCalculation(Exception): pass
    class tauOutOfRange(Exception): pass
    class noCCFIntersect(Exception): pass

    def __init__( self, first, second, interactive = False,
                  interp = interpolations.linear, firstlc=0 ):
        self.interp = interp
        self.interactive = interactive
        self.vector = interpolations.Segment(first)
        curve2 = interpolations.Segment(second)
        shift = -min(self.vector[0][0],curve2[0][0])
        self.vector.shift(shift)
        curve2.shift(shift) 
        self.interpolated= self.interp(curve2)
        if self.vector[ 0][0] > self.interpolated.vector[-1][0] or\
           self.vector[-1][0] < self.interpolated.vector[ 0][0]:
            raise self.noCCFIntersect()
        self.firstlc = firstlc
   
    def __len__(self):
        return len(self.vector)

    #Return result for given tau
    def __call__(self, tau):
        start = 0 
        end   = len(self.vector)
        if self.firstlc: tau = -tau
        #Find earliest and final relavent times
        try:
            while self.interpolated.vector[0][0] > self.vector[start][0] - tau :
                start += 1
            while self.interpolated.vector[-1][0] < self.vector[end-1][0] - tau:
                end -= 1
                if end < 0: self.vector[len(self.vector)]
        except IndexError:
            raise self.tauOutOfRange("Given tau=%.10f "%tau +
                        "out of range %.10f-%.10f=%.10f"%(self.vector[-1][0],
                                                  self.vector[0][0],
                               self.vector[-1][0]-self.vector[0][0]))
        ##############
        N = vi = vb = ib = isq = vsq = 0
        for i in range(start,end):
            v = self.vector[i][1]
            i = self.interpolated(self.vector[i][0]-tau)[1]
            vi  += v*i
            vb  += v
            ib  += i
            vsq += v**2
            isq += i**2
            N  += 1 
        N = float(N)
        if not N: return 0
        vi  /= N
        vb  /= N
        ib  /= N
        vsq /= N
        isq /= N
        if vsq == vb**2 or isq == vi ** 2: return float('Inf')
        return (vi-vb*ib)/((vsq-vb**2)*(isq-ib**2))**0.5
        ##############

    #step may be a float, or defaults to None, which samples only
    def calcRange(self, step = None, start = None, final = None):
        if not start: start = -abs(
                        min(self.vector[-1][0],self.interpolated.vector[-1][0])-
                        max(self.vector[0][0],self.interpolated.vector[0][0]))
        if not final: final = -start
        if not  step:  step = abs(final)/float(max(
                            len(self.vector),len(self.interpolated.vector)))
        t = start
        while t <= final:
            yield [t,self(t)]
            t += step
   
    def calcTable(self, step = None, start = None, final = None):
        return [x for x in self.calcRange(step,start,final)]
    
    #Calculate minimum time step in both lcs.
    def minStep( self, interactive = False ):
        delta = min(self.interpolated.vector.defaultStep(), self.vector.defaultStep())
        print("Got a minimum delta value of: " + str(delta) + ". Will " +
              "use as a step delta/10="+str(delta/10.0)+".")
        if interactive:
            try:
                print ("To change this enter new step (any none floating " +
                       "input will be treated as accepting this value): ")
                return float(raw_input())
            except:
                pass     
        return delta/10.0
            
