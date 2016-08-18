from Tkinter import Frame,N,S,E,W,Button,Label,BOTH,TOP,Canvas,Scrollbar
from commandline import commandLine
from plotInt import Iplot
ALL = N+S+E+W

def make_frames(self):
    self.main = Frame(self.root, bg = 'navyblue')
    self.main.grid( row = 0, rowspan=2, column = 0, columnspan=2,sticky =  ALL )

    cmdFrame = Frame(self.root,width = 300)
    cmdFrame.grid(row=2,column=0,sticky=ALL)
    self.commandline = commandLine(self, cmdFrame)
    cmdFrame.bind('<Configure>',self.commandline.resizeCmd)

    self.gui = Frame(self.root, bg = 'navyblue', relief = 'sunken')
    self.gui.grid( row = 2, column = 1,sticky = ALL)
    self.gui.rowconfigure(0,weight=1)
   
    Button( self.root, text='Dump command', command=self.dumpParamCmd).grid(row=2, column=2, sticky=ALL, padx=self.border)
    
    self.info_frame = Frame(self.root)
    self.info_frame.grid(row=1,column=2,sticky=ALL)
    Label(self.info_frame, textvariable = self.statistic, font = ('courier',12,'bold'),wraplength=370,bg='aliceblue',anchor=W).pack(fill=BOTH,side = TOP)
    Label(self.info_frame, textvariable = self.ignored, font = ('courier',12,'bold'),wraplength=370,bg='aliceblue',anchor=W).pack(fill=BOTH,side = TOP)

    self.data_frame = Frame(self.root)
    self.data_frame.grid( row = 0, column = 2, sticky = ALL  )
    self.data_frame.rowconfigure(0,weight=1)
    self.dataCanvas = Canvas(self.data_frame, bg='aliceblue')
    self.dataCanvas.grid(row=0,column=0,sticky=ALL)
    scrollbar = Scrollbar(self.data_frame,orient='vertical',command=self.dataCanvas.yview)
    scrollbar.grid(row=0,column=2,sticky=ALL)
    self.dataCanvas.configure(yscrollcommand=scrollbar.set)
    self.scrollbar = scrollbar

    self.canvasDataFrame = Frame( self.dataCanvas, bg = 'aliceblue' )

    self.canvasDataFrame.grid(column=0,row=0,sticky=ALL)
    self.dataCanvas.columnconfigure(0,weight=1)
    self.dataCanvas.bind("<Configure>", updateFrame)
    self.dataCanvas.create_window((0,0),window=self.canvasDataFrame,anchor='nw')
    Label(self.canvasDataFrame, textvariable = self.datatitle, font = ('courier',12,'bold underline'),wraplength=370,bg='aliceblue',anchor=N).grid(row=0,column=0,columnspan=4,sticky=N)
    self.paramLavels = {}

def updateFrame(event):
    event.widget.configure(scrollregion = event.widget.bbox('all'))

