#Make an even simpler plotting interface
import warnings
import matplotlib.pyplot as plt
from   matplotlib.ticker  import ScalarFormatter, FuncFormatter, NullFormatter
from   matplotlib.markers import MarkerStyle as MS
from   itertools          import cycle
from   numpy              import array
import numpy as np
warnings.filterwarnings('ignore')

SF = ScalarFormatter()
plt.ion()
class Iplot(object):
    #markers = sorted((marker for marker in MS.markers.keys() 
    #    if marker not in (None,'None'," ","",',')+tuple(range(8))))
    markers = ('o','s','^','v')
    cmarker = cycle(markers)
    xytext  = (-6,20)
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
            self.sizer  = eval("Iplot.axes.set_"+axis+"lim") 
            self.labelr = eval("Iplot.axes.set_"+axis+"label")
            self.sizer2    = None
            self.labelr2   = None
            self.transform = None
        def twin(self,function):
            op = 'y'
            if self.sizer2 is None:
                if self.ind: op = 'x'
                self.second = eval('Iplot.axes.twin'+op+'()')
                self.sizer2 = eval('self.second.set_'+self.axis+'lim')
                plt.gcf().delaxes(Iplot.axes)
                plt.gcf().add_axes(Iplot.axes)
            self.transform = function
            if function is not None:
                eval("self.second."+self.axis+
                    "axis.set_major_formatter(FuncFormatter"+
                    "(lambda c,p,t=self.transform: SF.format_data_short(t(c))))")
            else:
                eval("self.second."+self.axis+"axis.set_major_formatter(NullFormatter())")
                self.second.minorticks_on()
            self.resize()

        def scale(self,stype):
            eval("Iplot.axes.set_"+self.axis+"scale('"+stype+"')")
    
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
    def _log(axis,on):
        if Iplot.plots and axis.get_bounds()[0] <= 0:
            index = 0 if axis is Iplot.x else 1
            minimum = min([min(p[0].get_xydata()[:,index]) for p in Iplot.plots])
            if minimum <= 0:
                axis.resize(start=1e-10)
        if on:
            axis.scale('log')
        else:
            axis.scale('linear')
        plt.draw()

    xlogon = False
    @staticmethod
    def xlog(on=None):
        if on is None: on = not Iplot.xlogon
        Iplot.xlogon = on
        Iplot._log(Iplot.x,on)
    ylogon = False
    @staticmethod
    def ylog(on=None):
        if on is None: on = not Iplot.ylogon
        Iplot.ylogon = on
        Iplot._log(Iplot.y,on)

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
            if xy == [None,None]: return
            try: 
                Iplot.pickstate.set_position((0,0))
                Iplot.pickstate.xy = xy
                try:
                    origArrow          = Iplot.pickstate.arrow.get_xy()
                    origArrow[3:5]     = xy
                    Iplot.pickstate.arrow.set_xy(origArrow)
                except AttributeError: pass
            except AttributeError:
                xy  = Iplot.axes.transAxes.inverted().transform((event.x,event.y))
                Iplot.axes.get_legend()._set_loc(10) #This means center
                Iplot.axes.get_legend().set_bbox_to_anchor((xy))

            Iplot.pickstate    = None
            plt.draw()
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
        for axis in ['top','bottom','left','right']:
            Iplot.axes.spines[axis].set_linewidth(2)
        Iplot.axes.xaxis.set_tick_params(width=2)
        Iplot.axes.yaxis.set_tick_params(width=2)
        Iplot.axes.xaxis.set_tick_params(which='minor',width=2)
        Iplot.axes.yaxis.set_tick_params(which='minor',width=2)
        Iplot.fillstylecount = 0
        Iplot.fillstyle      = 'none'
   
    @staticmethod
    def secondAxis(function,axis='x'):
        axis = eval('Iplot.'+axis)
        axis.twin(function)
        plt.draw()
    @staticmethod
    def hideSecondAxis(axis='x'):
        axis = eval('Iplot.'+axis)
        if axis.transform != None:
            axis.twin(None)
            plt.draw()
        
    @staticmethod
    def clearPlots(keepannotations = False,keepscale = False):
        if keepannotations: annotations = Iplot.axes.texts
        Iplot.axes.clear()
        if keepannotations: Iplot.axes.texts = annotations
        try: Iplot.axes.legend().remove()
        except AttributeError: pass
        Iplot.plots = list()
        Iplot.axes.minorticks_on()
        if keepscale:
            Iplot.xlog(Iplot.xlogon)
            Iplot.ylog(Iplot.ylogon)
        plt.draw()

    @staticmethod 
    def legend(*labels,**legend_kwrags):
        if labels:
            for plot,label in zip(Iplot.plots,labels):
                plot.set_label(label)
        legend = Iplot.axes.legend(
                        frameon=False,numpoints=1,
                        scatterpoints=1,**legend_kwrags)
        legend.set_picker(True)
        plt.draw()

    #Can send this a curve, ccf table or any list. If args contain
    #scatter makes scatter plots.
    @staticmethod
    def plotCurves(*args,**kwargs):
        if not args: return

        try: plotype = kwargs.pop('plotype')
        except KeyError:
            raise ValueError("Bad plotype! Use 'x[dxdx]y[dydy]'")
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
        try: histogram = kwargs.pop('histogram')
        except KeyError: histogram = False
        if 'marker' not in kwargs:
            if not chain:
                Iplot.cmarker = cycle(Iplot.markers)
            kwargs['marker'] = next(Iplot.cmarker)
            if Iplot.fillstylecount == len(Iplot.markers):
                Iplot.fillstyle = 'none' if Iplot.fillstyle != 'none' else 'full' 
                Iplot.fillstylecount = 0
            kwargs['fillstyle'] = Iplot.fillstyle
            Iplot.fillstylecount += 1
        kwargs['linewidth'] = 2
        if not scatter:
            kwargs['markeredgewidth'] = 2
            kwargs['markersize'] = 8

        my = mx = float("Inf")
        My = Mx = float("-Inf")
        
        Iplot.col = 0
        col_step = 1.0/len(args)
        if chain:
            col_step = 1.0/(len(Iplot.plots)+len(args))
            for child in Iplot.plots:
                child[0].set_color([Iplot.col,0,1-Iplot.col])
                for echild in child[1]+child[2]:
                    echild.set_color([Iplot.col,0,1-Iplot.col])
                Iplot.col += col_step

        try:                  
            plotter = Iplot.axes.plot
        except AttributeError: 
            Iplot.init()
            plotter = Iplot.axes.plot
        if histogram: 
            plotter = Iplot.axes.bar
        for c in args:
            iserr = False
            errs  = {'x': None, 'y': None}
            index = 0
            try:
                for letter in plotype:
                    if letter == 'd':
                        iserr = True
                        continue
                    if iserr:
                        iserr = False
                        if errs[letter] is not None: 
                              errs[letter] = np.vstack((errs[letter],c[:,index]))
                        else: errs[letter] = c[:,index]
                    else:
                        if   letter == 'x': xdata = c[:,index]
                        elif letter == 'y': ydata = c[:,index]
                        else: raise KeyError()
                    index += 1
            except KeyError:
                raise ValueError("Bad plotype! Use 'x[dxdx]y[dydy]'")
            
            color = [Iplot.col,0,1-Iplot.col]
            plot = Iplot.axes.errorbar(xdata,ydata,xerr=errs['x'],yerr=errs['y'],capsize = 0,
                            elinewidth=kwargs['linewidth'],ecolor=color,color=color,**kwargs)
            Iplot.plots.append(plot)
            if scatter: plot[0].set_linestyle("")
            xv = xdata
            yv = ydata
            if not chain and autosize:
                if min(xv) < mx or max(xv) > Mx or\
                   min(yv) < my or max(yv) > My:
                    if stepx == None: 
                        stepx = min(abs(max(xv)),abs(min(xv)))*0.5 if scatter else 0
                    if stepy == None:
                        stepy = stepy = min(abs(max(yv)),abs(min(yv)))*0.5 if scatter else 0
                    if min(xv) < mx: mx = min(xv)
                    if max(xv) > Mx: Mx = max(xv)
                    if min(yv) < my: my = min(yv)
                    if max(yv) > My: My = max(yv)
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
            xytext = Iplot.xytext 
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

        origin = Iplot.axes.transData.inverted().transform((0,0))
        for i in range(len(labels)):
            a = newlabs[i]
            cbox = a.get_window_extent()
            arrow = False
            if slide is not None:
                direct  = int((slide[0] - 0.5)*2)
                current = -direct*float("inf")
                while True:
                    overlaps = False
                    total = 0
                    for box in boxes:
                        if cbox.overlaps(box):
                            if direct*box.get_points()[slide] > direct*current:
                                overlaps = True
                                current =  box.get_points()[slide] 
                                shift   = direct*(current - cbox.get_points()[1-slide[0],slide[1]])
                                total += shift*pixel_diff
                    if not overlaps: break
                    position = array(a.get_position())
                    position[slide[1]] += shift * direct * pixel_diff
                    a.set_position(position)
                    cbox = a.get_window_extent()
                    arrow = True
            (x1,y1),(x2,y2) = Iplot.axes.transData.inverted().transform(cbox)
            #For now arrow always to bottom mid
            x = (x1+x2)/2.0
            y = y1
            if x < xstart: xstart = x - xtickshift 
            if x > xstop : xstop  = x + xtickshift 
            if y < ystart: ystart = y - ytickshift 
            if y > ystop : ystop  = y + ytickshift 
            if arrow or offset[0] or offset[1]:
                a.arrow = Iplot.axes.arrow(x,y,data[i][0]-x,
                                               data[i][1]-y,
                                               head_length=0,
                                               head_width=0,width = 0)
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

