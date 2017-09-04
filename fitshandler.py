from astropy.io        import fits
from astropy.table     import Table
from numpy             import __dict__ as npdict
from numpy             import int    as ndint
from numpy             import max    as ndmax
from numpy             import append as ndappend
from numpy             import concatenate as ndconc
from numpy             import array,dot,inf,delete,sort,zeros,where,arange
from numpy             import unravel_index,argmax,isnan,ones,fromfile

from matplotlib.pyplot import show,figure
import re

class fitsHandler(object):
    def group(self,binfactor = None,reset = True):
        if reset:
            self.reset()
        if binfactor: 
            self.grouping = binfactor

    @staticmethod
    def rebin(model,binfactor,scale = lambda: 1):
        res = model/scale()
        res[isnan(res)] = 0
        res = fitsHandler.ndrebin(res,binfactor)
        return res

    @staticmethod
    def ndrebin(arr, rebin, function = 'mean'):
        if rebin <= 1: return arr
        start = arr[:(arr.shape[0]//rebin)*rebin].reshape(arr.shape[0]//rebin,-1,*arr.shape[1:])
        final = arr[(arr.shape[0]//rebin)*rebin:]
        
        arr = npdict[function](start,axis=1)
        if final.any():
            arr = ndappend(arr,npdict[function](final,axis=0))
        return arr
    
    @staticmethod
    def padgrouped(vector, binfactor):
        res = [] 
        for line in vector:
            count = 1
            res.append(line)
            while count < binfactor:
                res.append(line)
                count += 1
        return res

class Response(fitsHandler):
    def __init__(self, response):
        fitsio           = fits.open(response)
        self.ominebounds = array(list(fitsio['EBOUNDS'].data))[:,1]
        self.omaxebounds = array(list(fitsio['EBOUNDS'].data))[:,2]
        self.ebins       = []
        self.ebinAvg     = []
        self.grouping    = 1

        elow  = 0
        ehigh = 1
        ngrp  = 2
        fch   = 3
        nch   = 4
        row   = 5

        energies = []
        nchannels = fitsio['MATRIX'].header['DETCHANS']
        data = list(fitsio['MATRIX'].data)
        for record in data:
            self.ebins.append(record[ehigh]-record[elow])
            self.ebinAvg.append((record[ehigh]+record[elow])/2.0)
            channel = 1
            ind = 0
            grps = record[ngrp]
            #Speed things up!!! Also - while kills speed for some reason.
            matrow = list(record[row])
            energies.append([])
            for start_channel,nchannel in zip(record[fch][:grps],record[nch][:grps]):
                for _ in range(channel,start_channel):
                    energies[-1].append(0)
                    channel += 1
                for _ in range(start_channel,start_channel+nchannel):
                    energies[-1].append(matrow[ind])
                    ind += 1
                    channel += 1
            for _ in range(channel,nchannels+1):
                channel += 1
                energies[-1].append(0)
        self.omatrix = array(energies).transpose()
        self.calcEff()
        self.reset()
        self.ebins   = array(self.ebins)
        self.ebinAvg = array(self.ebinAvg)

    def calcEff(self):
        oeff       = self.omatrix.sum(axis=0)
        self.roeff = oeff
        self.oeff  = self.omatrix.sum(axis=1)

    def ignore(self, channels):
        self.group(self.grouping,reset = False)
        self.deleted.update([c-1 for c in channels if c > 0 and c <= len(self.matrix)])
        self.matrix     = delete(self.matrix     ,list(self.deleted), axis = 0)
        self.eff        = delete(self.eff        ,list(self.deleted))

    def reset(self):
        self.deleted    = set()
        self.matrix     = array(self.omatrix,copy=True)
        self.eff        = array(self.oeff,copy=True)
        self.reff       = array(self.roeff,copy=True)
        self.minebounds = self.ominebounds.copy()
        self.maxebounds = self.omaxebounds.copy()

    def group(self, binfactor = None, reset = True):
        fitsHandler.group(self,binfactor,reset)
        self.matrix     = fitsHandler.ndrebin(self.omatrix,self.grouping,'sum')
        self.eff        = fitsHandler.ndrebin(self.oeff,self.grouping,'sum')
        self.minebounds = fitsHandler.ndrebin(self.ominebounds,self.grouping,'min')
        self.maxebounds = fitsHandler.ndrebin(self.omaxebounds,self.grouping,'max')

    def loadancr(self,ancr):
        if not ancr: return
        print("-E- Ancr support not implemented. Implement or make sure it's OK. Didn't load:"+ancr+".")

    def convolve_channels(self,vector):
        return dot(self.matrix,vector*self.ebins)

    def _to_channel(self, minX, maxX):
        minE = self.minebounds
        maxE = self.maxebounds
        if minX == maxX:
            res = where((minX > minE) & (minX <= maxE))[0]
        else:
            res = where((minX <= maxE) & (maxX > minE))[0]
        return res+1
    
    keVAfac = 12.39842
    def wl_to_channel(self,minX,maxX):
        newMax = self.keVAfac/minX if minX else inf
        return self._to_channel(self.keVAfac/maxX,newMax)
    def energy_to_channel(self,minX,maxX):
        return self._to_channel(minX,maxX)

    def energy(self,table = None, xonly = False):
        try: 
            return ((self.maxebounds+self.minebounds)*0.5)[int(table)-1]
        except IndexError:
            return ((self.maxebounds+self.minebounds)*0.5)[-1]
        except TypeError: pass
     
        channels = table[:,0].astype('int16')-1
        energy   = ((self.maxebounds+self.minebounds)*0.5)[channels].reshape(-1,1)
        eerror   = (self.maxebounds-self.minebounds)[channels].reshape(-1,1)
        if xonly:
            if len(table[0]) > 2:
                return ndconc((energy,eerror,table[:,1:]),axis=1)
            return ndappend(energy,table[:,1:2],axis=1)

        cts = table[:,1:2]/eerror
        if len(table[0]) > 2:
            error = (table[:,2:3]/eerror)
            return ndconc((energy,eerror,cts,error),axis=1)
        return ndappend(energy,cts,axis=1)

    def wl(self, table, xonly = False):
        wave      = self.energy(table,xonly)
        try: return self.keVAfac/float(wave)
        except TypeError: pass
        E         = wave[:,0]
        dltodE    = self.keVAfac/E**2
        wave[:,0] = self.keVAfac/E
        if xonly:
            if len(wave[0]) == 4:
                wave[:,1] *= dltodE
            return wave
        if len(wave[0]) == 4:
            wave[:,1]  *= dltodE #dl
            wave[:,2:] /= dltodE.reshape(-1,1)
            return wave 
        wave[:,1] /= dltodE
        return wave

class FakeResponse(object):
    def __init__(self,axis):
        self.ebinAvg = array(axis)
        self.eff     = ones(len(axis))
    def energy(self,table = None, xonly = False):
        return table        
    def wl(self,table = None, xonly = False):
        return table
    def convolve_channels(self,vector):
        return vector
    def wl_to_channel(self,minX,maxX):
        raise NotImplementedError("Can't ignore when using a text file as data.")
    def energy_to_channel(self,minX,maxX):
        raise NotImplementedError("Can't ignore when using a text file as data.")

class Data(fitsHandler):
    class lengthMismatch(Exception): pass
    def __init__(self, data, background = None, text = None):
        self.ochannels  = []
        self.ocounts    = []
        self.oscales    = []
        self.obscales   = []
        self.grouping   = 1
        self.resp       = None
        self.ancr       = None
        self.back       = None
        self.background = None

        if text is None:
            self.loadFits(data)
        else:   
            self.loadText(data,text)

        self.ochannels  = array(self.ochannels)
        self.ocounts    = array(self.ocounts)
        self.oscales    = array(self.oscales)
        self.obscales   = array(self.obscales)
        if self.ochannels[0] == 0:
            self.ochannels += 1
        self.reset()

        if background is not None:
            self.loadback(background,text)

    def loadFits(self,data):
        fitsio          = fits.open(data)
        data            = fitsio[1].data
        h               = fitsio[1].header
        self.exposure   = h['EXPOSURE']
        self.asciiflag  = False

        for key in ('RESPFILE','BACKFILE','ANCRFILE'):
            try:
                if h[key] != 'none':
                    self.__dict__[key[:4].lower()] = h[key]
            except KeyError: pass
        
        CHANNEL = "CHANNEL"
        COUNTS  = "COUNTS"
        QUALITY = "QUALITY"
        AREASCAL= "AREASCAL"
        BACKSCAL= "BACKSCAL"
       
        for record in data:
            counts  = record[COUNTS]
            self.ochannels.append(record[CHANNEL])
            try:
                q = record[QUALITY] > 0
            except KeyError:
                q = 0
            if q > 0 or counts <= 0:
                counts = 0
                self.ocounts.append(0)
                self.oscales.append(0)
                self.obscales.append(0)
            else:
                bscale = scale = 1.0
                try:
                    scale   = record[AREASCAL]
                    bscale  = record[BACKSCAL]
                except KeyError: pass
                self.ocounts.append(counts)
                self.oscales.append(scale)
                self.obscales.append(bscale)

    def loadText(self,fname,delimiter):
        self.exposure    = 1
        self.errorarray = []
        with open(fname) as data:
            for line in data:
                line = re.split(delimiter+"+",line.strip())
                self.oscales.append(1.0)
                self.obscales.append(1.0)
                self.ochannels.append(float(line[0]))
                self.ocounts.append(float(line[1]))
                self.errorarray.append(float(line[2]))
        self.errorarray = array(self.errorarray)
        self.errors = lambda rebin=1,_=1,x=self.errorarray: Data.ndrebin(x,rebin)

    def getPlot(self,rebin = 1, eff = 1):
        return ndconc((
                   Data.ndrebin(self.channels,rebin).reshape(-1,1),
                   self.cts(rebin,eff),
                   self.errors(rebin,eff)),axis=1)

    def cts(self,rebin = 1,eff = 1, row = False):
        if self.background is None:
            cts = self.counts/self.scale(eff)
        else:
            back = self.background
            cts = (self.counts/self.scale(eff) -
                   back.counts/self.bscale(eff))
        cts[isnan(cts)] = 0
        cts = Data.ndrebin(cts,rebin)
        return cts if row else cts.reshape(-1,1)

    def errors(self,rebin = 1,eff = 1, row = False):
        counts = Data.ndrebin(self.counts,rebin,'sum')
        if self.background is None:
            error = counts**0.5/Data.ndrebin(self.scale(eff),rebin,'sum')
        else:
            back    = self.background
            bcounts = Data.ndrebin(back.counts,rebin,'sum')
            error   = ( counts/Data.ndrebin(self. scale(eff),rebin,'sum')**2+
                       bcounts/Data.ndrebin(self.bscale(eff),rebin,'sum')**2)**0.5
        error[isnan(error)] = inf
        return error if row else error.reshape(-1,1)

    def scale(self, eff = 1):
        try:
            return self.scales*self.exposure*eff*self.transmission
        except AttributeError:
            return self.scales*self.exposure*eff

    def bscale(self, eff = 1):
        back = self.background
        try:
            return (back.bscales/self.bscales)*back.scales*back.exposure*eff*self.transmission
        except AttributeError:
            return (back.bscales/self.bscales)*back.scales*back.exposure*eff

    def loadback(self,background = None,text = None):
        if background is None: background = self.back
        back = Data(background,text=text)
        if self.deleted:
            back.ignore([c+1 for c in self.deleted])
        if len(back) != len(self):
            raise Data.lengthMismatch("Got "+str(background)+" with length "+str(len(back))+".")
        self.background = back

    def __len__(self):
        return len(self.channels)

    #Assume same amount of channels
    def __div__(self,other):
        try:
            other.reset()
            other.ignore((c+1 for c in self.delete))
            you   = other.cts(rebin=self.grouping)
            eyou  = other.errors(rebin=self.grouping)
        except AttributeError:
            try:
                dother = Data(other)
                dother.ignore((c+1 for c in self.deleted))
                you   = dother.cts(rebin=self.grouping)
                eyou  = dother.errors(rebin=self.grouping)
            except IOError:
                you   = Data.ndrebin(fromfile(other,sep = " "),self.grouping)
                eyou  = zeros(you.size)
        me    =  self.cts(rebin=self.grouping)
        eme   =  self.errors(rebin=self.grouping)
        if len(you) != len(me):
            raise Data.lengthMismatch("Dividing to data with different amount of channels!")

        result  = me/you
        eresult = ((eme/you)**2+(me*eyou/you**2)**2)**0.5
        return list(zip(Data.ndrebin(self.channels,self.grouping),result,eresult))

    def reset(self):
        self.deleted  = set()
        self.channels = array(self.ochannels ,copy=True)
        self.counts   = array(self.ocounts   ,copy=True)
        self.scales   = array(self.oscales   ,copy=True)
        self.bscales  = array(self.obscales  ,copy=True)
        try:
            self.transmission = array(self.otransmission,copy=True)
        except AttributeError: pass
        if self.background != None:
            self.background.reset()

    def group(self, binfactor = None, reset = True):
        fitsHandler.group(self,binfactor,reset)
        self.channels = arange(len(self.ochannels)//self.grouping+
                              (len(self.ochannels)% self.grouping>0))+1
        self.counts   = fitsHandler.ndrebin(self.ocounts,self.grouping,'sum')
        self.scales   = fitsHandler.ndrebin(self.oscales ,self.grouping,'mean')
        self.bscales  = fitsHandler.ndrebin(self.obscales,self.grouping,'mean')
        try:
            self.transmission  = fitsHandler.ndrebin(self.otransmission,self.grouping,'mean')
        except AttributeError: pass
        if self.background != None:
            self.background.group(self.grouping,reset)

    def ignore(self,channels):
        if self.asciiflag:
            raise NotImplementedError("Can't ignore when using a text file as data.")
        self.group(self.grouping,reset = False)
        self.deleted.update((c-1 for c in channels if c >= self.channels[0] and c <= self.channels[-1]))
        self.channels  = delete(self.channels ,list(self.deleted),axis = 0)
        self.counts    = delete(self.counts   ,list(self.deleted),axis = 0)
        self.scales    = delete(self.scales   ,list(self.deleted),axis = 0)
        self.bscales   = delete(self.bscales  ,list(self.deleted),axis = 0)
        try:
            self.transmission  = delete(self.otransmission, list(self.deleted),axis = 0)
        except AttributeError: pass
        if self.background != None:
            self.background.ignore(channels)
    
    def untransmit(self):
        try:
            del(self.otransmission)
            del(self.transmission)
        except AttributeError: pass

    def transmit(self,table):
        name = str(table)
        try:
            transmission = array([float(x) for x in open(table)])
        except IOError: 
            transmission = array(list(table))
        if len(transmission) != len(self.counts):
            raise Data.lengthMismatch("Got "+name+" with length "+str(len(transmission)))
        self.otransmission = transmission
        self.transmission  = delete(self.otransmission, list(self.deleted),axis = 0)

class Events(fitsHandler):
    def __init__(self, event_file):
        fitsio      = Table.read(event_file,hdu=1)
        self.events = sort(fitsio['X','Y'])
        xmax        = self.events[-1][0]
        ymax        = max((a[1] for a in self.events))
        self.map    = zeros((ymax,xmax),dtype=ndint)

        X = 0
        Y = 1
        maximum = 0
        for event in self.events:
            self.map[event[Y]-1][event[X]-1] += 1
        self.xl,self.xr,self.yb,self.yt = (1,len(self.map[0]),1,len(self.map))
      
    def outOfBound(self,x,y):
        return x < self.xl or x > self.xr or y < self.yb or y > self.yt

    def _plotval(self,x,y):
        x = int(x+1)
        y = int(y+1)
        try:
            if self.outOfBound(x,y): return 'Out'
            return str(self[x,y])
        except IndexError: 
            return 'Out'

    def plot(self):
        fig  = figure()
        axes = fig.add_subplot(111)
        vals = lambda x,y: 'x=%d, y=%d, z=%s'%(x+1,y+1,self._plotval(x,y))
       
        img = axes.imshow(self.map,origin='lower',cmap='gray',interpolation=None)
        a    = axes.get_xticks()
        a[1] = 1
        axes.set_xticks(a)
        a    = axes.get_yticks()
        a[1] = 1
        axes.set_yticks(a)
        img.set_extent((0.5,len(self.map[0]+0.5),0.5,len(self.map)+0.5))
        axes.format_coord = vals
        show(block=False)
        return axes

    def centroid(self,ignore = ()):
        return tuple((x+1 for x in unravel_index(argmax(self.map),self.map.shape)[::-1]))

    def _validate_pixels(self,pixels,thresh):
        count = valid = 0
        for value in pixels:
            count += 1
            if value >= thresh: valid += 1
        return count,valid

    def is_effective_radius(self,center,R, thresh = None):
        if thresh == None:
            thresh = self[center]/20.0
        X,Y = center
        count = valid = 0
        for pixels in ((self[(X-R,y)] for y in range(Y-R,Y+R+1)),
            (self[(X+R,y)] for y in range(Y-R,Y+R+1)),
            (self[(x,Y-R)] for x in range(X-R+1,X+R)),
            (self[(x,Y+R)] for x in range(X-R+1,X+R))):
            res = self._validate_pixels(pixels,thresh)
            count += res[0]
            valid += res[1]
        return valid/float(count) >= 0.5

    def object(self, constant = None):
        R = 0
        center = self.centroid()
        if constant != None: return center + (constant,)
        while self.is_effective_radius(center,R): R += 1
        return center+(R,)
    
    def max(self):
        return ndmax(self.map)

    def background(self, outer_coefficient = 2, constant = None):
        x,y, Rmin = self.object()
        if constant != None: return x,y,constant[0],constant[1]
        return x,y,Rmin,Rmin*outer_coefficient

    def __iter__(self): 
        self.iter = 0
        return self

    def __next__(self):
        if self.iter == len(self.events): raise StopIteration()
        self.iter += 1
        return self.events[self.iter - 1]

    def __getitem__(self,coords):
        return self.map[coords[1]-1][coords[0]-1]

