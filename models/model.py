from inspect import getargspec
import operator
import re

from parameters import Parameters

exported = {}
def modelExport(model):
    global exportedModels
    exported[str(model)] = model
    return model

class prettyClass(type):
    def __str__(self):
        return self.__name__
    
class Model(object, metaclass=prettyClass):
    class NoSuchParam(Exception): pass
    class VirtualMethod(Exception): pass
    
    def tofit(self,xlist,*args):
        self.setp(dict(zip(self.getThawed(),args)))
        return self.calculate(xlist)

    def initArgs(self):
        return [self.__params__[i-1][p] for i,p in self.getThawed()]
    
    def tie(self,param,to):
        if param == to: raise KeyError("Sure you want to a parameter to itself...?")
        self.__params__[param[0]-1].clone_item(param[1],self.__params__[to[0]-1].pointer_to(*to))
        
    def is_tied(self,index,key):
        return self.__params__[index-1].pointing(key)
    
    def getParams(self):
        return [((index,param),val) for index,params in enumerate(self.__params__,1)
                                            for param,val in list(params.items())]
    
    def getThawed(self):
        return sum(self.thawed,[])            
    
    def iterArgs(self, args):
        for index,key in args:
            if key == '*':
                for key in self.__params__[index-1]:
                    yield index,key,index,'*'
            elif index == '*':
                for index in range(1,len(self.__params__)+1):
                    yield index,key,'*',key
            else: yield index,key,index,key
    
    def thaw(self, *args):
        if args == ("*",):
            index = 1
            for  thlist in self.thawed:
                thlist[:] = [(index,param) for param in self.__params__[index-1]]
                index += 1
            return
        for index,key,_,_ in self.iterArgs(args):
            self.__params__[index-1][key]
            thlist = self.thawed[index-1]
            if (index,key) not in thlist:
                thlist.append((index,key))

    def freeze(self, *args):
        if args == ("*",):
            for  thlist in self.thawed:
                thlist[:] = []
            return
        for index,key,_,_ in self.iterArgs(args):
            thlist = self.thawed[index-1]
            try:
                thlist.remove((index,key))
            except ValueError: pass
        
    def resetChanged(self):
        for chset in self._changed:
            chset.clear()       

    def _setp(self, index, key, val):
        if self.__params__[index-1][key] != val:
                self.__params__[index-1][key] = val
                self.__params__[index-1].hook(index,key)
                if self.__params__[index-1][key] == val:
                    self._changed[index-1].add(key)

    def setp(self, pDict = {}, **kwargs):
        if list(pDict.keys()) == ['*']:
            for index in range(1,len(self.__params__)+1):
                for p in self.__params__[index-1]:
                    self._setp(index,p,pDict['*'])
            return
        for index,key,pIndex,pKey in self.iterArgs(pDict):
            self._setp(index,key,pDict[(pIndex,pKey)])
        for key in kwargs:
            self._setp(1,key,kwargs[key])

    @staticmethod
    def splitModelString(string):
        res      = ['']
        argdepth = 0
        for c in string:
            if c in ('+','*') and not argdepth:
                res.extend((c,''))
            elif c == '(':
                if not argdepth and not res[-1] and res[-2][-1] in ('+','*'):
                    res[-1] = '('
                    res.append('')
                else:
                    argdepth += 1
                    res[-1]+='('
            elif c == ')':
                if argdepth:
                    argdepth -= 1
                    res[-1]+=')'
                    if not argdepth: res.append('')
                else:
                    res.extend((')',''))
            else: res[-1]+=c
        return res

    def paramString(self):
        for index,params in enumerate(self.__params__,1):
            res  = self.__class__.__name__+ " " + str(index) + ":\n"
            for k,v in list(params.items()):
                res += ("    "+k+": "+str(v)) + '\n'
        return res

    def printParams(self):
        print(self.paramString())
        
    def __getitem__(self,iparam):
        index, param = iparam
        return self.__params__[index-1][param]

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
        self.thawed    = [[]]    #Needs order
        self.changed   = set()          #For easy use in models
        self._changed  = [self.changed] #Actually used
        self._params   = Parameters(()) #For easy use in models(self.params)
        self._params.hook=self.sethook
        self.__params__  = [self._params] #Actually used
        self.modelIndex  = 0

    def setModelIndex(self,to):
        self.modelIndex = to

    def sethook(self, index, key): pass 

    @property
    def params(self):
        return self._params
    @params.setter
    def params(self, dict_init):
        self._params.update(Parameters(dict_init))
        self._params.hook = lambda index,key,s=self: s.sethook(index,key)
        return self.params 
    
    def calculate(self,xlist):
        result = self._calculate(xlist)
        self.resetChanged()
        return result

    def insertedComponent(self,relation,model,position):
        return _composite(self,model,relation)
    
    def deletedComponent(self,index):
        if index == self.modelIndex: return None
        return False

    def getComponent(self,index):
        if index == self.modelIndex: return self
        return None

    def modelList(self):
        return [self]

    def __str__(self):
        return self.__class__.__name__
    
    def __repr__(self):
        return str(self.modelIndex)+':'+self.__class__.__name__

class _composite(Model):
    def __init__(self,model1,model2,relation):
        self.first = model1
        self.second = model2
        self.relation = relation

        self.__params__  = self.first.__params__ + self.second.__params__
        self.thawed      = self.first.thawed     + self.second.thawed
        self._changed    = self.first._changed   + self.second._changed

        self.second.setModelIndex(self.first.modelIndex+1)
        self.modelIndex = self.second.modelIndex

    def setModelIndex(self,to):
        self.first.setModelIndex(to)
        self.second.setModelIndex(self.first.modelIndex+1)
        self.modelIndex = self.second.modelIndex

    def getComponent(self,index):
        if self.first.modelIndex < index:
            return self.second.getComponent(index)
        return self.first.getComponent(index)

    def deletedComponent(self,index):
        if self.first.modelIndex < index:
            deleted = self.second.deletedComponent(index)
            if  deleted is None:
                return self.first
            self.second = deleted
        else: 
            deleted = self.first.deletedComponent(index)
            if deleted is None:
                return self.second
            self.first = deleted
        return self

    def insertedComponent(self,relation,model,position):
        try:
            models = (self.first,self.second)
            if position: return _composite(self.first,_composite(models[position],model,relation),self.relation)
            else:        return _composite(_composite(models[position],model,relation),self.second,self.relation)
        except IndexError:
            raise ValueError("Insertion position may only be 0 or 1 - with first or with second component.")

    def _calculate(self,x):
        return self.calculate(x)

    def calculate(self,x):
        return self.relation(self.first.calculate(x),self.second.calculate(x))

    def paramString(self):
        res  = self.first.paramString()
        res += self.second.paramString()
        return res
    
    def modelList(self):
        return self.first.modelList() + self.second.modelList()

    def __repr__(self):
        return self.toStr(repr)

    def __str__(self): 
        return self.toStr()

    def toStr(self,func=str):
        left = func(self.first)
        rigt = func(self.second)
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

