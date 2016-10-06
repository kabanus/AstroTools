#!/usr/bin/python

'''
Created on Mar 15, 2013

@author: kabanus
'''
if True or __name__ == "__main__":
    import os
    from sys import argv
    if os.name == 'nt':
        #Windows ctrl-c handling
        try:
            import win32api
            import thread
            import ctypes
            import imp
            
            basepath = imp.find_module('numpy')[1]
            ctypes.CDLL(os.path.join(basepath,'core','libmmd.dll'))
            ctypes.CDLL(os.path.join(basepath,'core','libifcoremd.dll'))
            def handler(dwCtrlType, hook_sigint = thread.interrupt_main):
                if dwCtrlType == 0: # CTRL_C_EVENT
                    hook_sigint()
                    return 1
                return 0 # chain to the next handler
            win32api.SetConsoleCtrlHandler(handler, 1)
        except (ImportError,WindowsError):
            print("Warning: win32api  module  not found, you will  not be able to Ctlr-C  calculations. To fix\n" +
                  "this try 'pip installPyWin32'  from  any   terminal,  or download and  install binary  from\n" +
                  "https://sourceforge.net/projects/pywin32/files/pywin32/. This warning may also be generated\n"+
                  "on Windows machines if numpy or something close is missing.")

    import tkMessageBox as messagebox
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
    from Tkinter         import Tk,StringVar,LEFT,TOP,N,S,E,W,Label,BOTH
    from tkMessageBox    import askquestion 
    from fitter          import Fitter
    from plotInt         import Iplot,plt
    from modelReader     import modelReader
    from simplewindows   import runMsg
    from entrywindows    import ignoreReader
    from parameterframe  import parameterFrame
    from helperfunctions import make_frames, getfile
    from gui             import Gui
    ALL = N+S+W+E
    Iplot.quiet()
    
    class App(object):
        debug = False
        xspec_packages = []
        def __init__( self, h = 500, w = 800, b = 5 ):        
            self.root = Tk()
            self.root.wm_title("The amazing fitter!")
            self.border      = b
            self.width       = 800
            self.height      = 500
            self.fitter      = Fitter()
            self.thawedDict  = {}
            self.statistic   = StringVar()
            self.statistic.set("No fit run")
            self.ignored     = StringVar()
            self.ignored.set("Ignored:")
            self.model       = ""
            self.datatitle=StringVar()
            self.datatitle.set("No active model")
            self.respfile    = StringVar()
            self.respfile.set("No response")
            self.datafile    = StringVar()
            self.datafile.set("No data")
            self.backfile    = StringVar()
            self.backfile.set("No bg")
            self.transfile   = StringVar()
            self.transfile.set("No transmission")
            self.paramLabels = {}
            self.ranfit      = False
            self.errors      = {}
            
            make_frames(self)
            self.params = parameterFrame(self,self.canvasDataFrame)
            self.params.draw()

            self.root.bind("<Key-Escape>",self._quit)
            self.root.protocol('WM_DELETE_WINDOW',self._quit) 

            self.canvas = FigureCanvasTkAgg( plt.get_current_fig_manager().canvas.figure, master = self.main)
            #Only load figure after manager has been set
            self.fitter.initplot()
            nav = NavigationToolbar2TkAgg(self.canvas,self.main)
            Label(nav,textvar= self.datafile,padx=self.border).pack(side=LEFT)
            Label(nav,textvar= self.respfile,padx=self.border).pack(side=LEFT)
            Label(nav,textvar=self.backfile,padx=self.border).pack(side=LEFT)
            Label(nav,textvar=self.transfile,padx=self.border).pack(side=LEFT)
            Gui(self,self.gui)
            
            self.refreshPlot()

            self.root.rowconfigure(0,weight=1)
            self.root.columnconfigure(0,weight=1)
            #For windows
            self.root.focus_force()
            self.root.mainloop()

        def refreshPlot(self):
            try: self.fitter.plot()
            except AttributeError: pass
            self.canvas.show()
            self.canvas.get_tk_widget().pack( side = TOP, fill = BOTH, expand = 1) 

        def loadModel(self):
            try: self.modelload.root.destroy()
            except AttributeError: pass
            self.modelload = modelReader(self)

        def modelLoaded(self):
            self.datatitle.set(self.fitter.current)
            self.params.draw()
            self.calc()

        def toggleParam(self,index,param):
            if self.thawedDict[(index,param)][0].get():
                self.fitter.thaw((index,param))
            else: 
                self.fitter.freeze((index,param))

        def dumpParams(self):
            cmd = ""
            for (index,param),value in self.fitter.getParams():
                cmd += str(index)+':'+param+" = "+str(value)+','
            for (index,param) in sorted(self.thawedDict):
                if self.thawedDict[(index,param)][0].get():
                    cmd += 'thaw '+str(index)+':'+param+','
            return cmd[:-1]

        def dumpParamCmd(self):
            try:
                self.commandline.dump(self.dumpParams())
            except AttributeError: pass

        def loadSession(self):
            init = {}
            fname = getfile('fsess')
            if not fname: return
            for line in open(fname):
                index = line.index(':')
                init[line[:index]] = line[index+1:].strip('\n').strip()

            self.fitter.resp = None
            try: self.load(self.fitter.loadData,init['data'])
            except KeyError: pass
            try: 
                if self.fitter.resp == None: self.load(self.fitter.loadResp,init['resp'])
            except KeyError: pass
            try: self.load(self.fitter.transmit,init['tran'])
            except KeyError: pass
            try: self.fitter.setplot(int(init['ptype']))
            except KeyError: pass
            
            try:
                ignored = init['Ignored']
                ig = ignoreReader(self,False)
                ig.parse(ignored)
            except KeyError: pass
        
            try: 
                model     = modelReader(self,False)
                model.parse(init['model'])
                self.commandline.parseCmd(init['param'])
                e = init['errors'].split(',')
                self.ranfit = True
                l = 4
                for index,param,mine,maxe in ([e[n] for n in range(i,i+l) ] for i in range(0,len(e),l)):
                    iparam = (int(index),param)
                    self.errors[iparam] = (float(mine),float(maxe))
                    error = (self.errors[iparam][1]-self.errors[iparam][0])/2.0
                    self.thawedDict[iparam][1].set('(%.2E)'%error)
                    self.paramLabels[iparam][2].configure(relief='flat',state='disabled')
            except KeyError: pass
            self.refreshPlot()

        def saveSession(self, name, extension):
            fd = open(name+'.'+extension,'w')
            writeline = lambda string: fd.write(string+'\n')
            
            try: writeline('data:' +self.fitter.data_file)
            except AttributeError: pass
            try: writeline('resp:' +self.fitter.resp_file)
            except AttributeError: pass
            try: writeline('tran:' +self.fitter.transmit_file)
            except AttributeError: pass
            try: writeline('ptype:'+str(self.fitter.ptype))
            except AttributeError: pass
            try: writeline(self.ignored.get())
            except AttributeError: pass
            try: writeline('model:'+self.fitter.current.__str__())
            except AttributeError: pass
            try: writeline('param:'+self.dumpParams())
            except AttributeError: pass
            if self.errors:
                writeline('errors:'+str(self.errors).translate(None,"(){} '").replace(':',','))
           
            fd.close()

        def saveParams(self, name, extension):
            if extension:
                name += '.'+extension
            params = [param.split('=') 
                        for param in self.dumpParams().split(',') 
                            if param[0] != 't' and param[1] != 'f']
            
            for i in range(len(params)):
                index,param = params[i][0].split(':')
                index = int(index)
                param = param.strip()
                try:
                    try:
                        #Look for measured error
                        err = self.errors[(index,param)]
                        params[i] = u'%3d %10s = %s (%.3E,+%.3E)'%(index,param,params[i][1],err[0],err[1])
                    except KeyError:
                        #Settle for standard error
                        err = self.fitter.stderr[(index,param)]
                        params[i] = u'%3d %10s = %s \u00B1 %.3E'%(index,param,params[i][1],err)
                except (KeyError,AttributeError): 
                    #Guess this has no error
                    params[i] = u'%3d %10s = %s'%(index,param,params[i][1])

            params.append(  self.statistic.get())
            params.append(  self.ignored.get())
            params.insert(0,self.datatitle.get())

            paramFile = open(name,'w')
            for p in params:
                paramFile.write(p.encode('utf-8')+'\n')
            paramFile.close
    
        def load(self, what, res = None):
            if res == None: res = getfile('ds','dat','RMF','RSP')
            if not res: return 
            m = runMsg(self,"Loading data")
            try: what(res)
            except (ValueError,IOError,KeyError) as e:
                messagebox.showerror('Bad file!','Please check file is correct format:\n'+str(e))
                if self.debug: raise
                return
            except Exception as e: 
                if str(e).find('ndarray') > -1:
                    messagebox.showerror('Bad file!','Tranmission and data have a different amount of channels!')
                else:
                    raise
                if self.debug: raise
                return 
            finally:
                m.destroy() 
            if self.fitter.current != None: 
                self.calc()
            try: self.transfile.set('Transmission: ' + self.fitter.transmit_file.split('/')[-1]) 
            except AttributeError: 
                self.untransmit(label_only = True)
            try:  self.respfile.set('Response: ' + self.fitter.resp_file.split('/')[-1]) 
            except AttributeError: pass
            try:  self.backfile.set('BG: ' + self.fitter.back_file.split('/')[-1]) 
            except AttributeError: pass
            try:  self.datafile.set('Data: ' + self.fitter.data_file.split('/')[-1]) 
            except AttributeError: pass

        def getError(self, index, param):
            if not self.ranfit:
                messagebox.showerror('Why would you want to?!','Run fit before calculating errors')
                if self.debug: raise
                return
            
            iparam = (index,param)

            #Message construct used so beep is heard before message, and save return on each one.
            try:
                m = runMsg(self)
                err = ''
                self.errors[iparam] = self.fitter.error(index,param)
            except (ValueError,KeyError):
                title, err = ('No such parameter!','Check yourself')
            except KeyboardInterrupt: 
                title, err = ('Halt',"Caught Keyboard - thawed parameters may have changed.")
            except self.fitter.errorNotConverging:
                title, err = ('Error not converging!',"Statistic insensitive to parameter")
            except self.fitter.newBestFitFound:
                title, err = ('Error not converging!',"Found new best fit! Space not convex.")
                self.params.resetErrors()
                self.ranfit = False
                self.params.relabel()
            finally:
                m.destroy()
                self.ring()
                if err:
                    messagebox.showerror(title,err)
                    return
            error = (self.errors[iparam][1]-self.errors[iparam][0])/2.0
            self.thawedDict[(index,param)][1].set('(%.2E)'%error)
            self.paramLabels[(index,param)][2].configure(relief='flat',state='disabled')

        def ring(self):
            #Windows
            self.root.bell() 
            #Anywhere else
            print "\a"

        def calc(self):
            m = runMsg(self)
            try:
                self.fitter.checkLoaded()
                self.fitter.calc()              
                self.refreshPlot()
            except (AttributeError,self.fitter.dataResponseMismatch): pass
            finally:
                self.params.relabel()
                self.params.resetErrors()
                self.ranfit = False
                self.ring()
                m.destroy()

        def untransmit(self,label_only = False):
            self.transfile.set("No transmission")
            self.transmit_file = ""
            if label_only: return
            self.doAndPlot(self.fitter.untransmit)

        def runFit(self):
            try:
                thawed = self.fitter.current.getThawed()
                if not thawed:
                    messagebox.showerror('Failed fit!',"No thawed parameters!")
                    if self.debug: raise
                    return
            except AttributeError:
                    messagebox.showerror('Failed fit!',"No model loaded!")
                    if self.debug: raise
                    return
            m = runMsg(self)
            try:
                self.doAndPlot(self.fitter.fit)
                self.ranfit = True
            except AttributeError: 
                messagebox.showerror('Failed fit!',"No fitting method!")
            except RuntimeError:
                messagebox.showerror('Failed fit!',"Can't converge, too many free parameters?")
            except Exception as e:
                messagebox.showerror('Failed fit!',e)
                raise
            finally:
                self.params.relabel()
                self.params.resetErrors()
                self.ring()
                m.destroy()
            try:
                for index,param in thawed:
                    self.thawedDict[(index,param)][1].set('(%.2E)'%self.fitter.stderr[(index,param)])
            except (KeyError,AttributeError):
                pass
            self.params.relabel()

        def doAndPlot(self, func):
            try: func()
            except AttributeError as e:
                messagebox.showerror('Failed','No model/data/resp loaded\n\n'+str(e))
                if self.debug: raise
                return 
            except KeyboardInterrupt: 
                messagebox.showerror('Halt',"Caught Keyboard")
            except Exception as e:
                messagebox.showerror('Failed',e)
                raise

            self.refreshPlot()
            #In case we changed axes, change ignore values to fit
            try: ignoreReader(self,False).parse("")
            except AttributeError: pass

        def resetIgnore(self):
            self.fitter.reset(zoom=False)
            self.ignored.set("Ignored:")

        def _quit(self, event = None):
            if askquestion("Exit","Sure?") == 'no': return
            self.root.quit()
            self.root.destroy() 

    readingX = False
    if len(argv) > 1:
        for arg in argv[1:]:
            if arg == '-xspec-packages':
                readingX = True
                continue
            if arg[0] == '-': 
                readingX = False
                if arg == '-debug':
                    App.debug = True
                continue
            if readingX:
                if not len(App.xspec_packages) or len(App.xspec_packages[-1]) > 1:
                    App.xspec_packages.append([arg])
                else: App.xspec_packages[-1].append(arg)
        if len(App.xspec_packages) and len(App.xspec_packages[-1]) != 2:
            raise Exception("Xspec packages should be pairs of <name> <path>. Got odd number of args.")
    App()     
  
