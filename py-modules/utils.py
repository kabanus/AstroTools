from time import clock

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


