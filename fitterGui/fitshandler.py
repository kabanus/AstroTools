
from astropy.io        import fits
from astropy.table     import Table
from numpy             import int    as ndint
from numpy             import max    as ndmax
from numpy             import append as ndappend
from numpy             import array,dot,inf,delete,sort,zeros,unravel_index,argmax,isnan,ones
from itertools         import izip
from matplotlib.pyplot import show,figure

class fitsHandler(object): pass

class Response(fitsHandler):
    def __init__(self, response):
        fitsio           = fits.open(response)
        self.ebounds     = [(elow,ehigh) for _,elow,ehigh in fitsio['EBOUNDS'].data]
        self.ebins       = []
        self.ebinAvg     = []

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
            for start_channel,nchannel in izip(record[fch][:grps],record[nch][:grps]):
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
        self.oeff    = self.omatrix.sum(axis=1)
        self.reset() 
        self.ebins    = array(self.ebins)
        self.ebinAvg  = array(self.ebinAvg)

    def ignore(self, channels):
        self.deleted.update([c-1 for c in channels if c > 0 and c <= len(self.omatrix)])
        self.matrix = delete(self.omatrix,list(self.deleted), axis = 0)
        self.eff    = delete(self.oeff,list(self.deleted))

    def reset(self):
        self.deleted = set()
        self.matrix  = array(self.omatrix,copy=True)
        self.eff     = array(self.oeff,copy=True)

    def convolve_channels(self,vector):
        return dot(self.matrix,vector*self.ebins)

    def _to_channel(self, minX, maxX, to = lambda x: x):
        eps = 0.00001
        for channel in range(len(self.omatrix)):
            e0,e1  = self.ebounds[channel]
            if not e0 or not e1:
                yield 0
                continue
            energy = (e0+e1)/2.0
            x0 = min(to(e0),to(e1))
            x1 = max(to(e0),to(e1))
            if minX == maxX:
                if x0 <= minX+eps and x1 >= minX-eps:
                    yield channel + 1
            else:
                if x0 <= maxX+eps and x1 >= minX-eps:
                    yield channel + 1
    
    keVAfac = 12.39842
    def wl_to_channel(self,minX,maxX):
        return self._to_channel(minX,maxX,lambda x: self.keVAfac/x)
    def energy_to_channel(self,minX,maxX):
        return self._to_channel(minX,maxX)

    def energy(self,table = None, xonly = False):
        for row in table:
            if len(row) == 2:
                channel,count = row
            else:
                channel,count,error = row
            channel = int(channel - 1)
            energy = (self.ebounds[channel][1]+self.ebounds[channel][0])/2.0
            eerror = (self.ebounds[channel][1]-self.ebounds[channel][0])
            if xonly:
                if len(row) > 2: 
                    yield [energy,eerror,count,error]
                else: yield [energy,count]
                continue
            cts    = count/eerror
            if len(row) > 2: 
                error  = error/eerror
                yield [energy,eerror,cts,error]
            else:
                yield [energy,cts]

    def wl(self, table, xonly = False):
        for row in self.energy(table, xonly):
            row = list(row)
            E  = row[0]
            dltodE = self.keVAfac/E**2
            row[0] = self.keVAfac/E
            if xonly:
                if len(row) == 4:
                    row[1] = dltodE*row[1] #dl
                yield row
                continue
            if len(row) == 4:
                row[1] = dltodE*row[1] #dl
                row[2] = row[2]/dltodE
                row[3] = row[3]/dltodE
                yield row
            else:
                yield [row[0],row[1]/dltodE]

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
        self.background = None

        if text is None:
            self.loadFits(data)
        else:   
            self.loadText(data,text)

        self.ochannels  = array(self.ochannels)
        self.ocounts    = array(self.ocounts)
        self.oscales    = array(self.oscales)
        self.obscales   = array(self.obscales)
        self.reset()

        if background != None:
            self.loadback(background,text)

    def loadFits(self,data):
        fitsio          = fits.open(data)
        data            = fitsio[1].data
        h               = fitsio[1].header
        self.exposure   = h['EXPOSURE']
        self.asciiflag  = False
        try:
            if h['RESPFILE'].lower() != 'none':
                self.resp   = h['RESPFILE']
        except KeyError: pass
        try:
            if h['BACKFILE'].lower() != 'none':
                background = h['BACKFILE']
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
                    bscale   = record[BACKSCAL]
                except KeyError: pass
                self.ocounts.append(counts)
                self.oscales.append(scale)
                self.obscales.append(bscale)

    def loadText(self,fname,delimiter):
        self.exposure    = 1
        self.errorarray = []
        with open(fname) as data:
            for line in data:
                self.oscales.append(1.0)
                self.obscales.append(1.0)
                line = line.split(delimiter)
                self.ochannels.append(float(line[0]))
                self.ocounts.append(float(line[1]))
                self.errorarray.append(float(line[2]))
        self.errorarray = array(self.errorarray)
        self.errors = lambda rebin=1,_=1,x=self.errorarray: Data.ndrebin(x,rebin)

    @staticmethod
    def rebin(model,binfactor,scale = lambda: 1):
        res = model/scale()
        res[isnan(res)] = 0
        res = Data.ndrebin(res,binfactor)
        return res

    @staticmethod
    def ndrebin(arr, rebin, sumit = False):
        if rebin <= 1: return arr
        start = arr[:(arr.shape[0]/rebin)*rebin].reshape(arr.shape[0]//rebin,-1)
        final = arr[(arr.shape[0]/rebin)*rebin:]
        if not sumit:
            arr = start.mean(1)
            if final.any():
                arr = ndappend(arr,final.mean())
        else:
            arr = start.sum(1)
            if final.any():
                arr = ndappend(arr,final.sum())
        return arr

    def getPlot(self,rebin = 1, eff = 1):
        return zip(self.channels,self.cts(rebin,eff),self.errors(rebin,eff))

    def cts(self,rebin = 1,eff = 1):
        if self.background is None:
            cts = self.counts/self.scale(eff)
        else:
            back = self.background
            cts = (self.counts/self.scale(eff) -
                   back.counts/self.bscale(eff))
        cts[isnan(cts)] = 0
        cts = Data.ndrebin(cts,rebin)
        return cts

    def errors(self,rebin = 1,eff = 1):
        counts = Data.ndrebin(self.counts,rebin,sumit = True)
        if self.background is None:
            error = counts**0.5/Data.ndrebin(self.scale(eff),rebin,sumit = True)
        else:
            back    = self.background
            bcounts = Data.ndrebin(back.counts,rebin, sumit = True)
            error   = ( counts/Data.ndrebin(self. scale(eff),rebin,sumit=True)**2+
                       bcounts/Data.ndrebin(self.bscale(eff),rebin,sumit=True)**2)**0.5
        error[isnan(error)] = inf
        return error

    def scale(self, eff = 1):
        try:
            return self.scales*self.exposure*eff*self.transmission
        except AttributeError:
            return self.scales*self.exposure*eff

    def bscale(self, eff = 1):
        back = self.background
        try:
            return (back.bscale/self.bscale)*back.scale*back.exposure*eff*self.transmission
        except AttributeError:
            return (back.bscale/self.bscale)*back.scale*back.exposure*eff

    def loadback(self,background,text = False):
        back = Data(background,text)
        if self.deleted:
            back.ignore([c+1 for c in self.deleted])
        if len(back) != len(self):
            raise Data.lengthMismatch("Got "+str(background)+" with length "+str(len(back))+".")
        self.background = back

    def group(self,binfactor):
        self.grouping = binfactor

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

    def __len__(self):
        return len(self.channels)

    #Assume same amount of channels
    def __div__(self,other):
        you   = other.cts(rebin=self.grouping)
        me    =  self.cts(rebin=self.grouping)
        eyou  = other.errors(rebin=self.grouping)
        eme   =  self.errors(rebin=self.grouping)
        if len(you) != len(me):
            raise Data.lengthMismatch("Dividing to data with different amount of channels!")

        result  = me/you
        eresult = ((eme/you)**2+(me*eyou/you**2)**2)**0.5
        return zip(Data.ndrebin(self.channels,self.grouping),result,eresult)

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

    def ignore(self,channels):
        if self.asciiflag:
            raise NotImplementedError("Can't ignore when using a text file as data.")
        self.deleted.update([c-1 for c in channels if c >= self.ochannels[0] and c <= self.ochannels[-1]])
        self.channels  = delete(self.ochannels ,list(self.deleted),axis = 0)
        self.counts    = delete(self.ocounts   ,list(self.deleted),axis = 0)
        self.scales    = delete(self.oscales   ,list(self.deleted),axis = 0)
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

    def next(self):
        if self.iter == len(self.events): raise StopIteration()
        self.iter += 1
        return self.events[self.iter - 1]

    def __getitem__(self,coords):
        return self.map[coords[1]-1][coords[0]-1]

