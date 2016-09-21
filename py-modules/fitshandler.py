
from astropy.io        import fits
from astropy.table     import Table
from numpy             import int as ndint
from numpy             import max as ndmax
from numpy             import array,dot,inf,delete,sort,zeros,unravel_index,argmax
from itertools         import izip
from matplotlib.pyplot import imshow,show,figure

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
        self.omatrix  = array(energies).transpose()
        self.reset() 
        self.ebins    = array(self.ebins)
        self.ebinAvg  = array(self.ebinAvg)

    def ignore(self, channels):
        self.deleted.update([c-1 for c in channels if c > 0 and c <= len(self.omatrix)])
        self.matrix = delete(self.omatrix,list(self.deleted), axis = 0)

    def reset(self):
        self.deleted = set()
        self.matrix  = array(self.omatrix,copy=True)

    def convolve_channels(self,vector):
        return dot(self.matrix,vector*self.ebins)

    keVAfac = 12.39842
    def energy(self,table = None, forwl = False, ignore = []):
        if ignore:
            for channel in range(len(self.omatrix)):
                e0,e1  = self.ebounds[channel]
                if not e0 or not e1:
                    yield 0
                    continue
                energy = (e0+e1)/2.0
                w0 = self.keVAfac/e1
                w1 = self.keVAfac/e0
                wl = self.keVAfac/energy
                if ignore[0] == ignore[1]:
                    if ((not forwl and e0 <= ignore[0] and e1 >= ignore[0]) or
                        (forwl and w0 <= ignore[0] and w1 >= ignore[0])):
                        yield channel + 1
                else:
                    if ((not forwl and energy >= ignore[0] and energy <= ignore[1]) or
                        (forwl and wl >= ignore[0] and wl <= ignore[1])):
                        yield channel + 1
        else:
            for row in table:
                if len(row) == 2:
                    channel,count = row
                else:
                    channel,count,error = row
                channel = int(channel - 1)
                energy = (self.ebounds[channel][1]+self.ebounds[channel][0])/2.0
                eerror = (self.ebounds[channel][1]-self.ebounds[channel][0])
                cts    = count/eerror
                if len(row) > 2: 
                    error  = error/eerror
                    yield [energy,eerror,cts,error]
                else:
                    if forwl:
                        yield [energy,eerror,cts]
                    else:
                        yield [energy,cts]

    def wl(self, table):
        for row in self.energy(table, True):
            E  = row[0]
            dE = row[1]
            dl = self.keVAfac*dE/E**2
            row[0] = self.keVAfac/row[0]
            if len(row) > 3:
                row[1] = dl
                row[2] = row[2]*dE/dl
                row[3] = row[3]*dE/dl
                yield row
            else:
                yield (row[0],row[2]*dE/dl)

class Data(fitsHandler):
    class lengthMismatch(Exception): pass

    def __init__(self, data, background = None):
        fitsio          = fits.open(data)
        data            = fitsio[1].data
        h               = fitsio[1].header
        self.exposure   = h['EXPOSURE']
        self.resp       = None
        self.background = None
        try:
            if h['RESPFILE'].lower() != 'none':
                self.resp   = h['RESPFILE']
        except KeyError: pass
        try:
            if h['BACKFILE'].lower() != 'none':
                background = h['BACKFILE']
        except KeyError: pass
        self.ochannels  = []
        self.octs       = []
        self.ocounts    = []
        self.oscales    = []
        self.obscales   = []
        self.oerrors    = []
        self.grouping   = 1

        #CHANNEL = "CHANNEL"
        COUNTS  = "COUNTS"
        QUALITY = "QUALITY"
        AREASCAL= "AREASCAL"
        BACKSCAL= "BACKSCAL"
       
        row = 1
        for record in data:
            counts  = record[COUNTS]
            self.ochannels.append(row)
            row += 1
            try:
                q = record[QUALITY] > 0
            except KeyError:
                q = 0
            if q > 0 or counts <= 0:
                counts = 0
                self.ocounts.append(0)
                self.oscales.append(0)
                self.obscales.append(0)
                self.octs.append(0)
                self.oerrors.append(inf)
            else:
                bscale = scale = 1.0
                try:
                    scale   = record[AREASCAL]
                    bscale   = record[BACKSCAL]
                except KeyError: pass
                self.ocounts.append(counts)
                self.oscales.append(scale)
                self.obscales.append(bscale)
                self.octs.append(counts/self.exposure/scale)
                self.oerrors.append(counts**0.5/self.exposure/scale)

        self.ochannels  = array(self.ochannels)
        self.octs       = array(self.octs)
        self.ocounts    = array(self.ocounts)
        self.oscales    = array(self.oscales)
        self.obscales   = array(self.obscales)
        self.oerrors    = array(self.oerrors)
        self.reset()

        if background != None:
            self.loadback(background)

    def loadback(self,background):
        back = Data(background)
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

    def __getitem__(self,i):
        return self.channels[i],self.counts[i],self.errors[i]*self.exposure*self.scales[i]

    def __div__(self,other):
        you   = list(other.rebin(self.grouping,counts=True,include_bad=True))
        me    = list( self.rebin(self.grouping,counts=True,include_bad=True))
        div   = []
        err   = []
        for i in range(len(you)):
            if you[i][1]:
                you[i][1] = float(you[i][1])
                div.append(me[i][1]/you[i][1])
                err.append( ((me[i][2]/you[i][1])**2+(me[i][1]*you[i][2]/you[i][1]**2)**2)**0.5 )
            else:
                div.append(0)
                err.append(0)
        return div,err

    def reset(self):
        self.deleted  = set()
        self.channels = array(self.ochannels ,copy=True)
        self.cts      = array(self.octs      ,copy=True)
        self.counts   = array(self.ocounts   ,copy=True)
        self.scales   = array(self.oscales   ,copy=True)
        self.bscales  = array(self.obscales  ,copy=True)
        self.errors   = array(self.oerrors   ,copy=True)
        try:
            self.transmission = array(self.otransmission,copy=True)
        except AttributeError: pass
        if self.background != None:
            self.background.reset()

    def ignore(self,channels):
        self.deleted.update([c-1 for c in channels if c >= self.ochannels[0] and c <= self.ochannels[-1]])
        self.channels  = delete(self.ochannels ,list(self.deleted),axis = 0)
        self.cts       = delete(self.octs      ,list(self.deleted),axis = 0)
        self.counts    = delete(self.ocounts   ,list(self.deleted),axis = 0)
        self.scales    = delete(self.oscales   ,list(self.deleted),axis = 0)
        self.errors    = delete(self.oerrors   ,list(self.deleted),axis = 0)
        try:
            self.transmission  = delete(self.otransmission, list(self.deleted),axis = 0)
            self.cts    /= self.transmission
            self.errors /= self.transmission
        except AttributeError: pass
        if self.background != None:
            self.background.ignore(channels)

    def transmit(self,table):
        try:
            transmission = array([float(x) for x in open(table)])
        except: transmission = array(list(table))
        if len(transmission) != len(self.cts):
            raise Data.lengthMismatch("Got "+str(transmission)+" with length "+str(len(transmission))+".")
        self.otransmission = transmission
        self.transmission  = delete(self.otransmission, list(self.deleted),axis = 0)
        self.cts /= self.transmission

    @staticmethod
    def scaleCounts(data,scale,back = 0.0,bscale = 1.0):
        result = data/scale-back/bscale
        error  = ((1/scale)**2*data+(1/bscale)**2*back)**0.5
        return result,error

    #Plotter
    def rebin(self,binfactor = None, model = None, errors = None, counts = False, include_bad = False):
        if binfactor == None:
            binfactor = self.grouping
        cts = self.counts
        if model != None:
            cts = model
        
        ind = 0
        bscale = 1
        bcount = 0
        while ind < len(self.channels):
            sums = [0,0,0]
            if model != None and errors == None:
                sums = [0,0]

            scale = count = trans = 0
            if self.background != None:
                bcount  = bscale = bsscale = bbscale = 0
            while count < binfactor and ind < len(self.channels) and (not sums[0] or self.channels[ind]-self.channels[ind-1] == 1):
                scale   += self.scales[ind]
                sums[0] += self.channels[ind]
                sums[1] += cts[ind]
                if self.background != None:
                    bscale  += self.bscales[ind]
                    bcount  += self.background.counts[ind]
                    bsscale += self.background.scales[ind]
                    bbscale += self.background.bscales[ind]
                count   += 1
                if errors != None:
                    sums[2] += errors[ind]
                try: trans += self.transmission[ind]
                except AttributeError: pass
                ind += 1
            
            sums[0] /= float(count)
            if model == None:
                if self.background != None:
                    if bscale:
                        bscale = (bbscale/bscale)*bsscale
               
                if not bscale or not scale:
                    if not include_bad: continue
                    sums[1] = bcount = 0
                    scale   = bscale = 1
                  
                if not counts:
                    scale *= self.exposure
                    if self.background != None:
                        bscale *= self.background.exposure

                    if trans:
                        trans /= float(count)
                        scale *= trans
                        if self.background != None:
                            bscale *= trans
                sums[1],sums[2] = Data.scaleCounts(sums[1],scale,bcount,bscale)
            else:
                sums[1] /= float(count)
                if errors != None:
                    sums[2] /= float(count)
            yield sums

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

    def object(self):
        R = 0
        center = self.centroid()
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

