from Tkinter import Entry,END,LEFT
import tkMessageBox as messagebox

class commandLine(object):
    class noModelWithParam(KeyError): pass
    def __init__(self, parent, frame):
        self.parent = parent
        self.currentCmd = -1
        self.cmdHist    = []

        self.entry = Entry(frame,font = ('courier',12),bg='aliceblue',justify = LEFT)
        self.entry.place(x=0,y=0,width=0)
        self.entry.bind("<Return>",self.parseCmd)
        self.entry.bind("<Up>"    ,lambda event: self.traverseCmd(event, True))
        self.entry.bind("<Down>"  ,lambda event: self.traverseCmd(event, False))

    def parseParam(self):
        params = self.param.split(':')
        try: self.index = int(params[0])
        except ValueError:
            if params[0] == '*': self.index = params[0]
            else: raise
        if (len(params) == 1 and self.index == "*") or params[1] =='*':
            self.param = '*'
        else:
            self.param = ":".join(params[1:]).strip()

    def iterIndex(self,index):
        if index == '*':
            for index in range(1,len(self.parent.fitter.current.__params__)+1): yield index
            return
        else: yield index
        
    def iterParam(self,index,param):
        if param == '*':
            for param in self.parent.fitter.current.__params__[index-1]: yield param
            return
        else: yield param
                

    def parseToggleThaw(self,cmd,title,check):
        self.param = cmd[title:]
        self.parseParam()
        self.oparam = self.param
        for index in self.iterIndex(self.index):
            self.param = self.oparam
            for param in self.iterParam(index, self.param):
                self.index = index
                self.param = param   
                self.parent.thawedDict[(index,param)][0].set(check)
                self.parent.toggleParam(index,param)

    def parseThaw(self, cmd):
        self.parseToggleThaw(cmd,4,1)

    def parseFreeze(self, cmd):
        self.parseToggleThaw(cmd,6,0)

    def parseSet(self, cmd):
        try:
            self.param,value = cmd.split('=')
            self.parseParam()
        except ValueError:
            messagebox.showerror('Failed to parse!','Command must be either freeze <index:param>, thaw <index:param>, or <index:param>=<value>')
            if self.parent.debug: raise
            return False 

        try:
            if self.index == self.param == '*':
                self.parent.fitter.current.setp({'*':float(value)})
            else:
                self.parent.fitter.current.setp({(self.index,self.param):float(value)})
        except ValueError:
            try:
                toind,topar = value.split(":")
                self.parent.fitter.current.tie((self.index,self.param),(int(toind),topar))      
            except KeyError:
                messagebox.showerror('Failed to parse!','Value (' +str(value)+') for '+str(self.index)+':'+self.param+' is not a float')
                if self.parent.debug: raise
                return False
        self.parent.ranfit = False
        self.parent.params.relabel()
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
        toadd = ''
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
            except self.noModelWithParam:
                messagebox.showerror('Failed to parse!',self.param+' is not a parameter of any component')
                if self.parent.debug: raise
                break
            except (KeyError,IndexError):
                messagebox.showerror('Failed to parse!',str(self.index)+':'+self.param+' is not a model parameter')
                if self.parent.debug: raise
                break
            except ValueError as e:
                passDoubleFreeze = "list.remove"
                if e.message[:len(passDoubleFreeze)] != passDoubleFreeze:
                    messagebox.showerror('Failed to parse!',self.param+' is not a model parameter, missing index?')
                    if self.parent.debug: raise
                    break
            toadd += cmd.replace('thaw','thaw ').replace('freeze','freeze ') + ','
            try:
                event.widget.delete(0,len(cmdstr))
                if res[-1] != cmdstr: event.widget.delete(0,1)
            except AttributeError: pass
        if needReset:
            self.parent.params.resetErrors()
            self.parent.doAndPlot(self.parent.calc)
        if toadd:
            self.cmdHist.append(toadd[:-1])
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

