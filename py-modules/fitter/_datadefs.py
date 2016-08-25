from fitshandler import Response,Data

class dataResponseMismatch(Exception): pass
class noIgnoreBeforeLoad(Exception): pass

def loadResp(self,resp):
    self.resp = Response(resp)
    self.checkLoaded()
    self.resp_file = resp

def loadData(self,data):
    self.data  = Data(data)
    if self.data.resp != None:
        self.loadResp(self.data.resp)
    self.checkLoaded()
    self.plot()
    self.data_file = data

def checkLoaded(self):
    try: 
        if len(self.data.channels) != len(self.resp.matrix):
            raise self.dataResponseMismatch(len(self.data.channels),len(self.resp.matrix))
    except AttributeError: pass

def transmit(self, table):
    self.data.transmit(table)
    self.plot()
    self.transmit_file = table

def ignore(self, minX, maxX):
    try:
        self.checkLoaded()
        for fitshandler in (self.data,self.resp):
            #Need to reset generator
            if self.ptype == self.CHANNEL: channels = range(minX,maxX+1)
            if self.ptype == self.ENERGY : channels = self.resp.energy(ignore = (minX, maxX))
            if self.ptype == self.WAVE: channels    = self.resp.energy(forwl = True, ignore = (minX, maxX))
            fitshandler.ignore(channels)
        self.plot()
    except AttributeError:
        raise self.noIgnoreBeforeLoad()

def reset(self, zoom = True, ignore = True):
    if zoom:
        self.xstart = None
        self.xstop  = None
        self.ystart = None
        self.ystop  = None
    if ignore:
        for fitshandler in (self.data,self.resp):
            try:
                fitshandler.reset()
            except AttributeError: pass
            self.plot()
    self.plot()

