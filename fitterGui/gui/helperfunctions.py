from tkinter import Frame,N,S,E,W,Button,Label,BOTH,TOP,Canvas,Scrollbar,Menubutton,Menu
from tkinter.scrolledtext import ScrolledText
from tkinter.filedialog import askopenfilename
from os import path
ALL = N+S+E+W

def make_frames(self):
    #Prevent circular imports
    from .commandline import commandLine
    from .debugConsole import DebugConsole
    self.main = Frame(self.root, bg = 'navyblue')
    self.main.grid( row = 0, rowspan=2, column = 0, columnspan=2,sticky =  ALL )
    bgcol = 'aliceblue'

    cmdFrame = Frame(self.root,width = 300)
    cmdFrame.grid(row=2,column=0,sticky=ALL)
    self.commandline = commandLine(self, cmdFrame)
    cmdFrame.bind('<Configure>',self.commandline.resizeCmd)
    self.cmdFrame = cmdFrame

    self.gui = Frame(self.root, bg = 'navyblue', relief = 'sunken')
    self.gui.grid( row = 2, column = 1,sticky = ALL)
    self.gui.rowconfigure(0,weight=1)
  
    self.dumpFrame = Frame(self.root,bg=bgcol,bd=2)
    self.dumpFrame.grid(row=2, column=2, sticky=ALL)
    self.dump = Button(self.dumpFrame, text='Dump command', command=self.dumpParamCmd)
    self.dump.pack(expand=True,fill=BOTH)
    
    self.info_frame = Frame(self.root)
    self.info_frame.grid(row=1,column=2,sticky=ALL)
    self.info_frame.columnconfigure(1,weight=1)
    info_font = ('courier',12,'bold')
    info_wrap = 370
    #Statistic choice
    mb=Menubutton(self.info_frame, text="Statistic:", font=info_font, direction='above', bg=bgcol,anchor=W,relief='raised')
    mb.grid(column=0,row=0,sticky=ALL)
    m = Menu(mb,tearoff = 0)
    mb['menu'] = m
    m.add_command(label = '\u03C7\u00B2',command = lambda: self.setStat('chisq'))
    m.add_command(label = 'C stat',command = lambda: self.setStat('C'))
    
    Label( self.info_frame, textvariable=self.fstatistic , font=info_font, wraplength=info_wrap, bg=bgcol,anchor=W
        ).grid(column=1,row=0,sticky=ALL)
    Label( self.info_frame, textvariable=self.statistic  , font=info_font, wraplength=info_wrap, bg=bgcol,anchor=W
        ).grid(column=0,row=1,columnspan=2,sticky=ALL)
    Label( self.info_frame, textvariable=self.ignored    , font=info_font, wraplength=info_wrap, bg=bgcol,anchor=W
        ).grid(column=0,row=2,columnspan=2,sticky=ALL)
    Label( self.info_frame, textvariable=self.grouped    , font=info_font, wraplength=info_wrap, bg=bgcol,anchor=W
        ).grid(column=0,row=3,columnspan=2,sticky=ALL) 

    self.data_frame = Frame(self.root)
    self.data_frame.grid( row = 0, column = 2, sticky = ALL  )
    self.data_frame.rowconfigure(0,weight=1)
    self.dataCanvas = Canvas(self.data_frame, bg=bgcol)
    self.dataCanvas.grid(row=0,column=0,sticky=ALL)
    self.dataCanvas.columnconfigure(0,weight=1)
   
    self.canvasDataFrame,self.scrollbar = genScrollCanvas(self.root,self.data_frame,self.dataCanvas)
    self.scrollbar.grid(row=0,column=2,sticky=ALL) 
    self.canvasDataFrame.configure(bg = bgcol)
    
    Label(self.canvasDataFrame, textvariable = self.datatitle, font = ('courier',12,'bold underline'),wraplength=370,bg=bgcol,anchor=N).grid(row=0,column=0,columnspan=4,sticky=N)
    self.paramLavels = {}

    if self.debug:
        self.debugger = DebugConsole(self.root,
                                     "Debug console. Access app through App.",
                                     {'App':self},self._quit)

def genScrollCanvas(root,root_frame, canvas):
    scrollbar = Scrollbar(root_frame,command = canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.bind("<Configure>",updateFrame)
    canvas_frame = Frame(canvas)
    canvas_frame.pack(fill=BOTH,expand=True,side="left")
    #Catch both windows and linux
    root.bind("<Button-4>",onscroll(canvas,-1).do)
    root.bind("<Button-5>",onscroll(canvas,1).do)
    root.bind("<MouseWheel>",onscroll(canvas,0).do)
    canvas.create_window((0,0),window=canvas_frame,anchor='nw')
    return canvas_frame,scrollbar

class onscroll(object):
    def __init__(self,canvas,direction):
        self.canvas = canvas
        self.direct = direction
    def do(self, event):
        direct = self.direct
        if not direct:
            direct = -1*event.delta/120
        self.canvas.yview_scroll(direct,"units")

def updateFrame(event):
    event.widget.configure(scrollregion = event.widget.bbox('all'))
    
def getfile(*defaults):
    filetypes = list()
    defaultextension = '.*'
    for filetype in defaults:
        if defaultextension == '.*': defaultextension = filetype
        filetypes.append((filetype.capitalize()+' file','*.'+filetype))
    filetypes.append(('All files','*.*'))
    thefile = askopenfilename(defaultextension = defaultextension,
                              filetypes = filetypes)
    if not thefile: return None 
    return path.relpath(thefile)
