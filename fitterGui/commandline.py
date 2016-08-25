from Tkinter import Entry,END,LEFT
import tkMessageBox as messagebox

class commandLine(object):
    def __init__(self, parent, frame):
        self.parent = parent
        self.currentCmd = -1
        self.cmdHist    = []

        self.entry = Entry(frame,font = ('courier',12),bg='aliceblue',justify = LEFT)
        self.entry.place(x=0,y=0,width=0)
        self.entry.bind("<Return>",self.parseCmd)
        self.entry.bind("<Up>"    ,lambda event: self.traverseCmd(event, True))
        self.entry.bind("<Down>"  ,lambda event: self.traverseCmd(event, False))

    def parseThaw(self, cmd):
        self.param = cmd[4:]
        if self.param != '*':
            self.index,self.param = self.param.split(':')
            self.index = int(self.index)
            self.param = self.param.strip()
            if self.param == '*':
                for self.param in self.parent.thawedDict:
                    if self.param[0] != self.index: continue
                    self.parent.thawedDict[self.param][0].set(1)
                    self.parent.toggleParam(*self.param)
            else:
                self.parent.thawedDict[(self.index,self.param)][0].set(1)
                self.parent.toggleParam(self.index,self.param)
        else:
            for self.param in self.parent.thawedDict: 
                self.parent.thawedDict[self.param][0].set(1)
                self.parent.toggleParam(*self.param)

    def parseFreeze(self, cmd):
        self.param = cmd[6:]
        if self.param != '*':
            self.index,self.param = self.param.split(':')
            self.index = int(self.index)
            self.param = self.param.strip()
            if self.param == '*':
                for self.param in self.parent.thawedDict:
                    if self.param[0] != self.index: continue
                    self.parent.thawedDict[self.param][0].set(0)
                    self.parent.toggleParam(*self.param)
            else:
                self.parent.thawedDict[(self.index,self.param)][0].set(0)
                self.parent.toggleParam(self.index,self.param)
        else:
            for self.param in self.parent.thawedDict: 
                self.parent.thawedDict[self.param][0].set(0)
                try: self.parent.toggleParam(*self.param)
                except ValueError as e:
                    passDoubleFreeze = "list.remove"
                    if e.message[:len(passDoubleFreeze)] != passDoubleFreeze: raise

    def parseSet(self, cmd):
        try:
            self.param,value = cmd.split('=')
            self.index,self.param = self.param.split(':')
            self.index = int(self.index)
            self.param = self.param.strip()
        except ValueError:
            messagebox.showerror('Failed to parse!','Command must be either freeze <index:param>, thaw <index:param>, or <index:param>=<value>')
            return False 
            
        self.parent.fitter.current[(self.index,self.param)]
        try: 
            self.parent.fitter.current.setp({(self.index,self.param):float(value)})
            self.parent.ranfit = False
            self.parent.paramLabels[(self.index,self.param)][1].delete(0,END)
            self.parent.paramLabels[(self.index,self.param)][1].insert(0,value)
        except ValueError: 
            messagebox.showerror('Failed to parse!','Value for '+str(self.index)+':'+self.param+' is not a float')
            return False
        return True

    def parseCmd(self, event):
        if self.parent.fitter.current == None:
            messagebox.showerror('No model!', 'Please load model first')
            return
        
        try: 
            res = event.widget.get().split(',')
        except AttributeError:
            res = event.split(',')
            
        needReset = False
        for cmdstr in res:
            cmd = cmdstr.replace(' ','')
            try: 
                if cmd[:4] == 'thaw':
                    self.parseThaw(cmd)
                elif cmd[:6] == 'freeze':
                    self.parseFreeze(cmd)
                else:
                    if not self.parseSet(cmd): break
                    needReset = True
            except (KeyError,IndexError):
                messagebox.showerror('Failed to parse!',str(self.index)+':'+self.param+' is not a model parameter')
                break
            except ValueError as e:
                passDoubleFreeze = "list.remove"
                if e.message[:len(passDoubleFreeze)] != passDoubleFreeze:
                    messagebox.showerror('Failed to parse!',self.param+' is not a model parameter, missing index?')
                    break
            self.cmdHist.append(cmd.replace('thaw','thaw ').replace('freeze','freeze '))
            try:
                event.widget.delete(0,len(cmdstr))
                if res[-1] != cmdstr: event.widget.delete(0,1)
            except AttributeError: pass
        if needReset:
            self.parent.params.resetErrors()
        self.parent.doAndPlot(self.parent.calc)
        self.currentCmd = len(self.cmdHist)

    def resizeCmd(self,event):
        self.entry.place(x=0,y=0,width=event.width)

    def traverseCmd(self, event, up):
        if self.currentCmd == -1: return
        if not up and self.currentCmd != 0:
            self.currentCmd -= 1
        if up:
            if self.currentCmd <= len(self.cmdHist)-1:
                self.currentCmd += 1
            if self.currentCmd == len(self.cmdHist):
                event.widget.delete(0,END)
                return
        event.widget.delete(0,END)
        event.widget.insert(0,self.cmdHist[self.currentCmd])

    def dump(self, cmd):
        self.entry.delete(0,END)
        self.entry.insert(0,cmd)

