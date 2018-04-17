from utils import RomanConversion,frange
from plotInt import *
import os
defdata = os.path.dirname(os.path.realpath(__file__))+'/appdata/crossSections/Verner96.dat'

class Verner(object):
    def __init__(self,params = defdata):
        name = None
        self.cs = dict()
        for line in open(params):
            line = line.split()
            if name != line[0]:
                name = line[0]
                current = 1
            ion = name + " " + RomanConversion.toRoman(current)
            self.cs[ion] = Verner.genCS(*[float(p) for p in line[4:]])
            current += 1

    @classmethod
    def genCS(self,E0,s0,Ya,P,Yw,Y0,Y1):
        #E in eV
        def temp(E,s=s0,e=E0,yw=Yw,ya=Ya,p=P,y0=Y0,y1=Y1):
            E *= 1000.0
            x = E/e-y0
            y = (x**2+y1**2)**0.5
            return (10**-18)*s0*((x-1)**2+yw**2)*(y**(0.5*p-5.5))*(1+(y/ya)**0.5)**(-p)
        return lambda E,t=temp: t(E)

    def plot(self,ion,minE,maxE,dE):
        Iplot.init()
        Iplot.plotCurves([(E,self.cs[ion](E)) for E in frange(minE,maxE,dE)])
        
