from numpy import hstack,pi
from scipy.integrate import trapz
from astropy.io import fits
from glob import glob
kA    = 12.3984191
everg = 0.0000000000016022
kpcm  = 3.0856776e+21
herg  = 6.62607015e-27
evErg = 1.602177e-12 
c     = 2997924580000000000

def getArray(fname,*recs):
    with fits.open(fname) as ft:
        return hstack([ft[2].data[rec][:,None] for rec in recs])

def loadLines(fname='xout_lines1.fits',rng=(0.3,2.0)):
    global kA
    lines = getArray(fname,'wavelength','emit_outward') 
    return lines[(lines[:,0]>=kA/rng[1])&(lines[:,0]<=kA/rng[0])]

def loadCont(fname='xout_cont1.fits',rng=(0.3,2.0)):
    cont = getArray(fname,'energy','emit_outward') 
    return cont[(cont[:,0]>=rng[0]*1000)&(cont[:,0]<=rng[1]*1000)]
 
def makeFlux(cont,D=1):
    global kpcm,herg,evErg
    cont = cont.copy()
    cont[:,1] *= (1E38*cont[:,0]*evErg/herg/c/4/pi/kpcm**2/D**2)
    cont[:,0]=kA*1000/cont[:,0]
    return cont

def genAll(what,fname,logxi_dir='.',**opt):
    for f in glob(logxi_dir+'/logxi_*/'+fname):
        xi = float(f.split('/')[-2].split('_')[-1])
        yield xi,what(f,**opt)

def lineLum(wlarr = None):
    if wlarr is None: wlarr = loadLines()
    return sum(wlarr[:,1])*1E38
def contLum(enarr = None):
    global everg
    if enarr is None: enarr = loadCont()
    return 1E38*trapz(enarr[:,1],enarr[:,0]*everg)

