#Make an even simpler plotting interface
import matplotlib.pyplot as plt
from   matplotlib.ticker import ScalarFormatter, FuncFormatter, NullFormatter
import warnings
from numpy import array
warnings.filterwarnings('ignore')

SF = ScalarFormatter()
plt.ion()
class Iplot(object):
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
            if self.sizer2 is None:
                if self.ind: op = 'x'
                exec(
                    'self.second    = Iplot.axes.twin'+op+'();'+
                    'self.sizer2    = self.second.set_'+self.axis+'lim;'
                    )
                plt.gcf().delaxes(Iplot.axes)
                plt.gcf().add_axes(Iplot.axes)
            self.transform = function
            if function is not None:
                exec("self.second."+self.axis+
                    "axis.set_major_formatter(FuncFormatter"+
                    "(lambda c,p,t=self.transform: SF.format_data_short(t(c))))")
            else:
                exec("self.second."+self.axis+"axis.set_major_formatter(NullFormatter())")
                self.second.minorticks_on()
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
            if self.sizer2 is not None:
                self.sizer2(start,stop)
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

    pickstate = None
    @staticmethod
    def onclick(event):
        if event.mouseevent.button == 3:
            try: event.artist.arrow.remove()
            except (AttributeError,ValueError): pass
            try: event.artist.remove()
            except (ValueError): pass
        else: Iplot.pickstate = event.artist
    
    @staticmethod
    def release(event):
        if Iplot.pickstate is not None:
            xy                 = [event.xdata,event.ydata]
            Iplot.pickstate.set_position((0,2))
            Iplot.pickstate.xy = xy
            try:
                origArrow          = Iplot.pickstate.arrow.get_xy()
                origArrow[3:5]     = xy
                Iplot.pickstate.arrow.set_xy(origArrow)
            except AttributeError: pass
            Iplot.pickstate    = None
        try: plt.gcf().canvas.draw()
        except TypeError: pass

    @staticmethod
    def init():
        global Iplot
        Iplot.axes = plt.gca()
        Iplot.axes.minorticks_on()
        Iplot.x = Iplot.axis('x') 
        Iplot.y = Iplot.axis('y')
        Iplot.col = 0
        Iplot.plots = list()
        Iplot.clearPlots()
        plt.gcf().canvas.mpl_connect('pick_event',Iplot.onclick)
        plt.gcf().canvas.mpl_connect('button_release_event',Iplot.release)
   
    @staticmethod
    def secondAxis(function,axis='x'):
        exec('axis=Iplot.'+axis)
        axis.twin(function)
        plt.draw()
    @staticmethod
    def hideSecondAxis(axis='x'):
        exec('axis=Iplot.'+axis)
        if axis.transform != None:
            axis.twin(None)
            plt.draw()
        
    @staticmethod
    def clearPlots(keepannotations = False):
        try: 
            if keepannotations: annotations = Iplot.axes.texts
            Iplot.axes.clear()
            if keepannotations: Iplot.axes.texts = annotations

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
            for child in Iplot.axes.collections+Iplot.axes.lines:
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
        try: offset = kwargs.pop("offset")
        except KeyError: offset = (0,0)
        try: 
            xytexts = kwargs.pop("xytexts")
            xytext  = xytexts
        except KeyError: 
            xytext = (0,2)
            xytexts = None
        pixel_diff = 1
        
        boxes = []
        for annotation in Iplot.axes.texts:
            boxes.append(annotation.get_window_extent())

        newlabs = []
        for i in range(len(labels)):
            try: 
                len(xytexts[i])
                xytext = xytexts[i]
            except TypeError: pass
                
            try:
                loc = [d+o for d,o in zip(data[i],offset)]
                a = Iplot.axes.annotate(labels[i],xy=loc,textcoords='offset pixels',
                                        xytext=xytext,picker = True,**kwargs)
            except AttributeError: 
                Iplot.init()
                a = Iplot.axes.annotate(labels[i],xy=data[i],textcoords='offset pixels',
                                        xytext=xytext,picker = True,**kwargs)
            newlabs.append(a)
        plt.gcf().canvas.draw()
        xstart,xstop = Iplot.x.get_bounds()
        ystart,ystop = Iplot.y.get_bounds()
        xtickshift  = (Iplot.axes.get_xticks()[1]-Iplot.axes.get_xticks()[0])
        ytickshift  = (Iplot.axes.get_yticks()[1]-Iplot.axes.get_yticks()[0])
        for i in range(len(labels)):
            a = newlabs[i]
            cbox = a.get_window_extent()
            arrow = False
            if slide is not None:
                direct  = int((slide[0] - 0.5)*2)
                current = -direct*float("inf")
                while True:
                    overlaps = False
                    count = 0
                    for box in boxes:
                        if cbox.overlaps(box):
                            if direct*box.get_points()[slide] > direct*current:
                                overlaps = True
                                current =  box.get_points()[slide] 
                                shift   = direct*(current - cbox.get_points()[1-slide[0],slide[1]])
                    if not overlaps: break
                    position = array(a.get_position())
                    position[slide[1]] += shift * direct * pixel_diff
                    a.set_position(position)
                    cbox = a.get_window_extent()
                    arrow = True
            x,y = Iplot.axes.transData.inverted().transform(cbox)[0]
            if x < xstart: xstart = x - xtickshift 
            if x > xstop : xstop  = x + xtickshift 
            if y < ystart: ystart = y - ytickshift 
            if y > ystop : ystop  = y + ytickshift 
            if arrow or offset[0] or offset[1]:
                a.arrow = Iplot.axes.arrow(x,y,data[i][0]-x,data[i][1]-y,head_length=0,head_width=0)
            boxes.append(cbox)
        plt.draw()
        return (xstart,xstop,ystart,ystop)

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

