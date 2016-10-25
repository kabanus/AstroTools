from Tkinter import Toplevel,Frame,Button,TOP,Label,LEFT,BOTH,Canvas,N,S,W
import tkMessageBox as messagebox
from helperfunctions import updateFrame,genScrollCanvas

class simpleWindow(object):
    def __init__(self,parent,check,field,title):
        try:
            if check.find("data")     > -1: parent.fitter.data
            if check.find("response") > -1: parent.fitter.resp
            if check.find("model") > -1 and parent.fitter.current == None: raise AttributeError()
        except AttributeError:
            messagebox.showerror('No '+check+'!','Please load '+check+' first')
            raise

        try: 
            exec('field=parent.'+field) in locals(),globals()
            field.destroy()
        except AttributeError: pass
        field = self

        self.parent = parent
        self.root = Toplevel(self.parent.root)
        self.root.transient(self.parent.root)
        self.root.wm_geometry("+%d+%d" %(parent.root.winfo_rootx()+parent.root.winfo_width()/3.0, parent.root.winfo_rooty()+parent.root.winfo_height()/2.0))
        self.root.wm_title(title)
        self.root.bind("<Key-Escape>",self.eventDestroy)
        self.root.bind("<Return>",self.parse)
        self.root.resizable(0,0)
    def parse(self,event):
        raise Exception('Not implemented')

    def eventDestroy(self,event):
        self.root.destroy()

class ScrollingCanvas(simpleWindow):
    def updateFrame(self, event):
        updateFrame(event)
        event.widget.configure(height=max(self.root.winfo_height(),self.canvasFrame.winfo_height()),
                               width=self.canvasFrame.winfo_width())

    def __init__(self,parent,field,title):
        simpleWindow.__init__(self,parent,"",field,title)
        frame = Frame(self.root,background = 'lightblue')
        frame.pack(side=TOP)
        frame.rowconfigure(0,weight=1)
        
        canvas = Canvas(frame,background='lightblue')
        self.canvasFrame,scrollbar = genScrollCanvas(self.root,frame,canvas)
        canvas.grid(row=0,column=0,sticky=N+S)
        scrollbar.grid(row=0,column=1,rowspan=2,sticky=N+S)
        canvas.bind("<Configure>", self.updateFrame) 
        root = self.parent.root
        self.root.maxsize(99999,root.winfo_height())
        self.root.wm_geometry("+%d+%d" %(root.winfo_rootx()+root.winfo_width()/7,root.winfo_rooty()))
        self.wrap = 90

        Button(frame, text = 'OK', command = self.root.destroy).grid(row=1,column=0,columnspan=2,sticky=N+S)
        self.root.bind("<Key-Escape>",lambda event: self.root.destroy())
        
class Help(ScrollingCanvas):
    def __init__(self, parent):
        ScrollingCanvas.__init__(self,parent,'helper',"Howto")
        self.helplabel("Modelling gui, Uria Peretz, 2016\n")
        self.helplabel("Most of it is self explanatory:","",16)
        self.helplabel("Load         : Load session or data/response fits file, XMM/Chandra format for now.")
        self.helplabel("Save         : Save session, plot, plot data or parameters (with errors).")
        self.helplabel("Plot         : Plot options that do not affect fit such as persistent zoom, rebin and second Z axis or data shift.")
        self.helplabel("Ignore       : Ignore channels in fitting and plotting, or reset to all.")
        self.helplabel("Axis         : Plot counts as function of energy,wavelength or channel.")
        self.helplabel("Run          : Calculate and plot model with given parameters, and errors on parameters.")
        self.helplabel("Fit          : Go ahead and guess.")
        self.helplabel("Model        : Model selection - see syntax inside.")
        self.helplabel("Dump command : Effective way of saving current model. Dumps state to parser (bottom left) to be copied or re-used.\n\n")
        self.helplabel("That's it! On the right you can see the parameters available, errors if calculated and which one's are frozen (and used for fit).\n","")
        
        self.helplabel("The parameter window","",16)
        self.helplabel("The parameter window on the left has useful information:")
        self.helplabel("1. Current model loaded")
        self.helplabel("2. index:parameter, then current value, then the error (see later), and finally" +
                           " wether it is thawed or not.","   ")
        self.helplabel(u"3. The current \u03C7\u00B2/d.o.f and ignored channels in the current axis' units.\n\n","   ")

        self.helplabel("Errors","",16)
        self.helplabel("Errors will be appear once a fit is perfomed - initial values, marked in a redish tint, "+
                       "and appearing on a raised button are the standard error, and shouldn't be quoted in anything." + 
                       u"Once a fit is performed you can press this buttons on thawed parameters to compute the \u03C7\u00B2 "+
                       "based proper errors, though this may take a while depending on the amount of thawed parameters."+
                       " Once this is done the errors will be black and the button flattened (until you change "+
                       "somthing/fit). Note if a new best fit is found this will reflect in the parameter window.\n\n","")
       
        self.helplabel("The command line","",16)
        self.helplabel("The command line on the bottom left is useful for batch inputting commands " +
                        "for parameter. Syntax is '<command>,<command>,<command>' and so forth. <command> is one of " +
                        "'thaw <index:param>' 'freeze <index:param>' or '<index:param>=<value>'. This will be parsed " +
                        "command by command and stop if one of the commands fails (leaving the rest of the command line " +
                        " intact for a quick fix.)\n\n","")
        
        self.helplabel("Useful shortcuts (middle click plot area to get keyboard focus):", "",16)
        self.helplabel("C,W,A  : Channel, wavelength, energy on axes.", "")
        self.helplabel("d,r,t,b: Load data/response/transmission/background.", "")
        self.helplabel("R,i,z  : Rebin/ignore/zoom.", "")
        self.helplabel("m,F,s  : Load model/fit/save parameters.", "")
        self.helplabel("L,S:   : Load/Save fitting session.", "")
        self.helplabel("c      : Switch to commandline.", "")
        self.helplabel("H      : You're looking at it.","")

    def rpad(self,substring):
        if substring[-1] == " ": 
            substring = substring[:-1]
            try: word = substring.rindex(" ")
            except ValueError:
                return substring
            substring = substring[:word]+" "+substring[word:]
        return substring

    def lpad(self,substring):
        if substring[0] == " ": 
            substring = substring[1:]
            try: word = substring.index(" ")
            except ValueError:
                return substring 
            substring = substring[:word]+" "+substring[word:]
        return substring

    def helplabel(self,txt,spacing = "               ",title = 12):
        color ='lightblue'
        wrap  = self.wrap
        if len(spacing):
            Label( self.canvasFrame, text = self.rpad(txt[:wrap]), justify = LEFT, background = color, 
                   anchor = W, font = ('courier',title)).pack( side = TOP, fill = BOTH )
            rest = (spacing+txt[i:i+wrap-len(spacing)] for i in range(wrap,len(txt),wrap-len(spacing)))
        else:
            rest = (txt[i:i+wrap] for i in range(0,len(txt),wrap))
           
        for substring in rest:
            substring = self.lpad(self.rpad(substring))
            Label( self.canvasFrame, text = substring, justify = LEFT, background = color, 
                   anchor = W, font = ('courier',title)).pack( side = TOP, fill = BOTH )

class errorLog(ScrollingCanvas): 
    def __init__(self, parent):
        ScrollingCanvas.__init__(self,parent,'helper',"Howto")

        try: 
            log = self.parent.fitter.errorlog
            self.root.maxsize(99999,420)
        except AttributeError: log = []
        if not log: 
            log =["No error calculation done!"]
            self.root.maxsize(99999,70)
        Label(self.canvasFrame, text = "\n".join(log), justify = LEFT, background = 'lightblue', 
              anchor = W, font =('courier',12),width=70).pack(side = TOP, fill = BOTH)

class runMsg(simpleWindow):
    def __init__(self,parent,msg = "Running calculation"):
        simpleWindow.__init__(self,parent,"",'running',msg)
        Label(self.root, text = "Cancel from terminal with Ctrl-C").pack()
        self.parent.root.update()
    def destroy(self):
        self.root.destroy()

