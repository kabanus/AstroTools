#Make an even simpler plotting interface

import matplotlib.pyplot as plt
plt.ion()
class Iplot(object):
    block=False
    class axis(object):
        def __init__(self,sizer,labelr,ind):
            self.sizer  = sizer
            self.labelr = labelr
            self.ind = ind
        def resize(self,start = None,stop = None):
            if stop == None:
                stop = plt.axis()[self.ind*2+1]
            if start == None:
                start = plt.axis()[self.ind*2]
            if start >= stop: raise Exception("Bad range! stop must be greater then start: "+str(start)+">="+str(stop))
            self.sizer(start,stop)
        def get_bounds(self):
            return plt.axis()[self.ind*2:self.ind*2+2]
        def label(self,title):
            self.labelr(title)

    x = axis(plt.xlim,plt.xlabel,0) 
    y = axis(plt.ylim,plt.ylabel,1)
    
    @staticmethod
    def clearPlots():
        plt.clf()
        if plt.isinteractive():
            plt.show(block=False)

    #Can send this a curve, ccf table or any list. If args contain
    #scatter all plots after will be scatter plots.
    @staticmethod
    def plotCurves(kwargsList=(),*args,**kwargs):
        if not args: return
        my = mx = float("Inf")
        My = Mx = float("-Inf")
        index = col = 0
        cols = 1.0/len(args)
        plotter = plt.plot
        autosize = True
        for c in args:
            if c == 'nosize':
                autosize = False
                continue
            if c == 'scatter': 
                plotter = plt.scatter
                continue
            try: xv = c.vector
            except AttributeError: xv = c
            tmp = zip(*xv)
            if len(tmp) == 4:
                xv = (tmp[0],tmp[2],tmp[3],tmp[1])
            elif len(tmp) < 4:
                xv = tmp
            else: raise Exception("Data has more than 4 columns!")
            try:
                kwargsl = kwargsList[index]
                index+=1
                plotter(*xv[:2],c=[col,0,1-col],**dict(kwargsl,**kwargs))
            except IndexError:
                if plotter == plt.scatter:
                    plotter(*xv[:2],s=2,c=[col,0,1-col],**kwargs)
                else: 
                    plotter(*xv[:2],c=[col,0,1-col],**kwargs)
            if len(tmp) > 2: 
                plt.errorbar(*xv,linestyle="None",capsize = 0)
            if autosize:
                if min(xv[0]) < mx or max(xv[0]) > Mx or\
                   min(xv[1]) < my or max(xv[1]) > My:
                    stepx = abs(xv[0][1] - xv[0][0]) 
                    stepy = abs(xv[1][1] - xv[1][0]) 
                    if min(xv[0]) < mx: mx = min(xv[0])
                    if max(xv[0]) > Mx: Mx = max(xv[0])
                    if min(xv[1]) < my: my = min(xv[1])
                    if max(xv[1]) > My: My = max(xv[1])
            col += cols
        if autosize:
            plt.xlim(mx-stepx,Mx+stepx)
            plt.ylim(my-stepy,My+stepy)
        if plt.isinteractive():
            plt.show(block=Iplot.block)

    @staticmethod
    def annotate(labels,data,**kwargs):
        for i in range(len(labels)):
            plt.annotate(labels[i],xy=data[i],textcoords='offset points',
                         xytext=(-15,10),**kwargs)

    @staticmethod
    def quiet():
        plt.ioff()
    @staticmethod
    def loud():
        plt.ion()

    @staticmethod
    def export(name,ptype = 'ps'):
        plt.savefig(name + '.' + ptype,bbox_inches='tight')

    @staticmethod
    def help():
        print("-I- Helper class for plotting. You can:")
        print("-I- clearPlots      = Clear plot window.")
        print("-I- plotCurves      = Accepts any number of curves and plots them.")
        print("-I-                   Can be used with *Iccf.tables and Iccf.peaks.")
        print("-I-                   'scatter' keyword will make all remaining plots scatter.")
