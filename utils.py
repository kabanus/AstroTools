from time import clock
from itertools import tee,izip
from inspect import getsourcelines

def printfunc(func):
    print ''.join(getsourcelines(func)[0])

def lookin(module,string,nodir = False):
    lst = dir(module)
    if nodir: lst = module
    for x in lst:
        if string.lower() in x.lower(): print x

def frange(stop,start=None,step=1):
    if start != None:
        tmp   = stop
        stop  = start
        start = tmp
    else: start = 0
    while start < stop:
        yield start
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
    t = 0 
    for _ in range(iters):
        begin = clock()
        com() 
        t+= (clock()-begin)
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
            amount = num/value
            if div == 2 and amount == 4 and numeral != 'M': 
                #If amount > 4 we have a problem
                result += numeral + numerals[index-1][0]
            elif (div == 5 and numeral != 'I' and num/numerals[index+1][1] == 9
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
        return izip(*iterators)
    return izip(*[iter(iterable)]*n)

