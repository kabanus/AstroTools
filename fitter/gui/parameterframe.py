from tkinter import Entry, LEFT, W, N, S, E, IntVar, StringVar, Button, END, Menu, Checkbutton
import tkinter.messagebox as messagebox
from .simplewindows import errorLog
from .entrywindows import paramReader
ALL = W+N+S+E


class parameterFrame(object):
    def __init__(self, parent, frame, root_frame):
        self.parent = parent
        self.frame = frame
        frame.columnconfigure(2, weight=1)
        self.parent.root.bind('<Control-f>', lambda event: paramReader(
            self.parent, self.find, "finder", "Find parameter", exactToggle=True))

        self.menu = Menu(self.frame, tearoff=0)
        self.menu.add_command(label='Hide frozen', command=self.hide)
        self.menu.add_command(label='Show all', command=self.show)
        self.menu.add_command(label='Show thawed', command=self.showthawed)
        self.menu.add_command(label='Thaw visible', command=lambda: self.toggleVisibleThaw(True))
        self.menu.add_command(label='Freeze visible', command=lambda: self.toggleVisibleThaw(False))
        self.menu.add_command(label='Errors on visible', command=self.errorVisible)
        self.menu.add_command(label='Show error log', command=lambda: errorLog(self.parent))
        self.menu.add_command(label='Hide Parameters', command=self.hideall)
        root_frame.bind("<Button-3>", self.showMenu)
        for child in root_frame.winfo_children():
            child.bind("<Button-3>", self.showMenu)
        self.frame.bind("<Button-3>", self.showMenu)
        for child in self.frame.winfo_children():
            child.bind("<Button-3>", self.showMenu)
        self.place = -1

    def errorVisible(self):
        # x[0] is the iparam
        # x[1] is the label
        self.parent.getError(*[x[0] for x in [x for x in list(self.parent.paramLabels.items()) if x[1][0].grid_info()]])

    def hideall(self):
        row = self.parent.cmdFrame.grid_info()['row']
        col = self.parent.cmdFrame.grid_info()['column']
        self.parent.data_frame.grid_remove()
        self.parent.dump.grid_remove()
        self.parent.info_frame.grid_remove()
        self.parent.cmdFrame.grid_remove()
        self.unhider = Button(text='Restore parameter frame', command=self.unhide)
        self.unhider.grid(row=row, column=col, sticky=ALL)

    def unhide(self):
        self.unhider.destroy()
        self.parent.data_frame.grid()
        self.parent.dump.grid()
        self.parent.info_frame.grid()
        self.parent.cmdFrame.grid()

    def showMenu(self, event):
        self.menu.tk_popup(event.x_root, event.y_root)

    def show(self):
        for iparam, labels in list(self.parent.paramLabels.items()):
            for label in labels:
                label.grid()

    def showthawed(self):
        for iparam, labels in list(self.parent.paramLabels.items()):
            if self.parent.thawedDict[iparam][0].get():
                for label in labels:
                    label.grid()

    def toggleVisibleThaw(self, thaw):
        for iparam, labels in list(self.parent.paramLabels.items()):
            if labels[0].grid_info():
                self.parent.thawedDict[iparam][0].set(thaw)
                self.parent.toggleParam(*iparam)

    def hide(self):
        for iparam, labels in list(self.parent.paramLabels.items()):
            if not self.parent.thawedDict[iparam][0].get():
                for label in labels:
                    label.grid_remove()

    def find(self, iparam, exact=False):
        index, param = iparam
        if not param:
            try:
                index = int(index)
            except ValueError:
                param = index
                index = '*'
        else:
            try:
                index = int(index)
            except ValueError:
                if index != '*':
                    messagebox.showerror("Bad index", "Got {}, expected integer or *".format(index))
                    return
        if not exact:
            param = param.lower()
        self.place += 1
        fail = not self.place
        for j, ((i, p), _) in enumerate(self.parent.fitter.getParams()):
            if j < self.place:
                continue
            if (index == '*' or i == index):
                if (not exact and param in p.lower()) or param == p:
                    param = p
                    break
            self.place += 1
        else:
            self.place = -1
            if fail:
                messagebox.showerror("No such parameter", "Please make sure "+str(index)+": *"+param+"* exists")
                return False
            else:
                return self.find(iparam, exact=exact)
        placement = self.place / (len(self.parent.paramLabels)+1.0)
        top,  bot = self.parent.scrollbar.get()
        offset = (bot-top)/2.0

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
        self.parent.scrollbar.set(top, bot)
        self.parent.dataCanvas.yview_moveto(placement)
        self.parent.paramLabels[(i, param)][1].focus_set()
        return True

    def entryIn(self, event):
        self.lastEntry = event.widget.get()
        event.widget.configure(background='white')
        self.place = event.widget.place

    def entryColor(self, event):
        event.widget.configure(background='white')

    def entryOut(self, event, index, param):
        current = event.widget.get()
        if current == "":
            event.widget.insert(0, self.lastEntry)
        elif current != self.lastEntry:
            try:
                try:
                    self.parent.fitter.setp({(index, param): float(current)})
                except ValueError:
                    to_index, to_param = current.split(": ", 1)
                    to_param = to_param.split("=")[0]
                    self.parent.fitter.tie((index, param), (int(to_index), to_param))
                self.resetErrors()
            except (KeyError, ValueError):
                event.widget.delete(0, END)
                event.widget.insert(0, self.lastEntry)
        event.widget.configure(background='aliceblue')
        if event.keysym == "Return":
            self.parent.calc()

    def resetErrors(self):
        for _, _, l3, _ in list(self.parent.paramLabels.values()):
            l3.configure(relief='raised', state='normal')
        self.parent.errors = {}

    def relabel(self):
        for iparam, value in self.parent.fitter.getParams():
            entry = self.parent.paramLabels[iparam][1]
            entry.delete(0, END)
            tied = self.parent.fitter.is_tied(*iparam)
            if not tied:
                tied = ''
            else:
                tied = str(tied[0])+": "+tied[1]+"="
            entry.insert(0, tied+str(value))
        self.parent.dataCanvas.update_idletasks()
        try:
            self.parent.statistic.set(u"Reduced \u03C7\u00B2: " + str(self.parent.fitter.reduced_chisq()))
            lab = {u'cstat': 'C', 'chisq': u'\u03C7\u00B2'}[self.parent.fitter.stat.__name__]
            self.parent.fstatistic.set("{} = {}".format(lab, self.parent.fitter.stat(self.parent.fitter.result)))
        except (AttributeError, IndexError):
            pass
        except ValueError:
            messagebox.showwarning("No Response", "Model loaded, but no response yet, so can't calculate or plot.")

    def draw(self):
        while self.parent.paramLabels:
            _, labels = self.parent.paramLabels.popitem()
            for label in labels:
                label.destroy()

        count = 1
        if self.parent.fitter.current is None:
            return
        self.parent.thawedDict = {}
        for p, ((index, param), value) in enumerate(self.parent.fitter.getParams()):
            l1 = Entry(self.frame, width=12, justify=LEFT, readonlybackground='aliceblue',
                       font=('courier', 12), takefocus=False)
            l1.insert(0, str(index)+": "+param)
            l1.configure(state='readonly')
            l1.grid(sticky=ALL, row=count, column=0),
            l2 = Entry(self.frame, justify=LEFT, font=('courier', 12), bg='aliceblue', width=7)
            l2.insert(0, str(value))
            l2.grid(sticky=ALL, row=count, column=1)
            l2.bind("<FocusOut>", lambda event, index=index, param=param: self.entryOut(event, index, param))
            l2.place = p
            l2.bind("<FocusIn>", self.entryIn)
            l2.bind("<Key>", self.entryColor)
            l2.bind("<Return>", lambda event, index=index, param=param: self.entryOut(event, index, param))
            i = StringVar()
            i.set("")
            l3 = Button(self.frame, textvariable=i, justify=LEFT,
                        command=lambda index=index, param=param: self.parent.getError((index, param)),
                        font=('courier', 12), bg='aliceblue', anchor=W, width=10, height=1, padx=0,
                        disabledforeground='black', foreground='purple', takefocus=False)
            l3.grid(sticky=ALL, row=count, column=2)
            v = IntVar()
            if (index, param) in self.parent.fitter.getThawed():
                v.set(1)
            l4 = Checkbutton(self.frame, variable=v, text="thawed", command=lambda index=index, param=param:
                             self.parent.toggleParam(index, param), takefocus=False)
            l4.grid(sticky=ALL, row=count, column=3)
            self.parent.thawedDict[(index, param)] = [v, i]
            self.parent.paramLabels[(index, param)] = (l1, l2, l3, l4)
            count += 1
        for child in self.frame.winfo_children():
            child.bind("<Button-3>", self.showMenu)
        self.parent.dataCanvas.update_idletasks()
        self.parent.dataCanvas.configure(scrollregion=self.parent.dataCanvas.bbox('all'))
        try:
            self.parent.statistic.set(u"Reduced \u03C7\u00B2: " + str(self.parent.fitter.reduced_chisq()))
        except (AttributeError, IndexError):
            pass
        except ValueError:
            messagebox.showwarning("No Response", "Model loaded, but no response yet, so can't calculate or plot.")
