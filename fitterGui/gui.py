from Tkinter import Button,Menubutton,N,S,W,E,Menu
from entrywindows import zoomReader, rebinReader, ignoreReader, Save, paramReader
from simplewindows import Help
ALL = N+S+E+W

class Gui(object):
    def __init__(self,parent,frame):
        col = 0
        self.parent = parent
        self.menuCommands()
        for  title,cmd, labels in (
                ('Load'  , self.load   , ('Data','Response','Transmission')),
                ('Axes'  , self.setplot, ('Channel','Energy','Wavelength')),
                ('Rebin' , lambda: rebinReader(parent), None),
                ('Zoom'  ,   self.zoom, ('Zoom','Reset')),
                ('Ignore', self.ignore, ('Ignore','Reset')),
                ('Model' , parent.loadModel, None),
                ('Fit'   , parent.runFit, None),
                ('Run'   , self.calc, ('Model','Error')),
                ('Save'  , self.save, ('Params','Image','Plot')),
                ('Help'  , lambda: Help(parent), None),
                ('Quit'  , parent._quit, None)):
            col += 1
            self.border = parent.border
            if not col%2: self.border = 0
            if labels == None:
                Button(parent.gui, text=title , command=cmd).grid(row=0,column = col, sticky=ALL, padx= self.border)
            else:
                self.makeMenu(col, title, labels, cmd)
        self.bindCommands()

    def menuCommands(self):
        #Can't list comprehend with lambda. Arr.
        self.setplot = (lambda: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(0)),
                        lambda: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(1)),
                        lambda: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(2)))
        self.load    = (lambda: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.loadData)),
                        lambda: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.loadResp)), 
                        lambda: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.transmit)))
        self.ignore  = (lambda: ignoreReader(self.parent), lambda: self.parent.doAndPlot(self.parent.resetIgnore))
        self.zoom    = (lambda: zoomReader(self.parent), lambda: self.parent.fitter.reset(ignore=False))
        self.save    = (lambda: Save(self.parent,self.parent.saveParams,"Save parameters and stats",'dat'),
                        lambda: Save(self.parent), 
                        lambda: Save(self.parent,lambda name,ext: self.parent.fitter.plot('.'.join((name,ext))),"Save plot data",'dat'))
        self.calc    = (lambda: self.parent.doAndPlot(self.parent.calc),
                        lambda: paramReader(self.parent,self.parent.getError,'errorer','Find error on parameter'))
    def bindCommands(self):
        self.parent.root.bind("<Return>",lambda event: self.parent.canvas.get_tk_widget().focus_set())
        self.parent.canvas.get_tk_widget().bind("<C>",lambda event: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(0)))
        self.parent.canvas.get_tk_widget().bind("<E>",lambda event: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(1)))
        self.parent.canvas.get_tk_widget().bind("<A>",lambda event: self.parent.doAndPlot(lambda: self.parent.fitter.setplot(2)))
        self.parent.canvas.get_tk_widget().bind("<H>",lambda event: Help(self.parent))
        self.parent.canvas.get_tk_widget().bind("<R>",lambda event: rebinReader(self.parent))
        self.parent.canvas.get_tk_widget().bind("<d>",lambda event: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.loadData)))
        self.parent.canvas.get_tk_widget().bind("<r>",lambda event: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.loadResp))) 
        self.parent.canvas.get_tk_widget().bind("<t>",lambda event: self.parent.doAndPlot(lambda: self.parent.load(self.parent.fitter.transmit)))
        self.parent.canvas.get_tk_widget().bind("<i>",lambda event: ignoreReader(self.parent))
        self.parent.canvas.get_tk_widget().bind("<z>",lambda event: zoomReader(self.parent))
        self.parent.canvas.get_tk_widget().bind("<s>",lambda event: Save(self.parent,self.parent.saveParams,"Save parameters and stats",'dat'))
        self.parent.canvas.get_tk_widget().bind("<f>",lambda event: self.parent.runFit())
        self.parent.canvas.get_tk_widget().bind("<m>",lambda event: self.parent.loadModel())
        self.parent.canvas.get_tk_widget().bind("<1>",lambda event: event.widget.focus_set())
        self.parent.canvas.get_tk_widget().bind("<c>",lambda event: self.parent.commandline.entry.focus_set())

    def makeMenu(self, col, title, labels, commands):
        plotMenu = Menubutton(self.parent.gui,text=title,direction='above', relief = 'raised')
        plotMenu.grid(row=0,column=col,sticky = ALL, padx = self.border)
        plotMenu.menu = Menu(plotMenu, tearoff = 0)
        plotMenu['menu'] = plotMenu.menu
        plotMenu.menu.configure(postcommand=lambda: plotMenu.configure(relief='sunken'))
        for label,cmd in zip(labels+('Close',),commands+(plotMenu.menu.forget,)): 
            plotMenu.menu.add_command(label = label,command = cmd)

