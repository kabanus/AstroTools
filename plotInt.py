# Make an even simpler plotting interface
# from matplotlib.markers import MarkerStyle as MS
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, FuncFormatter, NullFormatter
from itertools import cycle
from numpy import array
import shutil as sh
import numpy as np
import pandas as pd
import warnings
import logging
import matplotlib
warnings.filterwarnings('ignore')
logging.getLogger('matplotlib.legend').disabled = True

usetex = sh.which('latex') is not None


def setTexFonts(font_size=44):
    if usetex:
        matplotlib.rc('text', usetex=True)
        matplotlib.rcParams['text.latex.preamble'] = [r"\usepackage{amsmath} \boldmath"]
        matplotlib.rcParams['axes.labelweight'] = 'bold'
        matplotlib.rcParams['axes.labelsize'] = font_size
        matplotlib.rcParams['axes.titlesize'] = font_size
        matplotlib.rcParams['legend.fontsize'] = font_size/1.7
        matplotlib.rcParams['legend.title_fontsize'] = font_size
        matplotlib.rcParams['font.size'] = font_size
        matplotlib.rcParams['font.weight'] = 'bold'


def pd_plot(*dfs, axes=None, **plotkwargs):
    x = plotkwargs.pop('x')
    y = plotkwargs.pop('y')
    xerr = plotkwargs.pop('xerr', None)
    yerr = plotkwargs.pop('yerr', None)
    if axes is not None:
        try:
            axes = axes.flatten()
        except AttributeError:
            axes = [axes]
    else:
        axes = Iplot.axes
    for df, ax in zip(dfs, axes):
        Iplot.axes = ax
        try:
            df.plot(x=x, xerr=xerr, y=y, yerr=yerr, ax=Iplot.axes, elinewidth=4, lw=4, **plotkwargs)
        except KeyError:
            df.plot(x=df.columns[x], xerr=xerr, y=df.columns[y], yerr=yerr, ax=Iplot.axes, elinewidth=4,
                    lw=4, **plotkwargs)


class Igrid:
    def __init__(self, nrows, ncols, **subplot_kwargs):
        subplot_kwargs['gridspec_kw'] = {'hspace': 0.0, 'wspace': 0.05}
        self.fig, self.axes = plt.subplots(nrows=nrows, ncols=ncols, **subplot_kwargs)
        self.plots = array(
            pd.DataFrame(self.axes).applymap(PlotMaker)).reshape(self.axes.shape)
        self.default_font = 44
        self.reset()
        self.fig.set_size_inches(18.5, 10.5)

    def reset(self, axes=None):
        if axes is None:
            axes = self.axes
        rows = self.axes if len(axes.shape) > 1 else [axes]
        for row, raxes in enumerate(rows):
            for col, ax in enumerate(raxes):
                if col:
                    ax.tick_params(axis='y', labelleft='off')
                if row < len(self.axes.shape)-1:
                    ax.tick_params(axis='x', labelbottom='off')

    @staticmethod
    def _twin(plot, which, func=None):
        plot.secondAxis(func, which, override=True)
        plot.axes.tick_params(which='both', direction='in', top=True)

    def __iter__(self):
        return iter(self.plots.flatten())

    def twiny(self, func=None):
        for plot in self.plots:
            Igrid._twin(plot, 'y', func)

    def twinx(self, func=None):
        for plot in self.plots:
            Igrid._twin(plot, 'x', func)

    def show(self):
        self.fig.show()

    def remove_labels(self):
        for plot in self:
            plot.axes.set_xlabel('')
            plot.axes.set_ylabel('')

    def ylabel(self, label, clear=True):
        if clear:
            self.remove_labels()
        try:
            self._ylabel.remove()
        except AttributeError:
            pass
        self._ylabel = self.fig.text(0.04, 0.5, label, va='center', rotation='vertical', fontsize=self.default_font)

    def xlabel(self, label, clear=True):
        if clear:
            self.remove_labels()
        try:
            self._xlabel.remove()
        except AttributeError:
            pass
        self._xlabel = self.fig.text(0.5, 0.01, label, ha='center', fontsize=self.default_font)

    def xresize(self, min=None, max=None):
        for plot in self:
            plot.x.resize(min, max)

    def yresize(self, min=None, max=None):
        for plot in self:
            plot.y.resize(min, max)

    def __getitem__(self, i):
        return self.plots[i]

    def export(self, name, ptype=None):
        if ptype is None:
            name = name.split('.')
            ptype = name[-1]
            name = '.'.join(name[:-1])
        plt.savefig(name + '.' + ptype, bbox_inches='tight')


SF = ScalarFormatter()
plt.ion()


class PlotMaker:
    # markers = sorted((marker for marker in MS.markers.keys()
    # if marker not in (None, 'None', " ", "", ', ')+tuple(range(8))))
    markers = ('o', 's', '^', 'v')
    cmarker = cycle(markers)
    xytext = (-6, 20)

    class noSuchAxis(Exception):
        pass

    class axis(object):
        def __init__(self, axis, axes):
            if axis == 'x':
                self.ind = 0
            elif axis == 'y':
                self.ind = 1
            else:
                raise PlotMaker.noSuchAxis(axis)
            self.axes = axes
            self.axis = axis
            self.sizer = getattr(self.axes, 'set_'+axis+'lim')
            self.labelr = getattr(self.axes, 'set_'+axis+'label')
            self.sizer2 = None
            self.labelr2 = None
            self.transform = None

        def twin(self, function, formatter=SF.format_data_short, override=False):
            op = 'y'
            if override or self.sizer2 is None:
                if self.ind:
                    op = 'x'
                self.second = getattr(self.axes, 'twin'+op)()
                self.sizer2 = getattr(self.second, 'set_'+self.axis+'lim')
                plt.gcf().delaxes(self.axes)
                plt.gcf().add_axes(self.axes)
            self.transform = function
            if function is not None:
                getattr(self.second, self.axis+'axis').set_major_formatter(
                        FuncFormatter(lambda c, p, t=self.transform, f=formatter: f(t(c))))
            else:
                getattr(self.second, self.axis+'axis').set_major_formatter(NullFormatter())
                self.second.minorticks_on()
            self.resize()

        def scale(self, stype):
            getattr(self.axes, 'set_'+self.axis+'scale')(stype)
            if self.sizer2 is not None:
                getattr(self.second, 'set_'+self.axis+'scale')(stype)

        def resize(self, start=None, stop=None, minimal=None, maximal=None):
            if stop is None:
                stop = self.axes.axis()[self.ind*2+1]
            if start is None:
                start = self.axes.axis()[self.ind*2]
            if start >= stop:
                start, stop = stop, start
                # raise Exception("Bad range! stop must be greater then start: "+str(start)+">="+str(stop))
            self.sizer(start, stop)
            if self.sizer2 is not None:
                self.sizer2(start, stop)
            start = stop = None
            bot, top = self.get_bounds()
            if minimal is not None and minimal > bot:
                start = minimal
            if maximal is not None and maximal < top:
                stop = maximal
            if stop is not None or start is not None:
                self.resize(start, stop)
            else:
                plt.draw()

        def get_bounds(self):
            return self.axes.axis()[self.ind*2:self.ind*2+2]

        def label(self, title):
            if usetex:
                self.labelr(r'\textbf{'+title+'}')
            else:
                self.labelr(title)
            plt.draw()

    def __init__(self, axes=None):
        if axes is not None:
            self.axes = axes
            self.init(False)

    def _log(self, axis, on):
        if self.plots and axis.get_bounds()[0] <= 0:
            index = 0 if axis is self.x else 1
            try:
                minimum = min([min(p[0].get_xydata()[:, index]) for p in self.plots])
            except AttributeError:
                minimum = 1
            if minimum <= 0:
                axis.resize(start=1e-10)
        if on:
            axis.scale('log')
        else:
            axis.scale('linear')
        plt.draw()

    xlogon = False

    def xlog(self, on=None):
        if on is None:
            on = not self.xlogon
        self.xlogon = on
        self._log(self.x, on)
    ylogon = False

    def ylog(self, on=None):
        if on is None:
            on = not self.ylogon
        self.ylogon = on
        self._log(self.y, on)

    def log(self, on=None):
        self.xlog(on)
        self.ylog(on)

    pickstate = None

    def onclick(self, event):
        print('CLICK')
        if event.mouseevent.button == 3:
            try:
                event.artist.arr.remove()
            except (AttributeError, ValueError):
                pass
            try:
                event.artist.remove()
            except (ValueError):
                pass
        else:
            self.pickstate = event.artist
        print(self.pickstate)

    def move(self, event):
        if self.pickstate is not None:
            xy = [event.xdata, event.ydata]
            if xy == [None, None]:
                return
            try:
                b = self.pickstate.get_window_extent()
                self.pickstate.set_position(((b.x0-b.x1)/2, (b.y0-b.y1)/4))
                self.pickstate.xy = xy
                try:
                    (x0, y0), (x1, y1) = self.axes.transData.inverted().transform(b)
                    a = xy[:]
                    a[1] += (y0-y1)/2
                    origArrow = self.pickstate.arr.get_xy()
                    origArrow[3:5] = a
                except AttributeError:
                    self.pickstate.arr = self.axes.arrow(
                        a[0], a[1], 0.001, 0.001, head_length=0, head_width=0, linewidth=2, overhang=100, color='black')
            except AttributeError:
                xy = self.axes.transAxes.inverted().transform((event.x, event.y))
                self.axes.get_legend()._set_loc(10)  # This means center
                self.axes.get_legend().set_bbox_to_anchor((xy))

                plt.draw()

    def release(self, event):
            try:
                arrow = self.pickstate.arr
                arrxy = arrow.get_xy()
                x0, y0 = arrxy[0]
                x1, y1 = arrxy[3]
                if (x1-x0)**2+(y1-y0)**2 < 0.001:
                    self.pickstate.arr.remove()
                    delattr(self.pickstate, 'arr')
            except AttributeError:
                pass
            self.pickstate = None

    def init(self, get_current=True, no_picker=False, font_size=44):
        setTexFonts(font_size=font_size)
        if get_current:
            self.axes = plt.gca()
        self.axes.minorticks_on()
        self.axes.tick_params(which='both', direction='in')
        self.axes.tick_params(axis='both', top=True, right=True, which='both')
        self.x = self.axis('x', self.axes)
        self.y = self.axis('y', self.axes)
        self.plots = list()
        self.clearPlots()
        if no_picker:
            plt.gcf().canvas.mpl_connect('pick_event', self.onclick)
            plt.gcf().canvas.mpl_connect('motion_notify_event', self.move)
            plt.gcf().canvas.mpl_connect('button_release_event', self.release)
        for axis in ['top', 'bottom', 'left', 'right']:
            self.axes.spines[axis].set_linewidth(4)
        self.axes.xaxis.set_tick_params(which='major', top=True, bottom=True, right=True, left=True, width=4, length=10)
        self.axes.yaxis.set_tick_params(which='major', top=True, bottom=True, right=True, left=True, width=4, length=10)
        self.axes.xaxis.set_tick_params(which='minor', top=True, bottom=True, right=True, left=True, width=4, length=5)
        self.axes.yaxis.set_tick_params(which='minor', top=True, bottom=True, right=True, left=True, width=4, length=5)
        self.fillstylecount = 0
        self.fillstyle = 'none'
        self.xlog(False)
        self.ylog(False)

    def secondAxis(self, function, axis='x', override=False):
        axis = self.__dict__[axis]
        axis.twin(function, override=override)
        cur, x, y = self.axes, self.x, self.y
        self.axes = axis.second
        self.init(False)
        self.axes, self.x, self.y = cur, x, y
        plt.draw()

    def hideSecondAxis(self, axis='x'):
        axis = getattr(self, axis)
        if axis.transform is not None:
            axis.twin(None)
            plt.draw()

    def clearPlots(self, keepannotations=False, keepscale=False):
        if keepannotations:
            annotations = self.axes.texts
        self.axes.clear()
        if keepannotations:
            self.axes.texts = annotations
        try:
            self.axes.legend().remove()
        except AttributeError:
            pass
        self.plots = list()
        self.axes.minorticks_on()
        if keepscale:
            self.xlog(self.xlogon)
            self.ylog(self.ylogon)
        plt.draw()

    def legend(self, *labels, **legend_kwrags):
        legend = self.axes.get_legend()
        if legend is None:
            if labels:
                for plot, label in zip(self.plots, labels):
                    plot.set_label(label)
            legend = self.axes.legend(
                            frameon=False, numpoints=1,
                            scatterpoints=1, **legend_kwrags)
        legend.set_draggable(True)
        legend.set_picker(True)
        plt.draw()

    # Can send this a curve, ccf table or any list. If args contain
    # scatter makes scatter plots.
    def plotCurves(self, *args, **kwargs):
        if 'help' in kwargs:
            print('Options not passed to matplotlib: plotype, scatter, chain, histogram, marker, onecolor')
            args = None
        if not args:
            return

        try:
            plotype = kwargs.pop('plotype')
        except KeyError:
            raise ValueError("Bad plotype! Use 'x[dxdx]y[dydy]'")
        if 'fillstylecount' not in self.__dict__:
            print("-I- Please run object.init() first.")
            return

        scatter = kwargs.pop('scatter', False)
        chain = kwargs.pop('chain', False)
        histogram = kwargs.pop('histogram', False)
        onecolor = kwargs.pop('onecolor', None)
        if 'marker' not in kwargs:
            if not chain:
                self.cmarker = cycle(self.markers)
            kwargs['marker'] = next(self.cmarker)
            if self.fillstylecount == len(self.markers):
                self.fillstyle = 'none' if self.fillstyle != 'none' else 'full'
                self.fillstylecount = 0
            kwargs['fillstyle'] = self.fillstyle
            self.fillstylecount += 1
        kwargs['linewidth'] = kwargs.pop('lw', 4)
        kwargs['linewidth'] = kwargs.pop('linewidth', 4)
        if not scatter and not histogram:
            kwargs['markeredgewidth'] = kwargs.pop('markeredgewidth', 1)
            kwargs['markersize'] = kwargs.pop('markersize', 1)

        plots = []
        for c in args:
            errs = {'x': [], 'y': []}
            data = {'x': [], 'y': []}
            index = 0
            lindex = 0
            try:
                while index < c.shape[1]:
                    for axis in ('x', 'y')[(index > 0):]:
                        letter = plotype[lindex]
                        if letter != axis:
                            raise KeyError()
                        data[axis].append(c[:, index])
                        index += 1
                        lindex += 1

                        err = None
                        while lindex < len(plotype) and plotype[lindex] == 'd':
                            letter = plotype[lindex+1]
                            if letter != axis:
                                raise KeyError()
                            if err is not None:
                                err = np.vstack((errs[letter], c[:, index]))
                            else:
                                err = c[:, index]
                            index += 1
                            lindex += 2
                        errs[axis].append(err)
                    if lindex < len(plotype):
                        raise IndexError()
                    lindex = plotype.index('y')
                if not data['y']:
                    raise KeyError()
                if histogram and (errs['x'] or errs['y']):
                    raise ValueError('Cannot use histogram with error bars!')
            except (KeyError, IndexError):
                raise ValueError("Bad plotype! Use 'x[dxdx]y[dydy]'")

            xdata, xerr = data['x'][0], errs['x'][0]
            for ydata, yerr in zip(data['y'], errs['y']):
                if not histogram:
                    plot = self.axes.errorbar(xdata, ydata, xerr=xerr, yerr=yerr,
                                              color=onecolor, ecolor=onecolor,
                                              capsize=0, elinewidth=kwargs['linewidth'],
                                              rasterized=True, **kwargs)
                else:
                    kwargs.pop('marker')
                    kwargs.pop('fillstyle')
                    kwargs['fill'] = False
                    plot = self.axes.bar(xdata, ydata, **kwargs)
                plots.append(plot)
                if scatter:
                    plot[0].set_linestyle("")

        self.plots.extend(plots)
        if onecolor is None:
            col = 0
            if chain:
                plots = self.plots
            col_step = 1.0/len(plots)
            for child in plots:
                child[0].set_color([col, 0, 1-col])
                for echild in child[1]+child[2]:
                    echild.set_color([col, 0, 1-col])
                col += col_step
        plt.draw()

    def title(self, title, **kwargs):
        self.axes.set_title(title, **kwargs)
        plt.draw()

    def annotate(self, labels, data, **kwargs):
        # slide should be relevant edge of bbox - e.g. (0, 0) for left, (0, 1) for bottom...
        slide = kwargs.pop("slide", None)
        offset = kwargs.pop("offset", (0, 0))
        try:
            xytexts = kwargs.pop("xytexts")
            xytext = xytexts
        except KeyError:
            xytext = self.xytext
            xytexts = None
        pixel_diff = 1

        boxes = []
        for annotation in self.axes.texts:
            boxes.append(annotation.get_window_extent())

        newlabs = []
        for i in range(len(labels)):
            try:
                len(xytexts[i])
                xytext = xytexts[i]
            except TypeError:
                pass

            try:
                loc = [d+o for d, o in zip(data[i], offset)]
                if usetex:
                    label = r'\textbf{'+labels[i]+'}'
                else:
                    label = labels[i]
                a = self.axes.annotate(label, xy=loc, textcoords='offset pixels',
                                       xytext=xytext, picker=True, **kwargs)
            except AttributeError:
                self.init()
                a = self.axes.annotate(labels[i], xy=data[i], textcoords='offset pixels',
                                       xytext=xytext, picker=True, **kwargs)
            newlabs.append(a)
        plt.gcf().canvas.draw()
        xstart, xstop = self.x.get_bounds()
        ystart, ystop = self.y.get_bounds()
        xtickshift = (self.axes.get_xticks()[1]-self.axes.get_xticks()[0])
        ytickshift = (self.axes.get_yticks()[1]-self.axes.get_yticks()[0])

        for i in range(len(labels)):
            a = newlabs[i]
            cbox = a.get_window_extent()
            arrow = False
            if slide is not None:
                direct = int((slide[0] - 0.5)*2)
                current = -direct*float("inf")
                while True:
                    overlaps = False
                    total = 0
                    for box in boxes:
                        if cbox.overlaps(box):
                            if direct*box.get_points()[slide] > direct*current:
                                overlaps = True
                                current = box.get_points()[slide]
                                shift = direct*(current - cbox.get_points()[1-slide[0], slide[1]])
                                total += shift*pixel_diff
                    if not overlaps:
                        break
                    position = array(a.get_position())
                    position[slide[1]] += shift * direct * pixel_diff
                    a.set_position(position)
                    cbox = a.get_window_extent()
                    arrow = True
            (x1, y1), (x2, y2) = self.axes.transData.inverted().transform(cbox)
            # For now arrow always to bottom mid
            x = (x1+x2)/2.0
            y = y1
            if x < xstart:
                xstart = x - xtickshift
            if x > xstop:
                xstop = x + xtickshift
            if y < ystart:
                ystart = y - ytickshift
            if y > ystop:
                ystop = y + ytickshift
            if arrow or offset[0] or offset[1]:
                a.arr = self.axes.arrow(x, y, data[i][0]-x, data[i][1]-y,
                                        head_length=0, head_width=0, linewidth=2, overhang=100, color='black')
            boxes.append(cbox)
        plt.draw()
        return (xstart, xstop, ystart, ystop)

    def quiet(self, ):
        plt.ioff()

    def loud(self, ):
        plt.ion()

    def export(self, name, ptype=None):
        if ptype is None:
            name = name.split('.')
            ptype = name[-1]
            name = '.'.join(name[:-1])
        plt.savefig(name + '.' + ptype, bbox_inches='tight')

    def help(self, ):
        print("-I- Helper class for plotting. You can:")
        print("-I- clearPlots      = Clear plot window.")
        print("-I- plotCurves      = Accepts any number of curves and plots them.")
        print("-I-                   Can be used with *Iccf.tables and Iccf.peaks.")
        print("-I-                   'scatter' keyword will make all remaining plots scatter.")


Iplot = PlotMaker()
