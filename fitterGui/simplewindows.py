from Tkinter import Toplevel,Frame,Button,TOP,Label,LEFT,W,BOTH
import tkMessageBox as messagebox

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

class Help(simpleWindow):
    def __init__(self, parent):
        simpleWindow.__init__(self,parent,"",'helper',"Howto")
        root = self.parent.root
        self.root.wm_geometry("+%d+%d" %(root.winfo_rootx(),root.winfo_rooty()))
        self.frame = Frame(self.root,background = 'lightblue')
        self.frame.pack()
        self.helplabel("Modelling gui, Uria Peretz, 2016\n")
        self.helplabel("Most of it is self explanatory:")
        self.helplabel("Load         : Load data/response fits file, XMM/Chandra format for now."+
                       " Transmission can be applied to data (divides it) - two columns with num channel rows.")
        self.helplabel("Zoom         : Persistent zoom in on area of plot, does not affect fit.")
        self.helplabel("Rebin        : Rebins to channel amount.")
        self.helplabel("Ignore       : Ignore channels in fitting and plotting, or reset to all.")
        self.helplabel("Axis         : Plot counts as function of energy,wavelength or channel.")
        self.helplabel("Run          : Calculate and plot model with given parameters, and errors on parameters.")
        self.helplabel("Fit          : Go ahead and guess.")
        self.helplabel("Model        : Model selection - see syntax inside.")
        self.helplabel("Dump command : Effective way of saving current model. Dumps state to parser (bottom left) to be copied or re-used.\n\n")
        self.helplabel("That's it! On the right you can see the parameters available and which one's are frozen (and used for fit).\n","")
        self.helplabel("One more thing - the command line on the bottom left is useful for batch inputting commands " +
                        "for parameter. Syntax is '<command>,<command>,<command>' and so forth. <command> is one of " +
                        "'thaw <index:param>' 'freeze <index:param>' or '<index:param>=<value>'. This will be parsed " +
                        "command by command and stop if one of the commands fails (leaving the rest of the command line " +
                        " intact for a quick fix.)","")
        self.helplabel("Useful shortcuts (click plot area to get keyboard focus):", "")
        self.helplabel("C,W,A: Channel, wavelength, energy on axes.", "")
        self.helplabel("d,r,t: Load data/response transmission.", "")
        self.helplabel("R,i,z: Rebin/ignore/zoom", "")
        self.helplabel("m,F,s: load model/fit/save", "")
        self.helplabel("c    : Switch to commandline.", "")
        self.helplabel("H    : You're looking at it.","")

        Button( self.frame, text = 'OK', command = self.root.destroy ).pack( side = TOP )
        self.root.bind("<Key-Escape>",lambda event: self.root.destroy())

    def helplabel(self,txt,spacing = "               "):
        color ='lightblue'
        wrap  = 90
        if len(spacing):
            Label( self.frame, text = txt[:wrap], justify = LEFT, background = color, 
                   anchor = W, font = ('courier',12)).pack( side = TOP, fill = BOTH )
            rest = (spacing+txt[i:i+wrap-len(spacing)] for i in range(wrap,len(txt),wrap-len(spacing)))
        else:
            rest = (txt[i:i+wrap] for i in range(0,len(txt),wrap))
            
        for substring in rest:
            Label( self.frame, text = substring, justify = LEFT, background = color, 
                   anchor = W, font = ('courier',12)).pack( side = TOP, fill = BOTH )

class runMsg(simpleWindow):
    def __init__(self,parent,msg = "Running calculation"):
        simpleWindow.__init__(self,parent,"",'running',msg)
        Label(self.root, text = "Cancel from terminal with Ctrl-C").pack()
        self.parent.dataCanvas.update_idletasks()
    def destroy(self):
        self.root.destroy()

