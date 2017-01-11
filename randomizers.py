#Functions accepting a vector, then randomizes something.
#Some of these require an error for the y.
#Most of these are easy to implement, but also native.
from numpy import append as ndappend
import random
def points(vector,errors = None):
    if errors is not None:
        try: 
            vector = [list(v) + list(e) for v,e in zip(vector,errors)]
        except TypeError:
            vector = [[v,e] for v,e in zip(vector,errors)]
        return [random.gauss(p[-2],p[-1]) for p in vector]
    return [p[:-2]+[random.gauss(p[-2],p[-1])]+[p[-1]]
                                        for p in vector]

#This is native. k may either be a function
#accepting the vector or an integer, defini
#ing sample size.
def sample( vector, k = lambda x: int(0.9*len(x)) or 1 ):
    try: return random.sample(vector,k(vector))
    except: return random.sample(vector, k)

class hashed0list(list):
    def __hash__(self): return self[0].__hash__()

def sampleWithRepeat( vector ):
    res = set()
    for _ in range(len(vector)):
        res.add(hashed0list(random.choice(vector)))
    return list(res)

