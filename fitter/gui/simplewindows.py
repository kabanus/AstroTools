from tkinter import Toplevel, Frame, Button, TOP, Label, LEFT, BOTH, Canvas, N, S, W, TclError
import tkinter.messagebox as messagebox
from .helperfunctions import updateFrame, genScrollCanvas


class simpleWindow:
    def __init__(self, parent, check, field, title):
        try:
            if check.find("data") > -1:
                parent.fitter.data
            if check.find("response") > -1:
                parent.fitter.resp
            if check.find("model") > -1 and parent.fitter.current is None:
                raise AttributeError()
        except AttributeError:
            messagebox.showerror('No '+check+'!', 'Please load '+check+' first')
            raise

        self.parent = parent
        self.root = Toplevel(self.parent.root)
        self.root.transient(self.parent.root)
        self.root.wm_geometry("+%d+%d" % (parent.root.winfo_rootx()+parent.root.winfo_width()/3.0,
                              parent.root.winfo_rooty()+parent.root.winfo_height()/2.0))
        self.root.wm_title(title)
        try:
            exec(('fld=parent.'+field), locals(), globals())
            field.focus_set()
            field.lift()
            return
        except (AttributeError, TclError):
            pass

        exec(('parent.'+field+' = self.root'), locals(), globals())
        self.root.bind("<Key-Escape>", self.eventDestroy)
        self.root.bind("<Return>", self.parse)
        self.root.resizable(0, 0)

    def parse(self, event):
        raise Exception('Not implemented')

    def eventDestroy(self, event):
        self.root.destroy()


class ScrollingCanvas(simpleWindow):
    def updateFrame(self, event):
        updateFrame(event)
        event.widget.configure(height=max(self.root.winfo_height(), self.canvasFrame.winfo_height()),
                               width=self.canvasFrame.winfo_width())
        self.root.wm_geometry('%dx%d' % (event.widget.winfo_width()+self.scrollbar.winfo_width(),
                              self.root.winfo_height()))

    def __init__(self, parent, field, title):
        simpleWindow.__init__(self, parent, "", field, title)
        root = self.parent.root
        self.root.wm_geometry("+%d+%d" % (root.winfo_rootx()+root.winfo_width()/7, root.winfo_rooty()))

        frame = Frame(self.root, background='lightblue')
        frame.pack(side=TOP, fill=BOTH)
        frame.rowconfigure(0, weight=1)

        canvas = Canvas(frame, background='lightblue')
        self.canvasFrame, self.scrollbar = genScrollCanvas(self.root, frame, canvas)
        canvas.grid(row=0, column=0, sticky=N+S)
        self.scrollbar.grid(row=0, column=1, rowspan=2, sticky=N+S)
        canvas.bind("<Configure>", self.updateFrame)
        self.wrap = 90

        Button(frame, text='OK', command=self.root.destroy).grid(row=1, column=0, columnspan=2, sticky=N+S)
        self.root.bind("<Key-Escape>", lambda event: self.root.destroy())


class Help(ScrollingCanvas):
    def __init__(self, parent):
        ScrollingCanvas.__init__(self, parent, 'helper', "Howto")
        self.helplabel("Modelling gui, Uria Peretz, 2016\n")
        self.helplabel("Most of it is self explanatory:", "", 16)
        self.helplabel("Load         : Load session or data/response fits file, XMM/Chandra format for now.")
        self.helplabel("Save         : Save session, plot, plot data or parameters (with errors).")
        self.helplabel("Plot         : Plot options that do not affect fit such as persistent zoom, "
                       "rebin and second Z axis or data shift. In addition can plot data divided by "
                       "other data, or divide out effective area.")
        self.helplabel("Ignore       : Ignore channels in fitting and plotting, or reset to all.")
        self.helplabel("Axis         : Plot counts as function of energy, wavelength, or channel.")
        self.helplabel("Calculate    : Calculate and plot model with given parameters, and errors on "
                       "parameters. Grouping here bins the data so the fit and division by other data is affected.")
        self.helplabel("Fit          : Go ahead and guess.")
        self.helplabel("Model        : Model selection - see syntax inside.")
        self.helplabel("Dump command : Effective way of saving current model. Dumps state to parser "
                       "(bottom left) to be copied or re-used.\n\n")
        self.helplabel("That's it! On the right you can see the parameters available, errors if calculated "
                       "and which one's are frozen (and used for fit).\n", "")

        self.helplabel("The parameter window", "", 16)
        self.helplabel("The parameter window on the left has useful information:")
        self.helplabel("1. Current model loaded")
        self.helplabel("2. index:parameter, then current value, then the error (see later), and finally"
                       " wether it is thawed or not.", "   ")
        self.helplabel(u"3. The current \u03C7\u00B2/d.o.f and ignored channels in the current axis' units.\n\n", "   ")
        self.helplabel("Right clicking gives some options such as hiding/showing frozen parameters and hiding the "
                       "window all together. Ctrl-F allows jumping to parameters if list is long, format is "
                       "index:param.", "")
        self.helplabel("\n")

        self.helplabel("Errors", "", 16)
        self.helplabel("Errors will be appear once a fit is performed - initial values, marked in a redish tint, "
                       "and appearing on a raised button are the standard error, and shouldn't be quoted in anything." +
                       u"Once a fit is performed you can press these buttons to compute the \u03C7\u00B2 "
                       "based proper errors, though this may take a while depending on the amount of thawed parameters."
                       " Once this is done the errors will be black and the button flattened (until you change "
                       "somthing/fit). Note if a new best fit is found this will reflect in the parameter "
                       "window.\n\n", "")

        self.helplabel("The command line", "", 16)
        self.helplabel("The command line on the bottom left is useful for batch inputting commands for "
                       "parameter. Syntax is '<command>, <command>, <command>' and so forth. <command> is one"
                       " of 'thaw <index:param>' 'freeze <index:param>' or '<index:param>=<value>'. This will"
                       " be parsed command by command and stop if one of the commands fails (leaving the rest"
                       " of the command line intact for a quick fix). Syntax such as *:param and param:* is "
                       "accepted. Note thawing a parameter while frozen are hidden will not make it appear, "
                       "and freezing won't make a parameter disappear, " "use the show thawed/hide frozen "
                       "right clicks to refresh this.\n\n", "")
        self.helplabel("Important notes", "", 16)
        self.helplabel("1. When saving session note you should leave parameters you want to focus on on load "
                       "thawed.", "")
        self.helplabel("\n")

        self.helplabel("Useful shortcuts (middle click plot area to get keyboard focus):", "", 16)
        self.helplabel("C, W, A  : Channel, wavelength, energy on axes.", "")
        self.helplabel("d, r, t, b: Load data/response/transmission/background.", "")
        self.helplabel("R, G, i, z: Rebin/group/ignore/zoom.", "")
        self.helplabel("m, F, s  : Load model/fit/save parameters.", "")
        self.helplabel("L, S:   : Load/Save fitting session.", "")
        self.helplabel("c      : Switch to commandline.", "")
        self.helplabel("H      : You're looking at it.", "")
        self.helplabel("Ctrl-F : Find parameter.", "")

    def rpad(self, substring):
        if substring[-1] == " ":
            substring = substring[:-1]
            try:
                word = substring.rindex(" ")
            except ValueError:
                return substring
            substring = substring[:word]+" "+substring[word:]
        return substring

    def lpad(self, substring):
        if substring[0] == " ":
            substring = substring[1:]
            try:
                word = substring.index(" ")
            except ValueError:
                return substring
            substring = substring[:word]+" "+substring[word:]
        return substring

    def helplabel(self, txt, spacing="               ", title=12):
        color = 'lightblue'
        wrap = self.wrap
        if len(spacing):
            Label(self.canvasFrame, text=self.rpad(txt[:wrap]), justify=LEFT, background=color,
                  anchor=W, font=('courier', title)).pack(side=TOP, fill=BOTH)
            rest = (spacing+txt[i:i+wrap-len(spacing)] for i in range(wrap, len(txt), wrap-len(spacing)))
        else:
            rest = (txt[i:i+wrap] for i in range(0, len(txt), wrap))

        for substring in rest:
            substring = self.lpad(self.rpad(substring))
            Label(self.canvasFrame, text=substring, justify=LEFT, background=color,
                  anchor=W, font=('courier', title)).pack(side=TOP, fill=BOTH)


class errorLog(ScrollingCanvas):
    def __init__(self, parent):
        ScrollingCanvas.__init__(self, parent, 'helper', "Howto")

        try:
            log = self.parent.fitter.errorlog
            self.root.maxsize(99999, 420)
        except AttributeError:
            log = []
        if not log:
            log = ["No error calculation done!"]
            self.root.maxsize(99999, 70)
        Label(self.canvasFrame, text="\n".join(log), justify=LEFT, background='lightblue',
              anchor=W, font=('courier', 12), width=70).pack(side=TOP, fill=BOTH)


class runMsg:
    def __init__(self, parent, msg="Running calculation"):
        self.root = Frame(parent.root, bg='')
        rows, cols = parent.root.grid_size()
        self.root.grid(row=0, column=0, columnspan=cols, rowspan=rows, sticky='nesw')

        frame = Frame(self.root)
        frame.place(relx=0.5, rely=0.5)

        Label(frame, text=msg, bg='aliceblue', font='courier 12 bold').pack(fill=BOTH)
        Label(frame, text="Cancel from terminal with Ctrl-C", bg='white').pack(fill=BOTH)
        parent.root.update()

    def destroy(self):
        self.root.destroy()


class WrappingLabel(Label):
    def __init__(self, parent, **kwargs):
        Label.__init__(self, parent, **kwargs)
        self.parent = parent

        def wrap(e, s=self.parent):
            old_wrap = int(str(self.cget('wraplength')))
            self.config(wraplength=s.winfo_width())
            if int(str(self.cget('wraplength'))) <= old_wrap:
                e.widget.unbind('<Configure>')

        self.bind('<Configure>', wrap)
