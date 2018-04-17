'''
Created on Mar 15, 2013

@author: kabanus
'''

from tkinter          import LEFT,N,S,E,W,Button,Toplevel,Frame,Entry,Label
from tkinter.font     import Font
from re               import finditer
from .helperfunctions import getfile
from .entrywindows    import strReader
import models
import tkinter.messagebox as messagebox
ALL = N+S+W+E

currentReader = None

currentXread = None
class XspecLoader(strReader):
    def __init__(self):
        global currentXread
        strReader.__init__(self,currentReader,"Enter Xspec model string")
        if currentXread: currentXread.eventDestroy(None)
        currentXread = self
        self.good = False

    def activate(self):
        self.root.wait_window()
        return "'"+self.string+"'"

    def parse(self,event):
        self.string = strReader.parse(self,event).replace(" ","")
        try: 
            self.model = models.Xspec(self.string)
            self.good = True
        except Exception as e:
            print('-'+str(e)+'-')
            if str(e) == 'Model Command Error' or str(e):
                messagebox.showerror("Bad XSPEC string",'Consult XSPEC manual')
                return
            raise
        self.eventDestroy(None) 

currentGetfun = None
class getFunc(object):
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

MODELS = dict(((str(m),(m.description,m)) for m in list(models.exported.values())))
for m in models.exported:
    exec(m+' = MODELS["'+m+'"][1]')

PARAMS = {'Table' : lambda: '"'+getfile()+'"', 'function': lambda: getFunc().activate(),
          'Xspec' : lambda: XspecLoader().activate(),'bbody': lambda :'self.parent.fitter.resp.ebinAvg'}
PARAMNAMES  = {'Table' : ('file'), 'function': ('expression'), 'Xspec' : 'XSPEC model'}
class modelReader(object):
    def __init__(self,parent,gui = True):
        global currentReader
        currentReader = self
        self.border = parent.border
        self.width  = parent.width
        self.height = parent.height
        self.parent = parent
        
        for package in self.parent.xspec_packages:
            models.Xspec.lmod(*package)

        if not gui: return
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
        try:
            model = self.entry.get().replace(" ","")
        except AttributeError:
            model = event.replace(" ","")
        models  = ['']
        inparam = False
        last    = ''
        paramrng= []
        for i in range(len(model)):
            char = model[i]
            if char == '"' or char == "'": pass
            elif char == ')':
                if inparam:
                    inparam = False
                    paramrng[-1].append(i)
            elif inparam: pass
            elif char in '+*':
                models.append('')
            elif char == '(' and last and last not in '+*(':
                inparam  = True
                paramrng.append([i])
            else: 
                models[-1] += char
            last = char

        used = []
        for m in models:
            m = m.strip('(').strip(')')
            try: 
                index = m.index('(') 
                m = m[:index]
            except ValueError: pass
            if m not in MODELS:
                if m == '':
                    messagebox.showerror( 'Bad syntax!', 'Bad operation or empty equation.' )
                else:
                    messagebox.showerror( 'Bad syntax!', m + ' is NOT a model, see table below (CASE SENSITIVE).' )
                return
            used.append(m)
        models = set(used)
        try: 
            for m in models:
                padded = 0
                for p in finditer(m,model):
                    inparam = False
                    for rng in paramrng:
                        if p.start() >= rng[0] and p.start() <= rng[1]:
                            inparam = True
                            break
                    if inparam: continue
                    args = '()'
                    if m in PARAMS:
                        try:
                            if model[padded+p.end()] == '(':
                                args = ''
                            else: 
                                args = '('+PARAMS[m]()+')'
                        except IndexError:
                            args = '('+PARAMS[m]()+')'
                    for rng in paramrng:
                        if p.start() < rng[0]:
                            rng[0] += len(args)
                            rng[1] += len(args)
                    model = model[:padded+p.end()] + args + model[padded+p.end():]
                    padded += len(args)
            model = eval(model) 
        except TypeError:
            messagebox.showerror("Failed to build model!","Perhaps you forgot '*' for multiplication?")
            if self.parent.debug: raise
            return
        except AttributeError as e:
            if str(e) == "'Fitter' object has no attribute 'resp'":
                messagebox.showerror("Failed to build model!","Can't use bbody without loaded response")
            elif str(e) == "'str' object has no attribute 'sort'":
                messagebox.showerror("Failed to build model!", "Missing file for table!")
            else: raise
            if self.parent.debug: raise
            return
        except Exception as e:
            messagebox.showerror("Failed to build model!",str(e)+'\n\nFinal model attempted to execute: '+model)
            if self.parent.debug: raise
            return
        
        self.parent.fitter.append(model)
        self.parent.model = str(model)
        self.parent.modelLoaded() 
        try: self.root.destroy()
        except AttributeError: pass

    def make_frames(self):
        self.main = Frame(self.root,width=self.width, height=self.height, bg = 'black')
        self.main.grid(sticky =  ALL)

