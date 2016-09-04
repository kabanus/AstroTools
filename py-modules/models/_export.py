
from os.path import dirname, basename, isfile, realpath
import glob
import sys 

sys.path.append(dirname(realpath(__file__)))
modules = glob.glob(dirname(__file__)+"/*.py")

__all__ = []
for f in modules:
    m = basename(f)[:-3]
    if m == '__init__' or m == '_export' or not isfile(f): continue
    module = __import__(m)
    for name in dir(module):
        exec(name+'=module.'+name)

from model import exported

