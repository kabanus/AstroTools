from tkinter import Tk,Frame,Label,Entry,StringVar,Button,Checkbutton,IntVar,Canvas,Text,Toplevel
from tkinter import LEFT,RIGHT,BOTH,NW,BOTTOM,TOP,X,Y,END
from PIL     import Image,ImageTk,ImageDraw
from sys     import argv
from time    import time
from numpy   import log10,array,apply_along_axis,hstack,vstack,lib,where,delete as npdelete
from tkinter.messagebox import askquestion,showerror
from tkinter.filedialog import asksaveasfilename

class DataExtraction:
    @staticmethod
    def logscale(value,p0,p1):
        return p0*(p1/p0)**value

    @staticmethod
    def rolling_window(a, shape):
        s = ((a.shape[0] - shape[0] + 1,) + (a.shape[1] - shape[1] + 1,) + 
                (1,) + shape + (a.shape[2],))
        strides = a.strides + a.strides
        return lib.stride_tricks.as_strided(a, shape=s, strides=strides)

    @staticmethod
    def inside(r,x,y):
        return r[2] >= x >= r[0] and r[3] > y > r[1]

    def __init__(self,image,width = 800,height=600):
        self.root = Tk() 
        
        self.root.wm_title('Plot Data Extraction Tool')
        self.root.bind("<Key-Escape>",self._quit)
        self.root.protocol('WM_DELETE_WINDOW',self._quit) 
        self.root.resizable(0,0)
        
        self.main = Frame(self.root)
        self.main.pack()

        self.circles  = array((),dtype='int16').reshape(0,4)
        self.filename = image
        self.shapex   = -1
        self.im       = Image.open(image)
        self.original = self.im.copy()
        self.pim      = ImageTk.PhotoImage(self.im)
        self.canvas   = Canvas(self.main,cursor='plus',width=self.im.width,height=self.im.height)
        self.canvas.create_image(0,0,image=self.pim,anchor=NW)
        self.canvas.pack(side=LEFT)
        self.canvas.bind("<Motion>",self.getxy)
        self.canvas.bind("<ButtonPress-1>",self.setxy)
        self.canvas.bind("<ButtonRelease-1>",self.setShape)

        self.gui  = Frame(self.main)
        self.gui.pack(fill=BOTH,expand=True)
        Label(self.gui,text="Pix-Phys - click to reset").pack()
        self.xy = Frame(self.gui)
        self.xy.pack()
        self.coords = []
        self.fixed  = False
        for i,coord in enumerate(('x0','x1','y0','y1')):
            v = StringVar()
            self.coords.append({
                                'pix': Label(self.xy,text=coord),
                                'ent': Entry(self.xy,width=5),
                                'lab': Label(self.xy,textvariable=v,width=11,borderwidth=2,
                                       relief='solid'),
                               })
           
            self.coords[-1]['pix'].grid(row=i>1,column=3*(i%2)+0)
            self.coords[-1]['ent'].grid(row=i>1,column=3*(i%2)+1)
            self.coords[-1]['lab'].grid(row=i>1,column=3*(i%2)+2)
            
            self.coords[-1]['lab'].set = False
            self.coords[-1]['lab'].var = v
            
            self.coords[-1]['lab'].bind("<Button-1>",self.resetxy)
        self.xlog = IntVar()
        self.ylog = IntVar()
        Checkbutton(self.xy,variable=self.xlog,text='x log').grid(row=0,column=6)
        Checkbutton(self.xy,variable=self.ylog,text='y log').grid(row=1,column=6)

        bf = Frame(self.gui)
        bf.pack(fill=X)
        Button(bf,text="Fix Scale",command=self.fix,bg='grey').pack(side=LEFT,fill=X,expand=True)
        c = Button(bf,text="Find shape",command=self.findShape,bg='grey',anchor='w')
        c.pack(side=RIGHT,fill=X,expand=True)
        c.pack_propagate(False)

        vcmd = (c.register(lambda val: not len(val) or (len(val) <=2 and val.isdigit())) ,'%P')
        self.precision = Entry(c,width=2,vcmd=vcmd,validate='key')
        self.precision.pack(side=RIGHT)
        self.precision.insert(0,"1")
        self.position = StringVar()
        Label(c,text="uncertain=0.",bg='white').pack(side=RIGHT)

        f = Frame(self.gui) 
        f.pack(fill=X)
        Label(f,text="Plot Coordinates").pack(side=LEFT)
        Label(f,textvariable=self.position,borderwidth=2,relief='sunken').pack(
            side=RIGHT,expand=True,fill=X)
     
        c = Frame(self.gui)
        c.pack(side=TOP,fill=BOTH,expand=True)
        self.writerFrame = Frame(c)
        self.writerFrame.pack(side=LEFT,fill=BOTH,expand=True)
        self.writerFrame.pack_propagate(False)
        self.writer = Text(self.writerFrame)
        self.writer.pack()
        c = Frame(c)
        c.pack(side=RIGHT,fill=Y)
        self.pop = Button(c,text="Pop" ,command=self.pop)
        self.pop.pack(expand=True,fill=BOTH)
        Button(c,text="Clear",command=self.clear).pack(expand=True,fill=BOTH)
        Button(c,text="Save",command=self.save).pack(expand=True,fill=BOTH)

        c = Canvas(self.gui,bg='grey')
        c.pack(side=BOTTOM,fill=X)
        self.root.update()
        w,h=c.winfo_width(),c.winfo_height()
        self.zoom = Image.new("RGBA",(w,h),color="white")
        self.pzoom=ImageTk.PhotoImage(self.zoom)
        c.create_image(w//2,h//2,image=self.pzoom,anchor='center')
        length = 20
        c.create_line(w//2-length,h//2,w//2+length,h//2,width=2,fill='blue')
        c.create_line(w//2,h//2-length,w//2,h//2+length,width=2,fill='blue')
        
        #For windows
        self.root.focus_force()
        self.root.mainloop()

    def clear(self):
        self.writer.delete(1.0,END)
        self.im = Image.open(self.filename)
        self.pim.paste(self.im)

    def save(self):
        f = asksaveasfilename()
        if not f: return 
        with open(f,'w') as fd:
            fd.write(self.writer.get(1.0,END))

    def unpop(self,event = None):
        w = Text(self.writerFrame)
        w.pack()
        w.insert(END,self.writer.get(1.0,END))
        self.writer = w
        
        self.top.destroy() 
        self.pop.configure(state='normal')

    def pop(self):
        self.pop.configure(state='disabled')
        self.top = Toplevel(self.root)
        self.top.wm_title("Right click to save")
        w = Text(self.top)
        w.pack()
        w.insert(END,self.writer.get(1.0,END))
        self.writer.destroy()
        self.writer = w
        
        self.top.bind("<Key-Escape>",self.unpop)
        self.top.protocol('WM_DELETE_WINDOW',self.unpop) 

    def addCircle(self,draw,x,y,w,h):
        draw.ellipse((x,y,x+w,y+h),outline='red')

    def processShape(self,x0,y0,x1,y1,draw):
            draw.ellipse((x0,y0,x1,y1),outline='red')
            if self.fixed:
                self.writer.insert(END,"{:.2g} , {:.2g}\n".format(*self.pixToPlot((x0+x1)/2,(y0+y1)/2)))

    def findShape(self):
        try: x0,y0,x1,y1 = self.shape
        except AttributeError: return
        if x0 == x1 or y0 == y1: return

        self.im     = Image.open(self.filename)
        draw = ImageDraw.Draw(self.im)
        
        shape   = array(self.im)[y0:y1,x0:x1]
        a,b,c   = shape.shape
        windows = self.rolling_window(array(self.im),shape.shape[:2])
        target  = float("0."+self.precision.get())*a*b*c*255
        result  = vstack(where((windows-shape).sum(axis=(2,3,4,5))<target))
        apply_along_axis(lambda r: self.processShape(r[1],r[0],r[1]+b,r[0]+a,draw),0,result)
        
        self.pim.paste(self.im)

    def fix(self):
        pixels = []
        points = []
        for coord in self.coords:
            value = coord['ent'].get()
            if not coord['lab'].set or not len(value):
                showerror("Can't fix yet!","Make sure all pixels and plot values are set first!")
                self.fixed = False
                return
            try: points.append(float(value))
            except ValueError:
                showerror("Can't fix yet!","Non-float value in entry, "+value+"!")
                self.fixed = False
                return
            pixels.append(eval(coord['lab'].var.get()))
        self.xscale = (points[1] - points[0])/((pixels[1][0]-pixels[0][0])**2 +
                      (pixels[1][1]-pixels[0][1])**2)
        self.yscale = (points[3] - points[2])/((pixels[3][0]-pixels[2][0])**2 +
                      (pixels[3][1]-pixels[2][1])**2)
        self.px0,self.px1,self.py0,self.py1 = points
        self.x0,self.x1,self.y0,self.y1 = pixels
        self.xx = pixels[1][0]-pixels[0][0]
        self.xy = pixels[1][1]-pixels[0][1]
        self.yx = pixels[3][0]-pixels[2][0]
        self.yy = pixels[3][1]-pixels[2][1]
        self.fixed = True

    def pixToPlot(self,x,y):
        if not self.fixed:
            showerror("Can't calculate xy!","Mapping not fixed yet!")
        px = x - self.x0[0]
        py = y - self.x0[1]
        X=(px*self.xx+py*self.xy)*self.xscale
        px = x - self.y0[0]
        py = y - self.y0[1]
        Y=(px*self.yx+py*self.yy)*self.yscale
        try: 
            if self.xlog.get(): X = self.logscale(X,self.px0,self.px1)
            if self.ylog.get(): Y = self.logscale(Y,self.py0,self.py1)
        except ZeroDivisionError:
            showerror("Invalid range!","0 or negative value in logarithmic scale!")
            self.fixed = False
            self.position.set("")
            return
        return X,Y

    def removeShapes(self,rows):
        apply_along_axis(lambda r: self.im.paste(self.original.crop(r),r),1,self.circles[rows])
        npdelete(self.circles,rows,axis=0)
        self.pim.paste(self.im)
       
    def drawCircle(self,x0,y0,x1,y1,clear = False,save = True):
        if clear: 
            #self.im.paste(self.oldim.copy().crop((x0-1,y0-1,x1+1,y1+1)),(x0,y0))
            self.im = self.oldim.copy()
        draw = ImageDraw.Draw(self.im)
        draw.ellipse((x0,y0,x1,y1),outline='red')
        self.pim.paste(self.im)
        self.shape   = (x0,y0,x1,y1)
        if save:
            width = 1
            self.circles = vstack((self.circles,(x0-width,y0-width,x1+width,y1+width)))

    def initShape(self,x,y):
        self.shapex = x
        self.shapey = y
        self.oldim  = self.im.copy()
        self.drawCircle(x,y,x,y,True,False)

    def setShape(self,event):
        self.shapex = -1
        if time()-self.time < 0.3:
                if not self.fixed:
                    for coord in self.coords:
                        if not coord['lab'].set:
                            coord['lab'].set = True
                            coord['lab'].configure(relief='ridge')
                            break
                else:
                    x,y = event.x,event.y
                    try:
                        rows = apply_along_axis(lambda r: self.inside(r,x,y),1,self.circles)
                    except IndexError: rows = array(())
                    if rows.any():
                        self.removeShapes(where(rows))
                    else:
                        width = 5
                        self.writer.insert(END,"{:.2g} , {:.2g}\n".format(*self.pixToPlot(x,y)))
                        self.drawCircle(x-width,y-width,x+width,y+width)
                    self.getZoom(x,y) 
                    return
        self.im     = self.oldim.copy()

    def getZoom(self,x,y):
        try:
            h       = self.zoom.height
            w       = self.zoom.width
        except AttributeError: return

        white   = array([255,255,255,255])
        subimg  = array(self.im)[max(y-h//2,0):min(y+h//2,self.im.height),max(x-w//2,0):min(x+w//2,self.im.width)]
        if w//2 > x:
            leftpad  = white.repeat((w//2-x)*subimg.shape[0]).reshape(subimg.shape[0],-1,4)
            subimg   = hstack((leftpad,subimg))
        if w//2+x > self.im.width:
            rightpad = white.repeat((w//2+x-self.im.width)*subimg.shape[0]).reshape(subimg.shape[0],-1,4)
            subimg   = hstack((subimg,rightpad))
        if h//2 > y:
            toppad   = white.repeat(((h//2-y)*subimg.shape[1])).reshape(-1,subimg.shape[1],4)
            subimg   = vstack((toppad,subimg))
        if h//2+y > self.im.height:
            bottpad  = white.repeat((h//2+y-self.im.height)*subimg.shape[1]).reshape(-1,subimg.shape[1],4)
            subimg   = vstack((subimg,bottpad))
        color        = tuple(map(tuple,subimg.reshape(-1,4)))
        self.zoom.putdata(color)
        self.pzoom.paste(self.zoom.transform((self.zoom.width,self.zoom.height),Image.EXTENT,
            (0.25*self.zoom.width,0.25*self.zoom.height,0.75*self.zoom.width,0.75*self.zoom.height)))

    def getxy(self,event):
        x,y = event.x,event.y
        
        if self.shapex > -1:
            dx,dy = abs(self.shapex-x),abs(self.shapey-y)
            self.drawCircle(x-dx,y-dy,x+dx,y+dy,True,False)
        elif not self.fixed:
            for coord in self.coords:
                if not coord['lab'].set:
                    coord['lab'].var.set(str((x,y)))
        else:
            self.position.set("x = {:.4f} , y = {:.4f}".format(*self.pixToPlot(x,y)))
        self.getZoom(x,y)

    def setxy(self,event):
        self.initShape(event.x,event.y)
        self.time = time()

    def resetxy(self,event):
        event.widget.configure(relief='solid')
        event.widget.set = False
        self.fixed = False
    
    def _quit(self, event = None):
            if askquestion("Exit","Sure?") == 'no': return
            self.root.quit()
            self.root.destroy() 

try:
    DataExtraction(argv[1])
except IndexError:
    print("-E- Image filename missing!")


