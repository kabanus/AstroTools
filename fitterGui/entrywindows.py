
from Tkinter import Entry,LEFT,Label
import tkMessageBox as messagebox
from plotInt import Iplot
from simplewindows import simpleWindow

class entryWindow(simpleWindow):
    def __init__(self,parent,check,field,title,width = 20):
        simpleWindow.__init__(self,parent,check,field,title)
        
        self.entry = Entry(self.root,justify = LEFT, font = ('courier',12), width = width, border = parent.border)
        self.entry.pack()
        self.entry.focus_set()

class strReader(entryWindow):
    def __init__(self, parent,title):
        try: entryWindow.__init__(self,parent,'',"stringer",title)
        except AttributeError: return

    def parse(self,event):
        return self.entry.get()

class zReader(entryWindow):
    def __init__(self, parent,data):
        try: entryWindow.__init__(self,parent,'data',"ashifter","Rest frame")
        except AttributeError: return
        self.data = data
    def parse(self, event):
        try: 
            res = float(self.entry.get())
        except ValueError:
            messagebox.showerror('Bad Z!', 'Only float please')
            return 

        self.parent.doAndPlot(lambda: self.parent.fitter.shift(res,self.data))
        self.root.destroy()

class rebinReader(entryWindow):
    def __init__(self, parent):
        try: entryWindow.__init__(self,parent,'data',"rebinner","Rebin")
        except AttributeError: return
    
    def parse(self, event):
        try: 
            res = int(self.entry.get())
            if res < 1: raise ValueError()
        except ValueError:
            messagebox.showerror('Bad rebin!', 'Only positive (>=1) integer please')
            return 
        self.parent.doAndPlot(lambda: self.parent.fitter.rebin(res) )
        self.root.destroy()

class ignoreReader(entryWindow):
    def __init__(self, parent, gui = True):
        if not gui:
            self.parent = parent
            return
        try: entryWindow.__init__(self,parent,'data/response',"ignorer","Ignore x-axis values")
        except AttributeError: return

    def parse(self, event):
        res = []
        try:
            try:
                res = self.entry.get().split()
            except AttributeError:
                res = event.split()
            channels = []
            for rng in res:
                try:
                    if self.parent.fitter.ptype == 0:
                        start = int(rng)
                    else:
                        start = float(rng)
                    stop  = start
                except ValueError:
                    if self.parent.fitter.ptype == 0:
                        start,stop = [int(x) for x in rng.split('-')]
                    else:
                        start,stop = [float(x) for x in rng.split('-')]
                channels.append((start,stop))
        except ValueError as e:
            messagebox.showerror('Failed to resize!', 'All values must be integers: '+str(e))
            return
        for start,stop in channels:
            self.parent.doAndPlot(lambda: self.parent.fitter.ignore(start,stop))

        ignored = ''
        deleted = sorted(self.parent.fitter.data.deleted)
        i = 0
        while i <  len(deleted):
            start = deleted[i]
            i += 1
            while i < len(deleted) and deleted[i] - deleted[i-1] == 1: i += 1
            if start != deleted[i-1]:
                ignored = ignored + ' ' + self.setUnits(start+1,deleted[i-1]+1)
            else: 
                ignored = ignored + ' ' + self.setUnits(start+1)
        if len(deleted) == 1:
            ignored = ' ' + str(deleted[0]+1)
        self.parent.ignored.set("Ignored:"+ignored)
        try:
            self.root.destroy()
        except AttributeError: pass

    def setUnits(self,start,end = ''):
        if end != '':
            if self.parent.fitter.ptype == 0: end   = '-%d'%end
            if self.parent.fitter.ptype == 1:
                tmp   = end
                end   = '-%.2f'%list(self.parent.fitter.resp.energy(((start,0),)))[0][0]
                start = tmp
            if self.parent.fitter.ptype == 2: end   = '-%.2f'%list(self.parent.fitter.resp.wl    (((end,0),)))[0][0]
      
        if self.parent.fitter.ptype == 0: return ('%d'%start)+end
        if self.parent.fitter.ptype == 1: return ('%.2f'%list(self.parent.fitter.resp.energy(((start,0),)))[0][0])+end
        if self.parent.fitter.ptype == 2: return ('%.2f'%list(self.parent.fitter.resp.wl    (((start,0),)))[0][0])+end
   
class Save(entryWindow):
    def __init__(self,parent,saver = Iplot.export, title = 'Save (extensions determines type)', default_ext = 'ps'):
        try:
                if saver == Iplot.export: parent.fitter.data
                elif saver == parent.saveParams and parent.fitter.current == None:
                    messagebox.showerror('Nothing to save!','Please load model')
                    return
                else:
                    try: parent.fitter.data
                    except AttributeError:
                        if parent.fitter.current == None:
                            messagebox.showerror('Nothing to save!','Please load model or data')
                            return
        except AttributeError:
            messagebox.showerror('Nothing to save!','Please load data')
            return

        try: entryWindow.__init__(self,parent,'data',"saver",title,30)
        except AttributeError: return
        self.saver = saver
        self.default_ext = default_ext

    def parse(self, event):
        try:
            name,ext = self.entry.get().split('.')
        except ValueError:
            name = self.entry.get()
            ext  = self.default_ext
        try: self.saver(name,ext)
        except ValueError as e:
            messagebox.showerror('Bad format!',e)
            return
        self.root.destroy()

class paramReader(entryWindow):
    def __init__(self, parent, function, parent_field,title):
        try: entryWindow.__init__(self,parent,'model',parent_field,title)
        except AttributeError: return
        self.do = function
    def parse(self, event):
        try:
            index, param = self.entry.get().split(":")
        except ValueError:
            messagebox.showerror('Bad format!',"Must be <index>:<parameter>")
            return
        index = int(index)
        param = param.strip()
        self.do(index,param)
        self.root.destroy()

class rangeReader(simpleWindow):
    def __init__(self, parent):
        try: simpleWindow.__init__(self,parent,'model',"mranger","Range in keV")
        except AttributeError: return
        
        self.entries = []
        for col,axis in enumerate(('min','max')):
            Label(self.root,text=axis).grid(row = 0, column=col*2)
            self.entries.append(Entry(self.root,justify = LEFT, font = ('courier',12), width = 4, border = parent.border))
            self.entries[-1].grid(row = 0, column=col*2+1)
        self.entries[0].focus_set()

    def parse(self, event):
        try:
            start = float(self.entries[0].get())
            stop  = float(self.entries[1].get())
            if start >= stop: raise ValueError
        except ValueError:
            messagebox.showerror('Bad range!', 'Please enter floats, and min < max')
            return

        self.parent.doAndPlot(lambda: self.parent.fitter.plotModel(start,stop,(stop-start)/1000.0))
        self.root.destroy()


class zoomReader(simpleWindow):    
    def __init__(self, parent):
        try: simpleWindow.__init__(self,parent,'data',"zoomer","Zoom")
        except AttributeError: return
         
        self.entries = []
        for axis in ('xmin','xmax','ymin','ymax'):
            row = 0
            col = 0
            if axis[0] == 'y': row = 1
            if axis[-1] == 'x': col = 2
            Label(self.root,text=axis).grid(row=row, column=col)
            self.entries.append(Entry(self.root,justify = LEFT, font = ('courier',12), width = 4, border = parent.border))
            self.entries[-1].grid(row=row,column=col+1)

        self.entries[0].focus_set()

    def parse(self, event):
        res = [self.parent.fitter.xstart,self.parent.fitter.xstop,
               self.parent.fitter.ystart,self.parent.fitter.ystop]
        count = 0
        for entry in self.entries: 
            try:
                res[count] = float(entry.get())
            except ValueError as e:
                if entry.get() != "":
                    messagebox.showerror('Failed to resize!', 'Got bad value: '+str(e))
                    return
            count += 1
        if res[0] and res[1] and res[0] >= res[1]:
            messagebox.showerror('Failed to resize!', 'Max must be greater than min: '+str(res[0])+'>='+str(res[1]))
            return
        if res[2] and res[3] and res[2] >= res[3]:
            messagebox.showerror('Failed to resize!', 'Max must be greater than min: '+str(res[2])+'>='+str(res[3]))
            return

        self.parent.doAndPlot(lambda: self.parent.fitter.zoomto(*res))
        self.root.destroy()

