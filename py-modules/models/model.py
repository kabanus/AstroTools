from inspect import getargspec
from copy import deepcopy
import operator
from itertools import izip
from numpy import zeros

exported = {}
def modelExport(model):
    global exportedModels
    exported[str(model)] = model
    return model

class prettyClass(type):
    def __str__(self):
        return self.__name__

class Model(object):
    __metaclass__ = prettyClass
    class NoSuchParam(Exception): pass
    class VirtualMethod(Exception): pass

    def printParams(self):
        print self.paramString()

    def __mul__(self,other): return _composite(self,other,operator.mul)
    def __add__(self,other): return _composite(self,other,operator.add)

class _singleModel(Model):
    def __init__(self):
        try: args = getargspec(self._calculate)
        except AttributeError as e:
            raise self.VirtualMethod(str(e).split()[-1])
        self.description = "No description"

        defaults = args[-1]
        if defaults == None: defaults = []
        if len(args[0]) - len(defaults)< 2: 
            raise Exception('Calculator must have one non-default parameter! : ' + str(args[0])+" : "+str(args[-1]))
        
        self.thawed = [] #Needs order
        self.changed= set()
        self.params = {}
        self.wlhash = {} #User's responsibility.
        self.index  = 1  #This allows to differentiate same name parameters
        self.array       = zeros(0)

    def resetChanged(self):
        self.changed = set()
    
    def getThawed(self):
        return [(self.index,p) for p in self.thawed]

    def thaw(self, *args):
        if args[0] == "*" or args[0][1] == "*":
            self.thawed = self.params.keys()
            return
        for _,key in args:
            self.params[key]
            if key in self.thawed:
                continue
            self.thawed.append(key)

    def freeze(self, *args):
        if args[0] == "*" or args[0][1] == "*":
            print 'wtf'
            self.thawed = []
            return
        for _,key in args:
            try:
                self.thawed.remove(key)
            except ValueError: pass

    def getParams(self):
        for p in self.params.keys():
            yield (self.index,p),self.params[p]

    def initArgs(self):
        return [self.params[p] for p in self.thawed]

    def propagate_index(self, index = None):
        if index:
            self.index = index
            return index+1
        return 2
    
    def calculate(self,xlist):
        self.resetChanged()
        if len(xlist) != len(self.array):
            self.array = zeros(len(xlist))
        for i, el in enumerate(self._calculate(xlist)): self.array[i] = el
        return self.array


    def setp(self, pDict):
        for index,key in pDict.keys():
            if self.params[key] != pDict[(index,key)]:
                self.params[key] = pDict[(index,key)]
                self.changed.add(key)

    def tofit(self,xlist,*args):
        self.setp(dict(izip(izip((1 for _ in range(len(self.thawed))),
                                                 self.thawed),args)))
        return self.calculate(xlist)

    def paramString(self):
        res  = self.__class__.__name__+ " " + str(self.index) + ":\n"
        for k,v in self.params.items():
            res += ("    "+k+": "+str(v)) + '\n'
        return res

    def __getitem__(self,iparam):
        return self.params[iparam[1]]
    
    def printParams(self):
        print self.paramString()

    def __str__(self):
        return self.__class__.__name__

class _composite(Model):
    def __init__(self,model1,model2,relation):
        self.first    = deepcopy(model1)
        self.second   = deepcopy(model2)
        self.relation = relation
        self.propagate_index()
        self.params = []
        self.thawed = []
        try:
            self.params = self.first.params[:]
            self.thawed = self.first.thawed[:]
        except TypeError:
            self.params.append(self.first.params)
            self.thawed.append([])
        try:
            self.params.extend(self.second.params[:])
            self.thawed.extend(self.second.thawed[:])
        except TypeError:
            self.params.append(self.second.params)
            self.thawed.append([])

    def getParams(self):
        index = 1
        for params in self.params:
            for p in params:
                yield (index,p),params[p]
            index += 1            

    def propagate_index(self, index = None):
        index = self.first.propagate_index(index)
        self.index = self.second.propagate_index(index)
        return self.index

    def getThawed(self):
        res = []
        for i in range(len(self.thawed)):
            for p in self.thawed[i]:
                res.append((i+1,p))
        return res

    def thaw(self, *args):
        if args[0] == "*":
            count = 1
            for params in self.params:
                for p in params:
                    if count < self.second.index:
                        self.first.thaw((count,p))
                    else: 
                        self.second.thaw((count,p))
                    self.thawed[count-1].append(p)
                count += 1
            return
        for index,key in args:
            if index < self.second.index:
                self.first.thaw((index,key))
            else: 
                self.second.thaw((index,key))
            if key == '*':
                for (check,param),_ in self.getParams():
                    if check != index: continue
                    if param in self.thawed[index-1]: continue
                    self.thawed[index-1].append(param)
            else:
                if key in self.thawed[index-1]: continue
                self.thawed[index-1].append(key)

    def freeze(self, *args):
        if args[0] == "*":
            count = 1
            for params in self.params:
                for p in params:
                    if count < self.second.index:
                        self.first.freeze((count,p))
                    else: 
                        self.second.freeze((count,p))
                self.thawed[count-1] = []
                count += 1
            return
        for index,key in args:
            if index < self.second.index:
                self.first.freeze((index,key))
            else:
                self.second.freeze((index,key))
            if key == '*':
                self.thawed[index-1] = []
            else:
                try:
                    self.thawed[index-1].remove(key)
                except ValueError: pass

    def initArgs(self):
        return [self.params[i][p] for i in range(len(self.thawed))for p in self.thawed[i]]
    
    def tofit(self,xlist,*args):
        argIndex = 0
        if args:
            count = 1
            for model in self.thawed:
                for p in model:
                    self.setp({(count,p) : args[argIndex]})
                    argIndex += 1
                count += 1
        return self.calculate(xlist)

    def setp(self, pDict):
        for index,key in pDict:
            if index < self.second.index:
                self.first.setp({(index,key): pDict[(index,key)]})
            else:
                self.second.setp({(index,key): pDict[(index,key)]})
            self.params[index-1][key] = pDict[(index,key)]
   
    def resetChanged(self):
        self.first.resetChanged()
        self.second.resetChanged()

    def _calculate(self,x):
        return self.calculate(x)

    def calculate(self,x):
        return self.relation(self.first.calculate(x),self.second.calculate(x))

    def paramString(self):
        res  = self.first.paramString()
        res += self.second.paramString()
        return res
    
    def __getitem__(self,iparam):
        return self.params[iparam[0]-1][iparam[1]]

    def __str__(self):
        left = str(self.first)
        rigt = str(self.second)
        if self.relation == operator.mul:
            op = "*"
            try:
                if self.first.relation  == operator.add : left = '('+left+')'
            except AttributeError: pass
            try:
                if self.second.relation == operator.add : rigt = '('+rigt+')' 
            except AttributeError: pass
        if self.relation == operator.add:  op = "+"
        return left+op+rigt

