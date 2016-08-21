#Object for handling numerical functions

from plotInt import Iplot
from re import split

class lightCurve:
    x  = 0
    y  = 1
    dy = 2
    class lcOutOfBound(Exception): pass
    def __init__(self,table = []):
        self.table = []
        try: 
            for line in open(table):
                try:
                    self.table.append([float(x) for x in 
                                          split("\s+",line.strip())])
                except TypeError: continue
        except TypeError: self.table = table
        self.table.sort()

    'Currently only 3-point derivative.'
    def diff(self,i):
        if i <= 0 or i >= len(self.table)-1: return None
        dy = self.table[i+1][1] - self.table[i-1][1]
        dx = self.table[i+1][0] - self.table[i-1][0]
        return self.table[i][0],dy/dx

    def avg(self,column, transform = lambda x: x):
        return sum([transform(row[column]) for row in self.table])/len(self.table)

    def var(self, column):
        return self.avg(column,lambda x: x**2)-self.avg(column)**2

    def resetzoom(self):
        try: self.table = self.original
        except KeyError: pass

    def slideAndAverage(self, windowSize, action, verbose=False):
        if action in dir(self):
            start = -1
            res   = 0
            count = 0
            try: 
                while True:
                    start += 1
                    stop  = self.find(self.table[start][0]+windowSize)
                    self.zoom(window=[start,stop])
                    current = getattr(self,action)()
                    self.resetzoom()
                    if verbose:
                        print "-I- Window [",start,"=",self.table[start][0],"-",stop,"=",self.table[stop][0],"] got",action,"of",current
                    res   += current
                    count += 1
            except lightCurve.lcOutOfBound: pass
            if verbose:
                print "-I- Got",count,"windows."
            return res/count
        else: 
            print("-E- Got bad action! use dir() to see availble actions (no parameter functions).")

    def inPairs(self, column, action=lambda x,y: abs(x-y), after=lambda x: sum(x)/(len(x)-1)):
        return after([action(self.table[i][column],self.table[i-1][column])
                    for i in range(1,len(self.table))])

    def zoom(self, timewindow=None, window=[]):
        if timewindow:
            window.append(self.find(timewindow[0]))
            window.append(self.find(timewindow[1]))
        if window[1] < 0:
            window[1] += len(self.table)
        window[1] += 1
        self.original = self.table
        self.table = self.table[window[0]:window[1]]

    def Fvar(self):
        return ((self.var(self.y) - self.avg(self.dy,lambda x: x**2))/
                self.avg(self.y)**2)**0.5

    #Earliest time smaller or equal to time
    def find(self, time):
        if time > self.table[-1][0] or time < self.table[0][0]:
            raise lightCurve.lcOutOfBound()
        for i in range(0,len(self.table)):
            if self.table[i][0] > time: return i

    def dFvar(self):
        N  = len(self.table)
        s2 = self.avg(self.dy,lambda x: x**2)
        F  = (self.avg(self.y))
        return ( (((s2/N)**0.5)/F)**2 + ((s2/F**2/self.Fvar())*(1/(2*N))**0.5)**2 )**0.5
   
    def plot(self):
        Iplot.clearPlots()
        Iplot.plotCurves(self)

    def __getitem__(self,i):
        return self.table[i]

    def __iadd__(self,other):
        self.table += other.table
        return self

    def __len__(self):
        return len(self.table)
        
