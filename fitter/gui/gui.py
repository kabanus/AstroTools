from tkinter import Button, Menubutton, N, S, W, E, Menu
from .entrywindows import (zoomReader, rebinReader, ignoreReader, Save, paramReader, zReader, rangeReader,
                           varReader, ionLabeler, setEps)
from .simplewindows import Help
ALL = N+S+E+W


class Gui(object):
    def __init__(self, parent, frame):
        col = 0
        self.parent = parent
        self.menuCommands()
        for title, cmd, labels in (
                ('Load', self.load, ('Data', 'Response', 'Background', 'Ancillary', 'ASCII', 'Transmission',
                                     'Remove Transmission', 'Session', 'Model')),
                ('Axes', self.setplot, ('Channel', 'Energy', 'Wavelength')),
                ('Plot', self.plot,    ('Zoom', 'No zoom', 'Rebin', 'Rest frame axis Z',
                                        'Remove rest frame axis', 'Shift data Z', 'Remove data Z', 'Model',
                                        'Divide', 'Label x', 'Label y', 'unLabel', 'Toggle Ion labels',
                                        'Toggle effective area', 'Toggle x log', 'toggle y log', 'Effective area',
                                        'Data')),
                ('Ignore', self.ignore,  ('Ignore', 'Notice', 'Reset')),
                ('Model', parent.loadModel, None),
                ('Calculate', self.calc+(parent.runFit, )+self.step, ('Model', 'Error', 'Group', 'Fit', 'Set Step')),
                ('Save', self.save, ('Params', 'Image', 'Plot', 'Session')),
                ('Help', lambda: Help(parent), None),
                ('Quit', parent._quit, None)):
            col += 1
            self.border = parent.border
            if not col % 2:
                self.border = 0
            if labels is None:
                Button(parent.gui, text=title, command=cmd, takefocus=False
                       ).grid(row=0, column=col, sticky=ALL, padx=self.border)
            else:
                self.makeMenu(col, title, labels, cmd)
        self.bindCommands()

    def menuCommands(self):
        load = self.parent.load
        fitter = self.parent.fitter
        plot = self.parent.doAndPlot

        # Can't list comprehend with lambda. Arr.
        self.step = (lambda: setEps(self.parent), )
        self.setplot = (lambda: plot(lambda: fitter.setplot(0), True),
                        lambda: plot(lambda: fitter.setplot(1), True),
                        lambda: plot(lambda: fitter.setplot(2), True))
        self.load = (lambda: plot(lambda: load(name='Data', what=lambda d, dev=None, text=None:
                                               fitter.loadData(d, text=text, device=dev))),
                     lambda: plot(lambda: load(fitter.loadResp)),
                     lambda: plot(lambda: load(fitter.loadBack)),
                     lambda: plot(lambda: load(fitter.loadAncr)),
                     lambda: plot(lambda: load(name='Data', what=lambda fname: fitter.loadData(fname, text=" "))),
                     lambda: plot(lambda: load(fitter.transmit)),
                     lambda: plot(self.parent.untransmit),
                     self.parent.loadSession, lambda: self.parent.loadSession(keyword='model'))
        self.ignore = (lambda: ignoreReader(self.parent, 'ignore'), lambda: ignoreReader(self.parent, 'notice'),
                       lambda: plot(self.parent.resetIgnore))
        self.plot = (lambda: zoomReader(self.parent),
                     lambda: plot(lambda: fitter.reset(ignore=False)),
                     lambda: rebinReader(self.parent),
                     lambda: zReader(self.parent, False),
                     lambda: plot(lambda: fitter.removeShift(False)),
                     lambda: zReader(self.parent, True),
                     lambda: plot(lambda: fitter.removeShift(True)),
                     lambda: rangeReader(self.parent),
                     lambda: plot(lambda: load(fitter.plotDiv, user=False)),
                     lambda: varReader(self.parent, 'Tex math may be entered between $$',
                                       lambda s: fitter.labelAxis('x', s)),
                     lambda: varReader(self.parent, 'Tex math may be entered between $$',
                                       lambda s: fitter.labelAxis('y', s)),
                     lambda: plot(fitter.unlabelAxis),
                     lambda: ionLabeler(self.parent, u"Enter 1, 2, 3 (\u0251 \u03B2 \u0263)"),
                     lambda: plot(lambda: fitter.toggle_area()),
                     lambda: plot(lambda: fitter.toggleLog(0)),
                     lambda: plot(lambda: fitter.toggleLog(1)),
                     lambda: plot(fitter.plotEff),
                     lambda: plot(lambda: fitter.plot()))
        self.save = (lambda: Save(self.parent, self.parent.saveParams, "Save parameters and stats", 'dat'),
                     lambda: Save(self.parent),
                     lambda: Save(
                         self.parent, lambda name, ext: fitter.plot(
                             '.'.join((name, ext)), user=False), "Save plot data", 'dat'),
                     lambda: Save(self.parent, self.parent.saveSession, "Save session", 'fsess'))
        self.calc = (lambda: plot(self.parent.calc),
                     lambda: paramReader(self.parent, self.parent.getError, 'errorer',
                                         'Find error on parameter', multiple=True),
                     lambda: rebinReader(self.parent, True))

    def bindCommands(self):
        load = self.parent.load
        fitter = self.parent.fitter
        plot = self.parent.doAndPlot
        widget = self.parent.canvas.get_tk_widget()

        self.parent.root.bind("<Return>", lambda event: widget.focus_set())
        widget.bind(
                "<C>", lambda event: plot(lambda: fitter.setplot(0), True))
        widget.bind(
                "<E>", lambda event: plot(lambda: fitter.setplot(1), True))
        widget.bind(
                "<A>", lambda event: plot(lambda: fitter.setplot(2), True))
        widget.bind("<H>", lambda event: Help(self.parent))
        widget.bind("<R>", lambda event: rebinReader(self.parent))
        widget.bind("<G>", lambda event: rebinReader(self.parent, True))
        widget.bind(
                "<T>", lambda event: plot(lambda: fitter.toggle_area()))
        widget.bind(
                "<d>", lambda event: plot(lambda: load(name='Data', what=lambda d, dev=None, text=None:
                                                       fitter.loadData(d, text=text, device=dev))))
        widget.bind(
                "<b>", lambda event: plot(lambda: load(fitter.loadBack)))
        widget.bind(
                "<r>", lambda event: plot(lambda: load(fitter.loadResp)))
        widget.bind(
                "<t>", lambda event: plot(lambda: load(fitter.transmit)))
        widget.bind(
                "<a>", lambda event: plot(lambda: load(name='Data',
                                          what=lambda fname: fitter.loadData(fname, text=" "))))
        widget.bind("<i>", lambda event: ignoreReader(self.parent, 'ignore'))
        widget.bind("<n>", lambda event: ignoreReader(self.parent, 'notice'))
        widget.bind("<z>", lambda event: zoomReader(self.parent))
        widget.bind(
                "<s>", lambda event: Save(self.parent, self.parent.saveParams, "Save parameters and stats", 'dat'))
        widget.bind(
                "<S>", lambda event: Save(self.parent, self.parent.saveSession, "Save session", 'fsess'))
        widget.bind("<L>", lambda event: self.parent.loadSession())
        widget.bind("<F>", lambda event: self.parent.runFit())
        widget.bind("<m>", lambda event: self.parent.loadModel())
        widget.bind("<2>", lambda event: event.widget.focus_set())
        widget.bind("<c>", lambda event: self.parent.commandline.entry.focus_set())

    def makeMenu(self, col, title, labels, commands):
        plotMenu = Menubutton(self.parent.gui, text=title, direction='above', relief='raised')
        plotMenu.grid(row=0, column=col, sticky=ALL, padx=self.border)
        plotMenu.menu = Menu(plotMenu, tearoff=0)
        plotMenu['menu'] = plotMenu.menu
        plotMenu.menu.configure(postcommand=lambda: plotMenu.configure(relief='sunken'))
        for label, cmd in zip(labels+('Close', ), commands+(plotMenu.menu.forget, )):
            plotMenu.menu.add_command(label=label, command=cmd)
