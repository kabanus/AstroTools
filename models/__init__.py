
from ._export import exported
for model in exported:
    exec(model+'='+'exported["'+model+'"]')

