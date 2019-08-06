from tkinter import Toplevel,Frame,Canvas,BOTH
from tkinter.scrolledtext import ScrolledText
from io import StringIO
import re
import sys
import traceback

class DebugConsole:
    def __init__(self,root,title='',locals={},destroy=None):
        self.root = Toplevel(root)
        self.root.wm_title("Debug console")
        self.root.wm_geometry("480x640")
        self.locals = locals
        self.title  = title
        self.indent = 0
        self.block  = ''
        self.pos    = None
        if destroy is None:
            self.root.bind("<Key-Escape>",self._quit)
        else:
            self.root.bind("<Key-Escape>",destroy)
        
        self.orig_stdout = sys.stdout
        sys.stdout = StringIO()
        
        self.orig_stderr = sys.stderr
        sys.stderr = StringIO()
        
        self.initFrame()
    
    def _quit(self):
        self.root.quit()
        self.root.destroy()

    def initFrame(self):
        self.frame = Frame(self.root)
        self.frame.pack(fill=BOTH,expand=True)
        self.console = ScrolledText(self.frame,
                               bg="black",fg='orange',font=('Courier',15),
                               insertbackground='orange')
        self.console.pack(side="left",expand=True,fill=BOTH)

        if self.title:
            self.console.insert("insert",'='*(2+len(self.title))+'\n')
            self.console.insert("insert",'= '+self.title+'\n') 
            self.console.insert("insert",'='*(2+len(self.title))+'\n')

        self.console.insert("insert",'>')
        self.setLineStart()
        self.history = []
        self.history_index = -1

        self.console.bind("<Key>"       ,lambda e: self.insChar(e))
        self.console.bind("<Key-Return>",lambda e: self.run())
        self.console.bind("<Control-a>" ,lambda e: self.ctrlA())
        self.console.bind("<Control-A>" ,lambda e: self.ctrlA())
        self.console.bind("<Control-u>" ,lambda e: self.ctrlU())
        self.console.bind("<Control-U>" ,lambda e: self.ctrlU())
        self.console.bind("<Control-l>" ,lambda e: self.ctrlL())
        self.console.bind("<Control-L>" ,lambda e: self.ctrlL())
        self.console.bind("<BackSpace>" ,lambda e: self.delChar())
        self.console.bind("<Button-1>",lambda e: self.click())
        self.console.bind("<ButtonRelease-1>",lambda e: self.clack())
        self.console.bind("<B1-Motion>",self.cmove)
        self.console.bind("<ButtonRelease-2>",lambda e: "break")
    
        self.after_id = self.console.after(500,self.monitor)
    
    def setLineStart(self,offset = 0):
        r,c = self.console.index('end').split('.')
        self.lineStart = '{}.{}'.format(int(r)-1,int(c)+1+offset)

    def runEnd(self,insert, offset = 0,error = None):
        self.console.insert('end','\n'+insert)

        sys.stdout = StringIO()
        sys.stderr = StringIO()
        self.after_id = self.console.after(500,self.monitor)
        if error is not None:
            raise error
       
        self.setLineStart(offset)
        self.console.mark_set('insert','end')
        self.console.see('end')
        return 'break'

    def runBlock(self,cmd):
        if len(cmd):
            if self.indent or cmd.endswith(':'):
                self.block += self.indent*' '+cmd+'\n'
                
                if cmd.endswith(':'):
                    self.indent += 1
                dots = '...'*self.indent
                return self.runEnd(dots,len(dots)-1)
        if self.block:
            self.indent -= 1
            if self.indent:
                dots = '...'*self.indent
                return self.runEnd(dots,len(dots)-1)
            cmd         = self.block
            self.block  = ''
        return cmd

    def run(self):
        self.console.after_cancel(self.after_id)
        self.currentLine = ""
        try:
            cmd = self.console.get(self.lineStart,'end').strip()
            self.console.replace(self.lineStart,'end',cmd)
            cmd = re.sub('\s',' ',cmd)
            self.history.append(cmd)
            self.history_index = len(self.history)
           
            cmd = self.runBlock(cmd)
            if cmd == "break": return "break"
            if cmd:
                locs = locals()
                locs.update(self.locals)
                #In case we want to override self when debugging.
                s = self.locals.get('self',self)
                
                if cmd in locs: cmd = 'print({})'.format(cmd)
                if re.match(r'(import|for|while|if|from) |[a-zA-Z_]\w*\s*=',cmd):
                    ret = exec(cmd,globals(),locs)
                else:
                    ret = eval(cmd,globals(),locs)
                if ret is not None:
                    print(ret)
                
                #More trickery 
                self.locals.update(locals())
                self.locals['self'] = s
                if re.match(r'self\s*[+*/-|&]?=',cmd):
                    self.locals['self'] = eval(cmd.split('=',1)[1].strip(),globals(),self.locals)
        except Exception as e:
            traceback.print_exc()

        return self.runEnd(sys.stdout.getvalue()+sys.stderr.getvalue()+'>')
    
    def monitor(self):
        if sys.stdout.getvalue() or sys.stderr.getvalue():
            self.run()
        self.after_id = self.console.after(500,self.monitor)
        
    def delChar(self):
        c = self.console
        try:
            if c.tag_ranges('sel') or c.index('insert') == self.lineStart:
                return "break"
        except Exception: pass
    
    def ctrlA(self): 
        self.console.mark_set('insert',self.lineStart)
        return "break"
    def ctrlU(self): 
        self.console.replace(self.lineStart,'end','')
        return "break"
    def ctrlL(self): 
        self.console.replace('1.0 + {} chars'.format(3*(len(self.title)+3)),'end - 1 chars','>')
        self.setLineStart()
        self.console.mark_set('insert',self.lineStart)
        return "break"

    def insChar(self,event):
        if self.pos is not None: return "break"
        c = self.console
        if event.keysym == "Up":
            if self.history_index < 0: return "break"
            if self.history_index: 
                self.history_index -= 1
            c.replace(self.lineStart,'end',self.history[self.history_index])
            c.mark_set('insert','end')
            return "break"
        if event.keysym == "Down":
            if self.history_index < 0: return "break"
            if self.history_index < len(self.history):
                self.history_index += 1
            if self.history_index == len(self.history): 
                c.replace(self.lineStart,'end',self.currentLine.strip('\n'))
                return "break"
            c.replace(self.lineStart,'end',self.history[self.history_index])
            c.mark_set('insert','end')
            return "break"
        if event.keysym == "Left" and c.index('insert') == self.lineStart:
            return "break"

        self.currentLine = c.get(self.lineStart,'end')
    
        if (event.char or not event.keysym) and c.tag_ranges('sel'):
            c.selection_clear()

    def mark(self,x=None,y=None):
        if x is None:
            i = 'current'
        else: 
            i = '@{},{}'.format(x,y)
        r,c = [int(x) for x in self.console.index(i).split('.')]
        if r == self.click_pos[0] and r == self.click_pos[1]: return
        if r < self.click_pos[0] or (r == self.click_pos[0] and c < self.click_pos[1]):
            self.console.tag_add('sel',i,'{}.{}'.format(*self.click_pos))
        else:
            self.console.tag_add('sel','{}.{}'.format(*self.click_pos),i)

    def cmove(self,event):
        if self.pos is None: return "break"
        self.mark(event.x,event.y)
        return "break"
    
    def click(self):
        self.console.selection_clear()
        self.pos = self.console.index('insert')
        self.click_pos = [int(x) for x in self.console.index('current').split('.')]
        self.console.focus()
        return "break"
    
    def clack(self):
        self.console.mark_set('insert',self.pos)
        self.mark()
        self.pos = None
        return "break"
    
