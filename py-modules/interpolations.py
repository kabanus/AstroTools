#Interpolation funcitons
#Expect 3 column vectors in vector
from copy import deepcopy

class Curve:
    class LengthError(Exception): pass
    def __init__(self, curve, llength = 3):
        self.vector = sorted(deepcopy(curve),key = lambda x: x[0])     
        self.stats = []
        fsum = 0
        for line in self.vector:
            if len(line) != llength: 
                raise self.LengthError("Bad line length in line " + str(line))
        
    
    def shift(self, by):
        for line in self.vector:
            line[0] += by 
    
    @staticmethod
    def reflection(vector):
        table = deepcopy(vector)
        for line in table:
            line[0] = -line[0]
        return table 

    def defaultStep( self ):
        delta = float("inf")
        LC = self.vector 
        for i in range(1,len(LC)):
            delta = min(delta, LC[i][0]-LC[i-1][0])
        return delta
            
    def __iter__(self):
        self.count = 0
        return self.vector.__iter__()
        
    def __next__(self):
        self.count += 1
        if self.count > len(self.vector):
            raise StopIteration
        return self.vector.next()

    def __getitem__(self, index):            
        try:
            return self.vector[index]
        except IndexError:
            #A curve is defined -inf until inf
            return [2*((index>0)-0.5)*float("Inf"),self.avg,0]

    def __setitem__(self, index, item):
        self.vector[index] = item

    def __len__(self):
        return len(self.vector)
  
    def sort(self):
        self.vector.sort(key = lambda x: x[0])

class Segment(Curve):
    def __getitem__(self, i):
        return self.vector[i]

#Vector must implement sort. Default is a step function.
class Interpolation:
    class outOfRange(Exception): pass
    def __init__(self, vector):
        self.vector = vector
        self.vector.sort()

    def generate_table(self,step=0.5, initial='first',final='end'):
        if initial == 'first': initial = self.vector[0][0]
        if final   == 'end'  : final   = self.vector[-1][0]
        vector = []
        while initial < final+step:
            vector.append(self(initial))
            initial += step
        return vector
       
    def __call__(self,t):
        res = self.vector[self.find(t)]
        try: return [t, res[1],res[2]]
        except IndexError: return [t,res[1]]

    #Return first index of largest time smaller than t.
    def find( self, t, start = 0, end = 'full' ):
        if end == 'full': end = len(self.vector)-1
        if end == start:
            if t < self.vector[start][0]: return start-1
            return start
        rng = end - start
        if t == self.vector[rng/2+start][0]: return rng/2+start
        if t < self.vector[rng/2+start][0]:
            if t >= self.vector[rng/2+start-1][0]:
                return start+rng/2-1
            return self.find(t,start,start+rng/2)
        return self.find(t,start+rng/2+1,end)
        

class linear(Interpolation):
    def __call__(self, t):
        if t < self.vector[0][0] or t > self.vector[-1][0]:
            raise self.outOfRange( "Got time=%f"%t +
                ", edges are %f and %f."%(self.vector[0][0],self.vector[-1][0]));
        if t >= self.vector[-1][0]: return self.vector[-1]
        index = self.find(t)
        last  = self.vector[index]
        line  = self.vector[index+1]
        slope = (line[1]-last[1])/float(line[0]-last[0])
        #TODO fix error slope
        err_slope = 0
        try: return [t,last[1]+slope*(t-last[0]), last[2]]
        except IndexError: return [t,last[1]+slope*(t-last[0])]

