#Make an even simpler plotting interface

import matplotlib.pyplot as plt
plt.ion()
class Iplot(object):
    block=False
    second = None
    class axis(object):
        class noSuchAxis(Exception): pass
        def __init__(self,axis):
            if axis == 'x':
                self.ind = 0
            elif axis == 'y':
                self.ind = 1
            else:
                raise noSuchAxis(axis)
            self.axis = axis
            exec("self.sizer  = Iplot.axes.set_"+axis+"lim") 
            exec("self.labelr = Iplot.axes.set_"+axis+"label")
            self.sizer2    = None
            self.labelr2   = None
            self.transform = None
        def twin(self,function):
            op = 'y'
            if self.transform == None:
                if self.ind: op = 'x'
                exec(
                    'self.second    = Iplot.axes.twin'+op+'();'+
                    'self.sizer2    = self.second.set_'+self.axis+'lim;'+
                    'self.labelr2   = self.second.set_'+self.axis+'ticklabels;'
                    )
                self.second.minorticks_on()
            self.transform = function
            self.resize()

        def resize(self,start = None,stop = None):
            if stop == None:
                stop = Iplot.axes.axis()[self.ind*2+1]
            if start == None:
                start = Iplot.axes.axis()[self.ind*2]
            if start >= stop: raise Exception("Bad range! stop must be greater then start: "+str(start)+">="+str(stop))
            self.sizer(start,stop)
            plt.draw()
            if self.sizer2 != None:
                self.sizer2(start,stop)
                #Can't comprehend to support empty labels
                newlabels = []
                exec('labels = Iplot.axes.get_'+self.axis+'majorticklabels()')
                negative = u'\u2212'
                for label in labels:
                    if label.get_text():
                        label = label.get_text()
                        if label[0] == negative:
                            label = '-' + label[1:] 
                        label = float(label)
                        try:
                            newlabels.append("%.2f"%self.transform(label))
                        except TypeError:
                            newlabels.append(self.transform(label))
                    else: newlabels.append(label.get_text())
                self.labelr2(newlabels)
            plt.draw()
        def get_bounds(self):
            return Iplot.axes.axis()[self.ind*2:self.ind*2+2]
        def label(self,title):
            self.labelr(title)

    @staticmethod
    def init():
        global Iplot
        Iplot.axes = plt.gca()
        Iplot.axes.minorticks_on()
        Iplot.x = Iplot.axis('x') 
        Iplot.y = Iplot.axis('y')
   
    @staticmethod
    def secondAxis(function,axis='x'):
        exec('axis=Iplot.'+axis)
        axis.twin(function)
    @staticmethod
    def hideSecondAxis(axis='x'):
        exec('axis=Iplot.'+axis)
        if axis.transform != None:
            axis.twin(lambda x: '')
        
    @staticmethod
    def clearPlots():
        Iplot.axes.clear()
        Iplot.axes.minorticks_on()
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
        plotter = Iplot.axes.plot
        autosize = True
        for c in args:
            if c == 'nosize':
                autosize = False
                continue
            if c == 'scatter': 
                plotter = Iplot.axes.scatter
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
                if plotter == Iplot.axes.scatter:
                    plotter(*xv[:2],s=2,c=[col,0,1-col],**kwargs)
                else: 
                    plotter(*xv[:2],c=[col,0,1-col],**kwargs)
            if len(tmp) > 2: 
                Iplot.axes.errorbar(*xv,linestyle="None",capsize = 0)
            if autosize:
                if min(xv[0]) < mx or max(xv[0]) > Mx or\
                   min(xv[1]) < my or max(xv[1]) > My:
                    stepx = abs(xv[0][1] - xv[0][0]) 
                    stepy = abs(xv[1][1] - xv[1][0])
                    if not stepx:
                        stepx = abs(stepx)
                        if not stepx: stepx = 1
                    if not stepy:
                        stepy = abs(stepy)
                        if not stepy: stepy = 1
                    if min(xv[0]) < mx: mx = min(xv[0])
                    if max(xv[0]) > Mx: Mx = max(xv[0])
                    if min(xv[1]) < my: my = min(xv[1])
                    if max(xv[1]) > My: My = max(xv[1])
            col += cols
        if autosize:
            Iplot.axes.set_xlim(mx-stepx,Mx+stepx)
            Iplot.axes.set_ylim(my-stepy,My+stepy)
        if plt.isinteractive():
            plt.show(block=Iplot.block)
        if Iplot.x.transform != None: Iplot.x.resize()
        if Iplot.y.transform != None: Iplot.y.resize()

    @staticmethod
    def annotate(labels,data,**kwargs):
        for i in range(len(labels)):
            Iplot.axes.annotate(labels[i],xy=data[i],textcoords='offset points',
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

