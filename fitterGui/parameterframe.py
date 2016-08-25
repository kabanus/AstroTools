from Tkinter import Label, Entry, LEFT, W, N, S, E, IntVar, Checkbutton,StringVar,Button,END
from entrywindows import paramReader
import tkMessageBox as messagebox
ALL = W+N+S+E

class parameterFrame(object):
    def __init__(self,parent,frame):
        self.parent = parent
        self.frame  = frame
        frame.columnconfigure(2,weight=1)
        self.parent.root.bind('<Control-f>',lambda event: paramReader(self.parent,self.find,"finder","Find parameter"))

    def find(self,index,param):
        try: place = sorted(self.parent.paramLabels).index((index,param))
        except ValueError:
            messagebox.showerror("No such parameter","Please make sure "+str(index)+":"+param+" exists")
            return
        placement = place / (len(self.parent.paramLabels)+1.0)
        top,  bot = self.parent.scrollbar.get()
        offset       = (bot-top)/2.0

        top = placement - offset
        bot = placement - offset
        placement = placement - offset
        if top < 0: 
            top = 0
            bot = offset*2
            placement = 0
        elif bot > 1:
            top = 1-offset*2
            bot = 1
            placement = 1
        self.parent.scrollbar.set(top,bot)
        self.parent.dataCanvas.yview_moveto(placement)
        self.parent.paramLabels[(index,param)][1].focus_set()

    def entryIn(self,event):
        self.lastEntry = event.widget.get()
        event.widget.configure(background='white')

    def entryColor(self,event):
        event.widget.configure(background='white')

    def entryOut(self,event,index,param):
        current = event.widget.get()
        if  current == "":
            event.widget.insert(0,self.lastEntry)
        elif current != self.lastEntry:
            try:
                self.parent.fitter.current.setp({(index,param):float(current)})
                self.resetErrors()
            except ValueError: 
                event.widget.delete(0,END)
                event.widget.insert(0,self.lastEntry)
        event.widget.configure(background='aliceblue')
        if event.keysym == "Return": 
            self.parent.calc()

    def resetErrors(self):
        for _,_,l3,_ in self.parent.paramLabels.values():
            l3.configure(relief='raised',state='normal')
        self.parent.ranfit = False

    def relabel(self):
        for iparam,value in self.parent.fitter.current.getParams():
            entry = self.parent.paramLabels[iparam][1]
            entry.delete(0,END)
            entry.insert(0,str(value))

    def draw(self):
        while self.parent.paramLabels:
            _,labels = self.parent.paramLabels.popitem()
            for label in labels: 
                label.destroy()

        count = 1
        if self.parent.fitter.current == None: return
        self.parent.thawedDict = {}
        for (index,param),value in sorted(self.parent.fitter.current.getParams()):
            l1 = Label(self.frame, text=str(index)+":"+param,width=6,justify = LEFT, font = ('courier',12),bg='aliceblue',anchor=N+W)
            l1.grid(sticky=ALL,row=count, column=0),
            l2 = Entry(self.frame,justify = LEFT, font = ('courier',12),bg='aliceblue',width=13)
            l2.insert(0,str(value))
            l2.grid(sticky=ALL,row=count, column=1)
            exec('l2.bind("<FocusOut>",lambda event: self.entryOut(event,'+str(index)+',"'+param+'"))') in locals(), globals()
            l2.bind("<FocusIn>",self.entryIn)
            l2.bind("<Key>",self.entryColor)
            exec('l2.bind("<Return>",lambda event: self.entryOut(event,'+str(index)+',"'+param+'"))') in locals(), globals()
            i = StringVar()
            i.set("")
            exec("l3 = Button(self.frame,textvariable=i,justify = LEFT, command = lambda: self.parent.getError("+str(index)+",'"+param+
                             "'),"+"font = ('courier',12),bg='aliceblue',anchor=W,width=10,height=1,"+
                             "padx=0,disabledforeground='black',foreground='purple')") in locals(), globals()
            l3.grid(sticky=ALL,row=count,column=2)
            v = IntVar()
            exec('l4 = Checkbutton(self.frame,variable=v, text="thawed", command=lambda: self.parent.toggleParam('+str(index)+',"'+param+
                            '"))') in locals(), globals()
            l4.grid(sticky=ALL,row=count,column=3)
            self.parent.thawedDict[(index,param)] = [v,i]
            self.parent.paramLabels[(index,param)]=(l1,l2,l3,l4)
            count += 1
        self.parent.dataCanvas.update_idletasks()
        self.parent.dataCanvas.configure(scrollregion = self.parent.dataCanvas.bbox('all'))
        try: 
            self.parent.statistic.set(u"Reduced \u03C7\u00B2: " + str(self.parent.fitter.reduced_chisq()))
        except (AttributeError,IndexError): pass

