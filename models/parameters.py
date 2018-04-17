'''
Created on 15-Oct-2016

@author: kabanus
'''
from collections import UserDict

class Primitive(object):
    def __eq__(self,other):
        return self.val == other               
    def __repr__(self):
        return str(self)                             
    def __str__(self):
        return str(self.val)

class Value(Primitive):
    def __init__(self, val):
        self.val = val

class View(Primitive):
    def __init__(self, obj, index, viewing):
        self.obj = obj
        self.viewing = viewing
        self.index   = index
    @property
    def val(self):
        return self.obj.val
    @val.setter
    def val(self,value):
        raise KeyError('Readonly pointer')
                        
class Parameters(UserDict):
    def __init__(self, args, clone = False):
        UserDict.__init__(self)
        dictionary = dict(args)
        for k,v in list(dictionary.items()):
            if clone: self.clone_item(k, v)
            else:     self[k] = v      
    def update(self,other):
        for k,v in map(lambda ko: (ko,UserDict.__getitem__(other,ko)),other):
            self.clone_item(k,v)         
    def clone_item(self,key,val):      
        UserDict.__setitem__(self,key,val)
    def pointing(self,key):
        try:
            obj = UserDict.__getitem__(self, key)
            return obj.index,obj.viewing
        except AttributeError:
            return False                              
    def pointer_to(self,index,key):
        return View(UserDict.__getitem__(self,key),index,key)
    def view(self):
        return dict([(key,View(val)) for key,val in list(self.items())])
    def __setitem__(self,key,value):
        try:               UserDict.__getitem__(self,key).val = value
        except (KeyError): UserDict.__setitem__(self,key,Value(value))
    def __getitem__(self,key):
        return UserDict.__getitem__(self,key).val
    
