#!/usr/bin/env python3

header = True
result = open('res.dat','w')
for line in open('xitable.dat'):
    fields = line.split()
    if fields[0] == "Next:":
        current = fields[1]
        continue
    if fields[0] == "radius":
        if not header: continue
        header = False
        result.write('ion_run '+line)
        continue
    result.write(current+' '+line)
result.close()

