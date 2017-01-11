#!/bin/bash
#Assume heasarc!
echo $BASH_SOURCE
if [[ ! -f parameter.dat ]]; then
    echo -E- Expecting parameter.dat in working directory to generate XSTAR data. Check script directory for parameter names.
    exit
fi

for x in ${*}; do
    mkdir -p logxi_$x
    cd logxi_$x 
    cp ../parameter.dat .
    sed -i "7s/^/..\//" parameter.dat
    sed -i "12s/.*/$x/" parameter.dat 
    xstar niter=99 < parameter.dat
    cd ..
done

$BASH_SOURCE/makeTable.bash 

