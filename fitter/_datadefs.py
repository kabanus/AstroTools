from fitshandler import Response, Data, FakeResponse
from os.path import dirname, join
from numpy import array, where


class dataResponseMismatch(Exception):
    pass


class noIgnoreBeforeLoad(Exception):
    pass


def div(self, other):
    self.division = self.data/other


def loadResp(self, resp, refresh=True):
    self.resp = Response(resp)
    self.checkLoaded()
    self.resp_file = resp
    self.updateIonLabels()
    if refresh:
        self.plot(user=False)


def loadAncr(self, ancr, refresh=True):
    self.resp.loadancr(ancr)
    self.ancr_file = ancr
    if refresh:
        self.plot(user=False)


def updateIonLabels(self, shift=None):
    self.ionlabs = []
    ions = iter(self.ionlocations)
    emin, emax = self.resp.minebounds, self.resp.maxebounds
    channeliter = iter(range(len(emin)))
    if emin[0] < emin[1]:
        channeliter = iter(range(len(emin))[::-1])

    try:
        while True:
            channel = next(channeliter)
            ion = next(ions)
            wl = shift(ion[0]) if shift is not None else ion[0]
            energy = Response.keVAfac/wl
            while energy > emax[channel]:
                ion = next(ions)
                wl = shift(ion[0]) if shift is not None else ion[0]
                energy = Response.keVAfac/wl
            while energy < emin[channel]:
                channel = next(channeliter)
            self.ionlabs.append([channel+1, energy, wl, channel, ion[1], ion[-1]])
    except StopIteration:
        pass


def loadData(self, data, text=None):
    try:
        self.resp = None
        self.data.resp = None
    except AttributeError:
        pass
    self.data = Data(data, text=text)
    for key in ('resp', 'back', 'ancr'):
        if self.data.__dict__[key] is not None:
            try:
                self.__class__.__dict__['load'+key.title()](self, self.data.__dict__[key])
            except IOError:
                try:
                    self.__class__.__dict__['load'+key.title()](self, join(dirname(data), self.data.__dict__[key]))
                except ValueError:
                    pass
            except ValueError:
                pass

    if text is not None:
        self.resp = FakeResponse(self.data.channels, self.data.minE, self.data.maxE)

    self.checkLoaded()
    self.area = array(())
    try:
        self.untransmit()
    except AttributeError:
        pass
    self.data_file = data
    self.plot(user=False)


def loadBack(self, back):
    self.data.loadback(back)
    self.back_file = back


def checkLoaded(self):
    try:
        if len(self.data.channels) != len(self.resp.matrix):
            raise self.dataResponseMismatch(len(self.data.channels), len(self.resp.matrix))
    except AttributeError:
        pass


def untransmit(self):
    self.data.untransmit()
    del(self.transmit_file)
    self.plot(user=False)


def transmit(self, table):
    self.data.transmit(table)
    self.plot(user=False)
    self.transmit_file = table


def group(self, g):
    self.reset()
    self.data.group(g)
    self.resp.group(g)
    self.plot(user=False)


def ignore(self, minX, maxX, noplot=False):
    self.set_channels(minX, maxX, 'ignore', noplot)


def notice(self, minX, maxX, noplot=False):
    self.set_channels(minX, maxX, 'notice', noplot)


def set_channels(self, minX, maxX, what, noplot):
    try:
        self.checkLoaded()
        if self.data.asciiflag:
            if self.ptype == self.WAVE:
                minX, maxX = Response.keVAfac/maxX, Response.keVAfac/minX
            channels = list(where((self.data.channels >= minX) & (self.data.channels <= maxX))[0])
            self.data.__class__.__dict__[what](self.data, channels)
        else:
            if self.ptype == self.CHANNEL:
                    channels = list(range(minX, maxX+1))
            if self.ptype == self.ENERGY:
                channels = list(self.resp.energy_to_channel(minX, maxX))
            if self.ptype == self.WAVE:
                channels = list(self.resp.wl_to_channel(minX, maxX))
            for fitshandler in (self.data, self.resp):
                fitshandler.__class__.__dict__[what](fitshandler, channels)
            if self.area.any():
                self.area = self.resp.eff
            if not channels:
                return

            minC = channels[0]
            maxC = channels[-1]
            total = maxC-minC+1
            diff = self.ionlabs[-1][3]-self.ionlabs[-1][0]
            for label in self.ionlabs:
                if what == 'ignore':
                    if label[self.CHANNEL] > maxC:
                        label[3] -= total
                    elif label[self.CHANNEL] >= minC:
                        label[3] = -1
                elif what == 'notice':
                    if label[self.CHANNEL] > maxC:
                        label[3] += total
                    elif label[self.CHANNEL] >= minC:
                        label[3] = label[0]-diff+total
        if not noplot:
            self.plot(user=False)
    except AttributeError:
        raise self.noIgnoreBeforeLoad()


def reset(self, zoom=True, ignore=True):
    if zoom:
        self.zoomto(None, None, None, None)
    if ignore:
        for fitshandler in (self.data, self.resp):
            try:
                fitshandler.reset()
            except AttributeError:
                pass
        if self.area.any():
            self.area = self.resp.eff
        for label in self.ionlabs:
            label[3] = label[0]-1
    self.plot(user=False, keepannotations=True)
