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
        self.root.wm_geometry("+%d+%d" %(root.winfo_rootx()+root.winfo_width()/3.0,root.winfo_rooty()))
        self.frame = Frame(self.root,background = 'lightblue')
        self.frame.pack()
        self.helplabel( "Modelling gui, Uria Peretz, 2016\n")
        self.helplabel( "Most of it is self explanatory:")
        self.helplabel( "Data/Response: Load fits file, XMM/Chandra format for now.")
        self.helplabel( "Zoom         : Quick zoom in on area of plot.")
        self.helplabel( "Ignore/Reset : Ignore channels in fitting and plotting, or reset to all.")
        self.helplabel( "Plot         : Plot counts as function of energy,wavelength or channel.")
        self.helplabel( "Run          : Calculate and plot model with given parameters.")
        self.helplabel( "Fit          : Go ahead and guess.")
        self.helplabel( "Model        : Model selection - see syntax inside.\n\n")
        self.helplabel( "That's it! On the right you can see the parameters available and which one's are frozen (and used for fit).\n")
        self.helplabel( "One more thing - the command line on the bottom left is useful for batch inputting commands for parameter. Syntax is '<command>,<command>,<command>' and so forth. <command> is one of 'thaw <index:param>' 'freeze <index:param>' or '<index:param>=<value>'. This will be parsed command by command and stop if one of the commands fails (leaving the rest of the command line intact for a quick fix.)")

        Button( self.frame, text = 'OK', command = self.root.destroy ).pack( side = TOP )
        self.root.bind("<Key-Escape>",lambda event: self.root.destroy())

    def helplabel(self,txt):
        color ='lightblue'
        Label( self.frame, text = txt, justify = LEFT, background = color, wraplength = 520, anchor = W, font = ('courier',12)).pack( side = TOP, fill = BOTH )

class runMsg(simpleWindow):
    def __init__(self,parent,msg = "Running calculation"):
        simpleWindow.__init__(self,parent,"",'running',msg)
        Label(self.root, text = "Cancel from terminal with Ctrl-C").pack()
        self.parent.dataCanvas.update_idletasks()
    def destroy(self):
        self.root.destroy()

