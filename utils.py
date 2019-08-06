from time      import clock
from itertools import tee
from inspect   import getsourcelines
from importlib import reload
from os        import getcwd
import readline as rl

class ArgLess(object):
    def __init__(self,func,args = [],doneStr = '',verbose=False):
        self.f = func
        self.d = doneStr
        self.a = args
        self.v = verbose
    def __call__(self):
        return self.f(*self.a)
    def __repr__(self):
        res = self()
        if self.v:
            print(res,end='')
        return self.d

def history(start = 0, end = None,concat=False):
    if end is None:
        end = rl.get_current_history_length()
    if start < 0:
        start += rl.get_current_history_length()
    if concat:
        print(';'.join(rl.get_history_item(i+1) for i in range(start,end)))
        return
    for i in range(start,end):
        print(str(i+1)+":",rl.get_history_item(i+1))

hist = ArgLess(history)
pwd  = ArgLess(getcwd,verbose=True)

def whist(fname): rl.write_history_file(fname)
def rhist(fname): 
    code = []
    with open(fname) as fd:
        for line in fd:
            if not line.strip(): continue
            code.append('try:')
            code.append(' '+line.strip())
            code.append(' rl.add_history("'+line.strip().replace('"','\\"')+'")')
            code.append('except: pass')
    while True:
        try:
            exec("\n".join(code).encode(),globals())
            break
        except SyntaxError as e:
            print(e,code[e.lineno-1])
            for _ in range(4): del code[e.lineno-2]
    return a,b,code,skip

def printlist(lst, width = None, delim = "\n"):
    try:
        if width is not None:
            form = ('{:<'+str(width)+'}')*len(lst[0])
            print(delim.join(form.format(*y) for y in lst))
        else: 
            print(delim.join((" ".join((str(x) for x in y)) for y in lst)))
    except TypeError:
        print(delim.join((str(y) for y in lst)))

def printfunc(func):
    print(''.join(getsourcelines(func)[0]))

def lookin(module,string,nodir = False):
    lst = dir(module)
    if nodir: lst = module
    for x in lst:
        if string.lower() in x.lower(): print(x)

def frange(stop,start=None,step=1,decimals=None):
    if start is not None:
        start, stop = stop, start
    else: start = 0
    if decimals is None:
        decimals = 0
        for x in (start,step):
            if x is None: continue
            strx = str(x).split('.')
            cdec = 0 if len(strx) == 1 else len(strx[1]) 
            decimals = max(decimals,cdec)
    while start < stop:
        yield round(start,decimals)
        start += step

def raToSex(coord):
    h = coord*24/360.0
    m = (h-int(h))*60
    s= (m-int(m))*60
    return int(h),int(m),s

def decToSex(coord):
    sign = coord/abs(coord)
    deg  = abs(coord)
    m    = (deg-int(deg))*60
    s    = (m-int(m))*60
    deg  = sign*int(deg)
    if not deg:
        m = sign*int(m)
        if not m:
            s = sign*s
    return deg,int(m),s

def timer(com,iters=1):
    got_e = None 
    t = 0 
    for _ in range(iters):
        begin = clock()
        try:
            com() 
            end = clock()
        except Exception as e:
            end = clock()  
            got_e = e 
        t+= (end-begin)
    if got_e is not None:
        print("Got exception",got_e)
    return t/iters

def timelist (l):
    def check():
        for _ in l: pass
    return check

class RomanConversion(object):
    numerals = (('M',1000),('D',500),('C',100),('L',50),('X',10),('V',5),('I',1))
    @staticmethod
    def toRoman(num):
        numerals = RomanConversion.numerals
        div = 5
        result = ''
        for index,(numeral,value) in enumerate(numerals):
            div = 5 if div ==2 else 2
            amount = num//value
            if div == 2 and amount == 4 and numeral != 'M': 
                #If amount > 4 we have a problem
                result += numeral + numerals[index-1][0]
            elif (div == 5 and numeral != 'I' and num//numerals[index+1][1] == 9
                           and numeral != 'M'):
                result += numerals[index+1][0] + numerals[index-1][0]
                value = numerals[index+1][1]
            else:
                result += numeral * amount #3 tops, if not M
            num %= value
        return result

    @staticmethod
    def toInt(numeral):
        numeral = numeral.upper()
        numerals = dict(RomanConversion.numerals)
        res = 0
        skip = False
        for i,roman in enumerate(numeral):
            if skip:
                skip = False
                continue
            if i < len(numeral)-1 and numerals[roman] < numerals[numeral[i+1]]:
                res += numerals[numeral[i+1]] - numerals[roman]
                skip = True
            else: res += numerals[roman]
        return res

def closest(lst,value):
    if value <= lst[0] : raise ValueError("Value to low")
    if value >= lst[-1]: raise ValueError("Value to high")

    start = 0
    end = len(lst)-1
    while end - start > 1:
        mid = (end+start)/2
        if value == lst[mid]: 
            return mid
        if value >= lst[mid]:
            start = mid
        else: end = mid
    return (start,end,(lst[end]-value)/(lst[end]-lst[start]),
                      (value-lst[start])/(lst[end]-lst[start]))

def nwise(iterable, n = 2, overlap = True):
    if overlap:
        iterators = tee(iterable, n)
        for i in range(len(iterators)):
            for j in range(i):
                next(iterators[i], None)
        return zip(*iterators)
    return zip(*[iter(iterable)]*n)

def lmap(a,b):
    return list(map(a,b))

