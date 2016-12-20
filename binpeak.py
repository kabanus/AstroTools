#Calculations for historgrams or peak finding

from numpy import convolve
import math

def Gaussian( s, m = 0 ):
    return lambda x: (1/(2*math.pi*s**2)**0.5)*math.exp(-0.5*((x-m)/s)**2)

#Static calculations
class Phistogram:
    class binsizeNotInitialized(Exception): pass
    binsize = None
    #Expect a SORTED histogram of peaks - (tau,ccf,err).
    @staticmethod 
    def rebin(points):
        try:
            i = 0
            histogram = []
            while i < len(points):
                thresh = points[i][0] + Phistogram.binsize
                histogram.append([thresh-0.5*Phistogram.binsize,1])
                i+=1
                while i < len(points) and points[i][0] < thresh:
                    histogram[-1][1]+=1
                    i+=1
            return histogram
        except TypeError:
            raise Phistogram.binsizeNotInitialized()
    @staticmethod
    def fullPeakError(histogram):
        return Phistogram.gaussPeakError(histogram,0)
    @staticmethod
    def gaussPeakError(histogram, halfConfidence = 0.16):
        index = int(halfConfidence*len(histogram))
        cm = s = 0;
        binnedhist = Phistogram.rebin(histogram)
        for x in binnedhist:
            cm += x[0]*x[1]
            s  += x[1]
        cm /= float(s)
        return (cm,(histogram[index][0],histogram[-index-1][0]), len(histogram))
    @staticmethod 
    def findPeaks(table, cutoff=0.3):
        i = 0
        res = []
        while i < len(table):
            while i < len(table)-1 and \
                  (table[i][1] > 1 or table[i][1] < cutoff or \
                  table[i+1][1] >= table[i][1]):
                i+=1 
            if i < len(table) - 1 and table[i-1][1] < table[i][1]:
                res.append(table[i])
            i+=1
        return res
 
    @staticmethod
    def smooth( histogram, width = 1 ):
        width = int(width)
        if width == 0:
            print("Warning - width must be integer. Got 0.")
            return
        g = Gaussian(width)
        convolution = convolve([x[1] for x in histogram], 
                               [g(x/float(width)) for x in range(-width,width+1)],mode='same')
        return [[histogram[i][0],convolution[i]] for i in range(len(histogram))]
    @staticmethod
    def help():
        print("-I- Helper class for calculation. Assuming an ICCF object Iccf you can:")
        print("-I- [gauss/full]")
        print("    PeakError       = Given a peak histogram, calculate the error.")
        print("-I- findPeaks       = Returns list of peaks for given table. Default cutoff is 0.6.")
        print("-I- smooth          = Smoothes the histogram.")
        print("-I- rebin           = Creates a binned histogram.")
        print("-I- This package also provides a Gaussian function.")

