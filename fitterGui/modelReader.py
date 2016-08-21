'''
Created on Mar 15, 2013

@author: kabanus
'''

from Tkinter import LEFT,N,S,E,W,Button,Toplevel,Frame,Entry,Label
from tkFont import Font
from tkFileDialog import askopenfilename
from re import finditer
import models
from time import sleep
import tkMessageBox as messagebox
ALL = N+S+W+E

currentReader = None
currentGetfun = None
class getFunc:
    class failedToInit(Exception): pass
    def __init__(self):
        global currentGetfun
        if currentGetfun: currentGetfun.eventDestroy(None)
        currentGetfun = self

        self.root = Toplevel(currentReader.root)
        self.root.transient(currentReader.root)
        parent = currentReader
        self.root.wm_geometry("+%d+%d" %(parent.root.winfo_rootx()+parent.root.winfo_width()/3.0, parent.root.winfo_rooty()))
        self.root.wm_title("Enter expression of 'x'")
        self.root.resizable(0,0) 
        
        self.root.bind("<Return>",self.parse)
        self.root.bind("<Key-Escape>",self.eventDestroy)

        self.expr = Entry(self.root,width=20,font=Font(size=16))
        self.expr.grid(row=0,column=1,sticky=ALL)
        Label(self.root,text='Expression(x): ').grid(row=0,column=0,sticky=ALL)
        
        self.params = Entry(self.root,width=20,font=Font(size=16))
        self.params.grid(row=1,column=1,sticky=ALL)
        Label(self.root,text='Parameters: ').grid(row=1,column=0,sticky=ALL)
        self.good = False
        self.expr.focus_set()

    def activate(self):
        self.root.wait_window()
        if not self.good: return ""
        return '"'+self.expr +'",'+str(self.params)

    def parse(self,event):
        try:
            params = {}
            if self.params.get(): 
                params = dict((kv.split(':') for kv in self.params.get().split()))
            for key in params: params[key] = float(params[key])
            function(self.expr.get(),params)(10)
        except ValueError:
            messagebox.showerror('Failed to evaluate function',"Parameters need to be <param>:<default> separated by space.")
            return
        except NameError as e:
            param = str(e).split("'")[1]
            messagebox.showerror('Failed to evaluate function',"Parameter '"+param+"' appears in expression but not in params. Note the variable should be 'x'.")
            return
        except Exception as e:
            messagebox.showerror('Failed to evaluate function',e)
            raise
            return
        self.params = params
        self.expr  = self.expr.get()
        self.good = True
        self.eventDestroy(None)
    
    def eventDestroy(self,event):
        global currentGetfun
        self.root.destroy()
        currentGetfun = None

MODELS = dict(((str(m),(m.description,m)) for m in models.exported.values()))
for m in models.exported:
    exec(m+' = MODELS["'+m+'"][1]')

PARAMS = {'Table' : lambda: '"'+askopenfilename()+'"', 'function': lambda: getFunc().activate()}
PARAMNAMES  = {'Table' : ('file'), 'function': ('expression')}
class modelReader(object):
    def __init__(self,parent):
        global currentReader
        currentReader = self
        self.border = parent.border
        self.width  = parent.width
        self.height = parent.height
        self.parent = parent
        self.root   = Toplevel(self.parent.root)
        self.root.transient(self.parent.root)
        self.root.wm_geometry("+%d+%d" %(parent.root.winfo_rootx(), parent.root.winfo_rooty()))
        self.root.wm_title("Build Model")
        self.root.resizable(0,0) 
        self.make_frames()

        Button( self.main, text = 'Parse', command = self.parse).grid( column = 2, row = 3, rowspan = 2, sticky = ALL)
        Button( self.main, text = 'Cancel', command = self.root.destroy).grid( column = 2, row = 1, rowspan = 2, sticky = ALL)

        self.entry  = Entry(self.main,width=80,font=Font(size=16))
        self.entry.grid(row = 0, column = 0,  columnspan = 3,sticky = W+E)
        self.entry.bind("<Return>",self.parse)
        self.entry.bind("<Key-Escape>",self.eventDestroy)
        self.entry.insert(0,self.parent.model)

        txt = "%-31s : %15s : %15s\n"%('description','name','parameters')
        Label( self.main, text = txt, justify = LEFT, font = ('courier',12,'bold underline'),anchor=N).grid( column = 0, row = 1,sticky = ALL)
        Label( self.main, text = self.genTxt(), justify = LEFT, font = ('courier',12,'bold'),anchor=N).grid( column = 0, row = 2, rowspan = 3,sticky = ALL)
        txt = 'Use () to make sure calculation order is correct, you can multiply (*) or add (+) models as you wish. If arguments will be needed to initiate model they will be requested left to right.'
        Label( self.main, text = txt, justify = LEFT, wraplength=495, font = ('courier',12,'bold'),anchor=N).grid(column = 1, row = 1, rowspan = 4, sticky = E+S+W+N,padx=self.border)

        self.entry.focus_set()

    def eventDestroy(self,event):
        self.root.destroy()

    def genTxt(self):
        txt = ''
        for model in MODELS:
            desc  = MODELS[model][0]
            try:
                txt += "%-31s : %15s : %15s\n"%(desc,model, PARAMNAMES[model])
            except KeyError:
                txt += "%-31s : %15s : %15s\n"%(desc,model, '')
        return txt

    def parse(self,event = None):
        model = self.entry.get()
        models = model.replace(" ","").replace('+(','+').replace(')+','+').replace('*(','+').replace(')*','+').replace('(','+').replace(')','+').replace('*','+').strip('+').split('+')
        for m in models: 
            if m not in MODELS:
                if m == '':
                    messagebox.showerror( 'Bad syntax!', 'Bad operation or empty equation.' )
                else:
                    messagebox.showerror( 'Bad syntax!', m + ' is NOT a model, see table below (CASE SENSITIVE).' )
                return
        
        models = set(models)
        try: 
            for m in models:
                padded = 0
                for p in finditer(m,model):
                    args = '()'
                    if m in PARAMS:
                        args = '('+PARAMS[m]()+')'
                    model = model[:padded+p.end()] + args + model[padded+p.end():]
                    padded += len(args)
            exec('model = ' + model)
        except TypeError:
            return
        except Exception as e:
            messagebox.showerror("Failed to build model!",str(e)+'\n\nFinal model attempted to execute: '+model)
            return

        self.parent.fitter.append(model)
        self.parent.model = str(model)
        self.parent.modelLoaded() 
        self.root.destroy()

    def make_frames(self):
        self.main = Frame(self.root,width=self.width, height=self.height, bg = 'black')
        self.main.grid(sticky =  ALL)

