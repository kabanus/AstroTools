from tkinter import Button,Menubutton,N,S,W,E,Menu
from .entrywindows import (zoomReader, rebinReader, ignoreReader, 
                          Save, paramReader, zReader, rangeReader, 
                          strReader, ionLabeler)
from .simplewindows import Help
ALL = N+S+E+W

class Gui(object):
    def __init__(self,parent,frame):
        col = 0
        self.parent = parent
        self.menuCommands()
        for  title,cmd, labels in (
                ('Load'  , self.load   , ('Data','Response','Background','Ancillary',
                                          'ASCII','Transmission','Remove Transmission',
                                          'Session','Model')),
                ('Axes'  , self.setplot, ('Channel','Energy','Wavelength')),
                ('Plot'  , self.plot,    ('Zoom','No zoom','Rebin',
                                          'Rest frame axis Z','Remove rest frame axis',
                                          'Shift data Z','Remove data Z','Model','Divide',
                                          'Label x','Label y','unLabel',
                                          'Toggle Ion labels','Toggle effective area',
                                          'Toggle x log','toggle y log', 
                                          'Effective area','Data')),
                ('Ignore', self.ignore,  ('Ignore','Notice','Reset')),
                ('Model' , parent.loadModel, None),
                ('Fit'   , parent.runFit, None),
                ('Calculate', self.calc, ('Model','Error','Group')),
                ('Save'  , self.save, ('Params','Image','Plot','Session')),
                ('Help'  , lambda: Help(parent), None),
                ('Quit'  , parent._quit, None)):
            col += 1
            self.border = parent.border
            if not col%2: self.border = 0
            if labels == None:
                Button(parent.gui, text=title , command=cmd, takefocus = False).grid(row=0,column = col, sticky=ALL, padx= self.border)
            else:
                self.makeMenu(col, title, labels, cmd)
        self.bindCommands()

    def menuCommands(self):
        #Can't list comprehend with lambda. Arr.
        self.setplot = (lambda: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(0),True),
                        lambda: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(1),True),
                        lambda: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(2),True))
        self.load    = (lambda: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.loadData)),
                        lambda: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.loadResp)), 
                        lambda: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.loadBack)), 
                        lambda: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.loadAncr)), 
                        lambda: self.parent.doAndPlot(lambda: self.parent.load(
                            lambda fname: self.parent.fitter.loadData(fname," "))),
                        lambda: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.transmit)),
                        lambda: self.parent.doAndPlot(self.parent.untransmit),
                        self.parent.loadSession,lambda: self.parent.loadSession(keyword='model'))
        self.ignore  = (lambda: ignoreReader(self.parent,'ignore'), lambda: ignoreReader(self.parent,'notice'),
                        lambda: self.parent.doAndPlot(self.parent.resetIgnore))
        self.plot    = (lambda: zoomReader(self.parent), 
                        lambda: self.parent.doAndPlot(lambda: self.parent.fitter.reset(ignore=False)),
                        lambda: rebinReader(self.parent),
                        lambda: zReader(self.parent,False),
                        lambda: self.parent.doAndPlot(lambda: self.parent.fitter.removeShift(False)),
                        lambda: zReader(self.parent,True),
                        lambda: self.parent.doAndPlot(lambda: self.parent.fitter.removeShift(True)),
                        lambda: rangeReader(self.parent),
                        lambda: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.plotDiv,user = False)),
                        lambda: strReader(self.parent,'Tex math may be entered between $$',
                                lambda s: self.parent.fitter.labelAxis('x',s)),
                        lambda: strReader(self.parent,'Tex math may be entered between $$',
                                lambda s: self.parent.fitter.labelAxis('y',s)),
                        lambda: self.parent.doAndPlot(self.parent.fitter.unlabelAxis),
                        lambda: ionLabeler(self.parent,"Enter 1,2,3 (\u0251 \u03B2 \u0263)"),
                        lambda: self.parent.doAndPlot(lambda: self.parent.fitter.toggle_area()),
                        lambda: self.parent.doAndPlot(lambda: self.parent.fitter.toggleLog(0)),
                        lambda: self.parent.doAndPlot(lambda: self.parent.fitter.toggleLog(1)),
                        lambda: self.parent.doAndPlot(self.parent.fitter.plotEff),
                        lambda: self.parent.doAndPlot(lambda: self.parent.fitter.plot()))
        self.save    = (lambda: Save(self.parent,self.parent.saveParams,"Save parameters and stats",'dat'),
                        lambda: Save(self.parent), 
                        lambda: Save(self.parent,lambda name,ext: self.parent.fitter.plot('.'.join((name,ext)),user = False),"Save plot data",'dat'),
                        lambda: Save(self.parent,self.parent.saveSession,"Save session",'fsess'))
        self.calc    = (lambda: self.parent.doAndPlot(self.parent.calc),
                        lambda: paramReader(self.parent,self.parent.getError,'errorer','Find error on parameter',multiple = True),
                        lambda: rebinReader(self.parent,True))
    def bindCommands(self):
        self.parent.root.bind("<Return>",lambda event: self.parent.canvas.get_tk_widget().focus_set())
        self.parent.canvas.get_tk_widget().bind("<C>",lambda event: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(0),True))
        self.parent.canvas.get_tk_widget().bind("<E>",lambda event: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(1),True))
        self.parent.canvas.get_tk_widget().bind("<A>",lambda event: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(2),True))
        self.parent.canvas.get_tk_widget().bind("<H>",lambda event: Help(self.parent))
        self.parent.canvas.get_tk_widget().bind("<R>",lambda event: rebinReader(self.parent))
        self.parent.canvas.get_tk_widget().bind("<G>",lambda event: rebinReader(self.parent,True))
        self.parent.canvas.get_tk_widget().bind("<T>",lambda event: self.parent.doAndPlot(lambda: self.parent.fitter.toggle_area()))
        self.parent.canvas.get_tk_widget().bind("<d>",lambda event: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.loadData)))
        self.parent.canvas.get_tk_widget().bind("<b>",lambda event: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.loadBack)))
        self.parent.canvas.get_tk_widget().bind("<r>",lambda event: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.loadResp))) 
        self.parent.canvas.get_tk_widget().bind("<t>",lambda event: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.transmit)))
        self.parent.canvas.get_tk_widget().bind("<i>",lambda event: ignoreReader(self.parent,'ignore'))
        self.parent.canvas.get_tk_widget().bind("<n>",lambda event: ignoreReader(self.parent,'notice'))
        self.parent.canvas.get_tk_widget().bind("<z>",lambda event: zoomReader(self.parent))
        self.parent.canvas.get_tk_widget().bind("<s>",lambda event: Save(self.parent,self.parent.saveParams,"Save parameters and stats",'dat'))
        self.parent.canvas.get_tk_widget().bind("<S>",lambda event: Save(self.parent,self.parent.saveSession,"Save session",'fsess'))
        self.parent.canvas.get_tk_widget().bind("<L>",lambda event: self.parent.loadSession())
        self.parent.canvas.get_tk_widget().bind("<F>",lambda event: self.parent.runFit())
        self.parent.canvas.get_tk_widget().bind("<m>",lambda event: self.parent.loadModel())
        self.parent.canvas.get_tk_widget().bind("<2>",lambda event: event.widget.focus_set())
        self.parent.canvas.get_tk_widget().bind("<c>",lambda event: self.parent.commandline.entry.focus_set())

    def makeMenu(self, col, title, labels, commands):
        plotMenu = Menubutton(self.parent.gui,text=title,direction='above', relief = 'raised')
        plotMenu.grid(row=0,column=col,sticky = ALL, padx = self.border)
        plotMenu.menu = Menu(plotMenu, tearoff = 0)
        plotMenu['menu'] = plotMenu.menu
        plotMenu.menu.configure(postcommand=lambda: plotMenu.configure(relief='sunken'))
        for label,cmd in zip(labels+('Close',),commands+(plotMenu.menu.forget,)): 
            plotMenu.menu.add_command(label = label,command = cmd)

