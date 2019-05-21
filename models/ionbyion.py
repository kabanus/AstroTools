from glob import glob
import os.path
from model import _singleModel,modelExport
from sys import getsizeof
#Constants
from numpy import pi,exp,inf,full
c   = 3*10**5  # km/s
elec= 4.80320451*10**-10 #esu
m_e = 9.10938356*10**-28 #gram
evAfac = 12398.42
masses = { #keV
    'Fe': 52019000,
    'O' : 14903000,
    'Ni': 54672000,
    'Mg': 22640000,
    'Ne': 18797000,
    'Si': 26161000,
    'Al': 25133000,
    'Ar': 37211000,
    'C' : 11187000,
    'Ca': 37332000,
    'N' : 13047000,
    'Na': 21415000,
    'S' : 29868000
}
vconsts = [[122.607931777104326, 214.382388694706425,
     181.928533092181549, 93.155580458134410,
     30.180142196210589,  5.912626209773153,
     0.564189583562615],
     [122.607931773875350, 352.730625110963558,
     457.334478783897737, 348.703917719495792,
     170.354001821091472, 53.992906912940207,
     10.479857114260399],
     [0.5641641, 0.8718681,
     1.474395,  -19.57862,
     802.4513,  -4850.316,
     8031.468]]
globalIBIHash = {}
globalkTHash = {}
globalVHash = {}

deflinepath = os.path.dirname(os.path.realpath(__file__))+'/../appdata/ionbyion/lines'
 
class Ion:
    def __init__(self ,mass):
        self.m = mass
        self.e = [] 
        self.l = [] 
        self.t = None

@modelExport
class ibifit(_singleModel):
    description = 'Ion by ion absorption'
    def __init__(self, lines = deflinepath, fcut = 10**-3, ncut = float('inf')):
        super(ibifit,self).__init__()
        self.params = {'kT':0.1,'redshift':0,'vturb':0,'C':1}
        self.ions   = {}
        if os.path.isfile(lines):
            raise Exception('ibi from file not implemented')
        elif lines is dict:
            raise Exception('ibi from dict not implemented')
        elif os.path.isdir(lines):
            #recursive descent - make sure tree is clean.
            for elemf in glob(lines+'/*'):
                elem = os.path.basename(elemf)
                for ionf in glob(elemf+'/*'):
                    ion = os.path.basename(ionf).strip('+')
                    self.ions[ion] = Ion(masses[elem])
                    files = glob(ionf+'/*')
                    if len(files) == 1:
                        linef = files[0]
                    else:
                        linef = glob(ionf+'/lines*')[0]
                        edgef = glob(ionf+'/edge*')[0]
                        self.ions[ion].e = list(ibifit.getlines(edgef,edge = True))
                    self.ions[ion].l = list(ibifit.getlines(linef,fcut,number = ncut))
                    self.params[ion] = 0
        else:
            raise Exception("Can't understand how to init lines!")
        self.nzeroions = set()
        self.generator()
   
    @staticmethod
    def getlines(linef,fcut = 10**-3,edge = False, number = float('inf')):
        #Indices:
        wl  = 4; AAa = 6; f = 8; en = 2; a2 = 5; title = 1;
        if edge:
            #en, a0, a1, a2
            ind = list(range(en,a2+1))
            title += 1
        else:
            ind = [wl,AAa,f]
        count = -1
        for line in open(linef):
            count += 1
            if count < title:
                continue
            line = line.split()
            if not edge and float(line[f]) < fcut: continue
            yield [float(line[i]) for i in ind]
            if edge: break
            if count-title+1 >= number: break
                
    #X is frequency normaized by sigma, A is gamma normalized by sigma
    #unitless!!!! need to devide by sigma! normalized to 1 without the extra sg!!
    @staticmethod
    def voigt(X,A):
        if A <= 0.001: 
            v2 = X.copy()
            v2[X>=2.5]**=2
            v3   = 1.0
            fac1 = vconsts[2][0]
            for vc2 in vconsts[2]:
                v3   *= v2
                fac1 += vc2 / v3
            res = ((fac1 * A/v2) + exp(-v2) * (1 + (1 - 2*v2)*A**2))/pi**0.5
            indices = X<2.5
        else:
            indices = full(X.shape,True,dtype=bool)
            res = full(X.shape,0.0)

        p = A
        o = -X[indices]
        q = [vconsts[0][0], vconsts[1][0]]
        r = [0,0]
        for i in range(1,len(vconsts[0])):
            for ind in 0,1:
                q[ind] += p * vconsts[ind][i]
                r[ind] += o * vconsts[ind][i]
            tmp = p
            p = (p * A + o   * X[indices])
            o = (o * A - tmp * X[indices])
        q[1] += p
        r[1] += o
        res[indices] = (q[0]*q[1]+r[0]*r[1])/(q[1]**2+r[1]**2)/pi**0.5
        return res

    #Optical depth normalized to 10**18 Nion
    def taumodel( self, wl,ion, kT, vturb ):
        cs = 0
        m = self.ions[ion].m
        V = ((2*kT/m)*c**2+vturb**2)**0.5 #In km/s
        for line, rt, f in self.ions[ion].l:
            #Width - sqrt(2)sigma
            sg = V*10**13/line #Hz
            #Normalized frequency
            X = (c*10**13/sg)*(1/wl-1/line) #unitless
            #Normalized lorentzian width (rates/4pi=gamma, from Rybicki)
            A = (rt/4/pi)/sg  #unitless
            #unitless !!!! need to devide by sigma! Jacobian demands it!!
            voigt = self.voigt(X,A) #unitless
            add = (f/sg)*voigt #1/Hz 
            cs += add
        cs *= (pi*elec**2/m_e/(c*10**5)) #multiply by Hz cm^2 to get cm^2
        edge = self.ions[ion].e
        if len(edge): 
            edge = edge[0]
            ind  = wl<evAfac/edge[0]
            cs[ind]+=edge[1]*(evAfac/wl[ind]+edge[2])**edge[3]
        return cs

    def generator(self):
        global globalVHash, globalkTHash, globalIBIHash
        kT       = self.params['kT']
        vturb    = self.params['vturb']
        for ion in self.ions:
            exec(('self.ions[ion].t = lambda wl: self.taumodel(wl,"'+
                                                    str(ion)+'",'+
                                                    str(kT) +','+
                                                    str(vturb)+')'), locals(), globals())
         
        if globalVHash == vturb and globalkTHash == kT and getsizeof(self.wlhash) < 2**32:
            self.wlhash   = globalIBIHash 
        else:
            self.wlhash   = {}
            globalkTHash  = kT
            globalVHash   = vturb
            globalIBIHash = self.wlhash

    def ionExp(self, ion, wl, units):
        try: return -self.params[ion]*units*self.ions[ion].t(wl)
        except TypeError: raise Exception('No data found for '+ion+'!')

    def _calculate(self,atrange, units = 10**18):
        Nions = []
        gen = False
        gparams = ['kT','vturb']
        for param in self.changed:
            if param in gparams:
                if not gen:
                    self.generator()
                    gen = True
                    break
            elif param != 'redshift' and param != 'C': Nions.append(param)
     
        wl = 0.001*evAfac/(atrange*(1+self.params['redshift']))
        tau = sum(self.params[ion]*units*self.ions[ion].t(wl) for ion in self.nzeroions)
        return 1-self.params['C']*(1-exp(-tau))
    
    def sethook(self, index, key):
        gparams = ['kT','redshift','vturb','C']
        if key not in gparams:
            if self.params[key] > 0:
                self.nzeroions.add(key)
            else: 
                self.params[key] = 0
                self.nzeroions.discard(key)
        elif key == 'C':
            if self.params['C'] > 1:
                self.params['C'] = 1
            if self.params['C'] < 0:
                self.params['C'] = 0

