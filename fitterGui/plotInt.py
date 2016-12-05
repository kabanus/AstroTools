#Make an even simpler plotting interface
import matplotlib.pyplot as plt
import matplotlib
import warnings
from numpy import array
warnings.filterwarnings('ignore')

plt.ion()
class Iplot(object):
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

        def scale(self,stype):
            exec("Iplot.axes.set_"+self.axis+"scale('"+stype+"')")
    
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
            plt.draw()

    @staticmethod
    def _log(axis,off):
        if axis.get_bounds()[0] <= 0: 
            axis.resize(start=1)
        if off:
            axis.scale('linear')
        else:
            axis.scale('log')
        plt.draw()
    @staticmethod
    def xlog(off=False):
        Iplot._log(Iplot.x,off)
    @staticmethod
    def ylog(off=False):
        Iplot._log(Iplot.y,off)

    @staticmethod
    def init():
        global Iplot
        Iplot.axes = plt.gca()
        Iplot.axes.minorticks_on()
        Iplot.x = Iplot.axis('x') 
        Iplot.y = Iplot.axis('y')
        Iplot.col = 0
        Iplot.plots = list()
        Iplot.boxes = list()
        Iplot.clearPlots()
   
    @staticmethod
    def secondAxis(function,axis='x'):
        exec('axis=Iplot.'+axis)
        axis.twin(function)
        plt.draw()
    @staticmethod
    def hideSecondAxis(axis='x'):
        exec('axis=Iplot.'+axis)
        if axis.transform != None:
            axis.twin(lambda x: '')
        plt.draw()
        
    @staticmethod
    def clearPlots():
        try: 
            Iplot.axes.clear()
        except AttributeError: return
        try: Iplot.axes.legend().remove()
        except AttributeError: pass
        Iplot.plots = list()
        Iplot.axes.minorticks_on()
        plt.draw()

    @staticmethod 
    def legend(*labels,**legend_kwrags):
        label = None
        for plot,label in zip(Iplot.plots,labels):
            plot.set_label(label)
        if label is None: return 
        Iplot.axes.legend(**legend_kwrags)
        plt.draw()

    #Can send this a curve, ccf table or any list. If args contain
    #scatter makes scatter plots.
    @staticmethod
    def plotCurves(*args,**kwargs):
        if not args: return

        try: scatter = kwargs.pop('scatter')
        except KeyError: scatter = False
        try: autosize = kwargs.pop('autosize')
        except KeyError: autosize = True
        try: chain = kwargs.pop('chain')
        except KeyError: chain = False
        try: stepx = kwargs.pop('stepx')
        except KeyError: stepx = None
        try: stepy = kwargs.pop('stepy')
        except KeyError: stepy = None

        my = mx = float("Inf")
        My = Mx = float("-Inf")
        
        Iplot.col = 0
        col_step = 1.0/len(args)
        if chain:
            children = []
            for child in Iplot.axes.get_children():
                if (type(child) is not matplotlib.collections.PathCollection and
                    type(child) is not matplotlib.lines.Line2D):
                    continue
                children.append(child)
            col_step = 1.0/(len(children)+len(args))
            for child in children:
                child.set_color([Iplot.col,0,1-Iplot.col])
                Iplot.col += col_step

        try: plotter = Iplot.axes.plot
        except AttributeError: Iplot.init()
        plotter = Iplot.axes.plot
        if scatter: 
            plotter = Iplot.axes.scatter
        for c in args:
            color = [Iplot.col,0,1-Iplot.col]
            try: xv = c.vector
            except AttributeError: xv = c
            tmp = zip(*xv)
            if len(tmp) == 4:
                xv = (tmp[0],tmp[2],tmp[3],tmp[1])
            elif len(tmp) < 4:
                xv = tmp
            else: raise Exception("Data has more than 4 columns!")
            try:
                addtolist = Iplot.plots.extend
                if plotter == Iplot.axes.scatter:
                    addtolist = Iplot.plots.append
                addtolist(plotter(*xv[:2],c=color,**dict(**kwargs)))
            except IndexError:
                if plotter == Iplot.axes.scatter:
                    Iplot.plots.append(
                        plotter(*xv[:2],s=2,edgecolor=None,c=color,**kwargs))
                else: 
                    Iplot.plots.extend(plotter(*xv[:2],c=color,**kwargs))
            if len(tmp) > 2: 
                Iplot.axes.errorbar(*xv,linestyle="None",capsize = 0)
            if not chain and autosize:
                if min(xv[0]) < mx or max(xv[0]) > Mx or\
                   min(xv[1]) < my or max(xv[1]) > My:
                    if stepx == None: 
                        stepx = min(abs(max(xv[0])),abs(min(xv[0])))*0.5 if scatter else 0
                    if stepy == None:
                        stepy = stepy = min(abs(max(xv[1])),abs(min(xv[1])))*0.5 if scatter else 0
                    if min(xv[0]) < mx: mx = min(xv[0])
                    if max(xv[0]) > Mx: Mx = max(xv[0])
                    if min(xv[1]) < my: my = min(xv[1])
                    if max(xv[1]) > My: My = max(xv[1])
            Iplot.col += col_step
        if not chain and autosize:
            Iplot.axes.set_xlim(mx-stepx,Mx+stepx)
            Iplot.axes.set_ylim(my-stepy,My+stepy)
        plt.draw()
        if Iplot.x.transform != None: Iplot.x.resize()
        if Iplot.y.transform != None: Iplot.y.resize()

    @staticmethod
    def title(title,**kwargs):
        Iplot.axes.set_title(title,**kwargs)
        plt.draw()

    @staticmethod
    def annotate(labels,data,**kwargs):
        #slide should be relevant edge of bbox - e.g. (0,0) for left, (0,1) for bottom...
        try: slide = kwargs.pop("slide")
        except KeyError: slide = None
        try: 
            xytexts = kwargs.pop("xytexts")
            xytext  = xytexts
        except KeyError: 
            xytext = (0,2)
            xytexts = None
        pixel_diff = 1

        for i in range(len(labels)):
            try: 
                len(xytexts[i])
                xytext = xytexts[i]
            except TypeError: pass
                
            try:
                a = Iplot.axes.annotate(labels[i],xy=data[i],textcoords='offset pixels',
                                        xytext=xytext,**kwargs)
            except AttributeError: 
                Iplot.init()
                a = Iplot.axes.annotate(labels[i],xy=data[i],textcoords='offset pixels',
                                        xytext=xytext,**kwargs)
            
            Iplot.axes.redraw_in_frame()
            cbox = a.get_window_extent()
            if slide is not None:
                direct  = int((slide[0] - 0.5)*2)
                current = -direct*float("inf")
                arrow = False
                while True:
                    overlaps = False
                    count = 0
                    for box in Iplot.boxes:
                        if cbox.overlaps(box):
                            if direct*box.get_points()[slide] > direct*current:
                                overlaps = True
                                current =  box.get_points()[slide] 
                                shift   = direct*(current - cbox.get_points()[1-slide[0],slide[1]])
                    if not overlaps: break
                    arrow = True
                    position = array(a.get_position())
                    position[slide[1]] += shift * direct * pixel_diff
                    a.set_position(position)
                    cbox = a.get_window_extent()
                    x,y = Iplot.axes.transData.inverted().transform(cbox)[0]
                if arrow:
                    Iplot.axes.arrow(x,y,data[i][0]-x,data[i][1]-y,head_length=0,head_width=0)
            Iplot.boxes.append(cbox)
            Iplot.axes.redraw_in_frame()

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

