'''
Created on Mar 15, 2013

@author: kabanus
'''

from tkinter import LEFT, N, S, E, W, Button, Toplevel, Frame, Entry, Label, Text
from tkinter.font import Font
from .helperfunctions import getfile
from .entrywindows import strReader
from .simplewindows import runMsg
import models
import tkinter.messagebox as messagebox
ALL = N+S+W+E

currentReader = None

currentXread = None


class XspecLoader(strReader):
    def __init__(self):
        global currentXread
        strReader.__init__(self, currentReader, "Enter Xspec model string")
        if currentXread:
            currentXread.eventDestroy(None)
        currentXread = self
        self.good = False
        self.string = ''

    def activate(self):
        self.root.wait_window()
        return "'"+self.string+"'"

    def parse(self, event):
        self.string = strReader.parse(self, event).replace(" ", "")
        try:
            self.model = models.Xspec(self.string)
            self.good = True
        except Exception as e:
            self.string = ''
            messagebox.showerror("Bad XSPEC string", 'Consult XSPEC manual, got:\n    {}'.format(str(e)))
            return
        self.eventDestroy(None)


currentGetfun = None


class getFunc(object):
    def __init__(self):
        global currentGetfun
        if currentGetfun:
            currentGetfun.eventDestroy(None)
        currentGetfun = self

        self.root = Toplevel(currentReader.root)
        self.root.transient(currentReader.root)
        parent = currentReader
        self.root.wm_geometry("+%d+%d" % (parent.root.winfo_rootx()+parent.root.winfo_width()/3.0,
                                          parent.root.winfo_rooty()))
        self.root.wm_title("Enter expression of 'x'")
        self.root.resizable(0, 0)

        self.root.bind("<Return>", self.parse)
        self.root.bind("<Key-Escape>", self.eventDestroy)

        self.expr = Entry(self.root, width=20, font=Font(size=16))
        self.expr.grid(row=0, column=1, sticky=ALL)
        Label(self.root, text='Expression(x): ').grid(row=0, column=0, sticky=ALL)

        self.params = Entry(self.root, width=20, font=Font(size=16))
        self.params.grid(row=1, column=1, sticky=ALL)
        Label(self.root, text='Parameters: ').grid(row=1, column=0, sticky=ALL)
        self.good = False
        self.expr.focus_set()

    def activate(self):
        self.root.wait_window()
        if not self.good:
            return ""
        return '"' + self.expr + '", ' + str(self.params)

    def parse(self, event):
        try:
            params = {}
            if self.params.get():
                params = dict((kv.split(':', 1) for kv in self.params.get().split()))
            for key in params:
                params[key] = float(params[key])
            function(self.expr.get(), params)(10)
        except ValueError:
            messagebox.showerror('Failed to evaluate function',
                                 'Parameters need to be <param>:<default> separated by space.')
            return
        except NameError as e:
            param = str(e).split("'")[1]
            messagebox.showerror('Failed to evaluate function', "Parameter '"+param+"' appears in expression " +
                                 "but not in params. Note the variable should be 'x'.")
            return
        except Exception as e:
            messagebox.showerror('Failed to evaluate function', e)
            raise
            return
        self.params = params
        self.expr = self.expr.get()
        self.good = True
        self.eventDestroy(None)

    def eventDestroy(self, event):
        global currentGetfun
        self.root.destroy()
        currentGetfun = None


MODELS = dict(((str(m), (m.description, m)) for m in list(models.exported.values())))
for m in models.exported:
    exec(m+' = MODELS["'+m+'"][1]')

PARAMS = {'Table': lambda: '"'+getfile()+'"', 'function': lambda: getFunc().activate(),
          'Xspec': lambda: XspecLoader().activate(), 'bbody': lambda: 'self.parent.fitter.resp.ebinAvg'}
PARAMNAMES = {'Table': ('file'), 'function': ('expression'), 'Xspec': 'XSPEC model'}


class modelReader(object):
    def __init__(self, parent, gui=True):
        global currentReader
        currentReader = self
        self.border = parent.border
        self.width = parent.width
        self.height = parent.height
        self.parent = parent

        try:
            for package in self.parent.xspec_packages:
                models.Xspec.lmod(*package)
        except Exception as e:
            if str(e) == "Error attempting to load local model library.":
                messagebox.showerror('Bad XSPEC library!',
                                     '"{}" is not a valid lmod parameter.'.format(' '.join(p for p in package if p)))
                return
            raise

        if not gui:
            return
        self.root = Toplevel(self.parent.root)
        self.root.transient(self.parent.root)
        self.root.wm_geometry("+%d+%d" % (parent.root.winfo_rootx(), parent.root.winfo_rooty()))
        self.root.wm_title("Build Model")
        self.root.resizable(0, 0)
        self.make_frames()

        Button(self.main, text='Parse', command=self.parse).grid(column=2, row=3, rowspan=2, sticky=ALL)
        Button(self.main, text='Cancel', command=self.root.destroy).grid(column=2, row=1, rowspan=2, sticky=ALL)

        self.entry = Text(self.main, width=80, height=1, font=Font(size=16))
        self.entry.grid(row=0, column=0,  columnspan=3, sticky=W+E)
        self.entry.bind("<Return>", self.parse)
        self.entry.bind("<Key-Escape>", self.eventDestroy)
        if self.parent.model:
            comps = iter(self.parent.fitter.current.modelList())
            expr = self.parent.fitter.current.splitModelString(repr(self.parent.fitter.current))
            c = 0
            for word in expr:
                if not word:
                    continue
                if word in ('*', '+', '(', ')'):
                    self.entry.insert('1.%d' % c, word)
                else:
                    lab = Label(self.entry, text=word, relief='raised', font='courier 12 bold')
                    lab.model = next(comps)
                    self.entry.window_create('1.%d' % c, window=lab)
                c += len(word)

        txt = "%-31s: %15s: %15s\n" % ('description', 'name', 'parameters')
        Label(self.main, text=txt, justify=LEFT, font=('courier', 12, 'bold underline'), anchor=N
              ).grid(column=0, row=1, sticky=ALL)
        Label(self.main, text=self.genTxt(), justify=LEFT, font=('courier', 12, 'bold'), anchor=N
              ).grid(column=0, row=2, rowspan=3, sticky=ALL)
        txt = ('Use () to make sure calculation order is correct, you can multiply (*) or add (+) models as '
               'you wish. If arguments will be needed to initiate model they will be requested left to right.')
        Label(self.main, text=txt, justify=LEFT, wraplength=495, font=('courier', 12, 'bold'), anchor=N
              ).grid(column=1, row=1, rowspan=4, sticky=E+S+W+N, padx=self.border)
        self.entry.focus_set()

    def eventDestroy(self, event):
        self.root.destroy()

    def genTxt(self):
        txt = ''
        for model in MODELS:
            desc = MODELS[model][0]
            try:
                txt += "%-31s: %15s: %15s\n" % (desc, model, PARAMNAMES[model])
            except KeyError:
                txt += "%-31s: %15s: %15s\n" % (desc, model, '')
        return txt

    @staticmethod
    def get_model_string(arg):
        if not arg:
            return arg
        options = []
        for m in MODELS:
            if m.lower() == arg.lower():
                options = [m]
                break
            if m.lower().startswith(arg.lower()):
                options.append(m)
        if not len(options):
            messagebox.showerror('Bad syntax!', arg + ' is NOT a model, see table below.')
            return
        elif len(options) > 1:
            messagebox.showerror('Ambiguous', '{} matches all of {}.'.format(arg, ', '.join(options)))
            return
        return options[0]

    def _nextChar(self, index):
        return index+1, self.entry.get('1.%d' % (index+1))

    class entryStr(str):
        def get(self, index, finalIndex=None):
            return self[int(index.split('.')[-1])]

    def returnDestroy(self, m):
        try:
            m.destroy()
        except Exception:
            pass
        return "break"

    def parse(self, event=None):
        expression = []
        if isinstance(event, str):
            self.entry = self.entryStr(event+'\n')
            msglen = len(self.entry)
        else:
            msglen = len(self.entry.get('1.0', 'end'))
        index, char = self._nextChar(-1)
        m = runMsg(self.parent, 'Loading model...')
        evalStr = ''
        while char != '\n':
            model = ''
            if char in ('+*()\n'):
                if char:
                    expression.append(char)
                else:
                    lname = self.entry.window_cget('1.%d' % index, 'window').split('.')[-1]
                    label = self.entry.children[lname]
                    expression.append(label.model)
                index, char = self._nextChar(index)
                continue
            while char not in ('+*()\n'):
                model += char
                index, char = self._nextChar(index)
            model = self.get_model_string(model)
            if model is None:
                return self.returnDestroy(m)
            if char == '(':
                argdepth = 0
                while True:
                    model += char
                    if char == '(':
                        argdepth += 1
                    if char == ')':
                        argdepth -= 1
                    index, char = self._nextChar(index)
                    if index == msglen:
                        messagebox.showerror("Bad syntax", "Forgot to close paranthesis?")
                        return self.returnDestroy(m)
                    if not argdepth:
                        break
            else:
                if model in PARAMS:
                    params = PARAMS[model]()
                    if params == "''":
                        return self.returnDestroy(m)
                    model += '({})'.format(params)
                else:
                    model += '()'
            try:
                expression.append(eval(model))
            except Exception as e:
                if str(e) == 'Model Command Error':
                    messagebox.showerror("Bad XSPEC string", 'Consult XSPEC manual, got:\n    {}'.format(str(e)))
                    return self.returnDestroy(m)

        if expression:
            evalStr = ''.join(['expression[%d]' % i if not isinstance(c, str) else c for i, c in enumerate(expression)])
        if not evalStr:
            return self.returnDestroy(m)

        try:
            model = eval(evalStr)
        except TypeError:
            messagebox.showerror("Failed to build model!", "Perhaps you forgot '*' for multiplication?")
            if self.parent.debug:
                raise
            return "break"
        except AttributeError as e:
            if str(e) == "'Fitter' object has no attribute 'resp'":
                messagebox.showerror("Failed to build model!", "Can't use bbody without loaded response")
            elif str(e) == "'str' object has no attribute 'sort'":
                messagebox.showerror("Failed to build model!", "Missing file for table!")
            else:
                raise
            if self.parent.debug:
                raise
            return "break"
        except Exception as e:
            messagebox.showerror("Failed to build model!",
                                 str(e)+'\n\nFinal model attempted to execute: "{}"'.format(model))
            if self.parent.debug:
                raise
            return "break"
        finally:
            m.destroy()

        self.parent.fitter.append(model)
        self.parent.model = str(model)
        self.parent.modelLoaded()
        try:
            self.root.destroy()
        except AttributeError:
            pass

    def make_frames(self):
        self.main = Frame(self.root, width=self.width, height=self.height, bg='black')
        self.main.grid(sticky=ALL)
