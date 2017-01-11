#!/bin/bash
#Asshume heasarc!

columns=(`flcol logxi_0.0/xout_abund1.fits[1] nlist=1 | grep -v ___`)
for x in logxi*; do 
    echo "-I- Working $x"
    n=$(echo $x/*abund*)
    ntable=1
    cols=()
    for column in ${columns[*]}; do
        cols+=($column)
        if [[ ${#cols[*]} -lt 10 ]]; then continue; fi
        if [[ $ntable -eq 1 ]]; then
            echo "Next: $x" >> table$ntable
        else
            echo "" >> table$ntable
        fi
        fdump $n[1] STDOUT columns="${cols[*]}" \
              rows=1 prhead=no showrow=no showunit=no \
              align=yes pagewidth=256 page=no wrap=no >> table$ntable
        ((++ntable))
        cols=()
    done
    if [[ ${#cols[*]} -gt 0 ]]; then 
        echo "" >> table$ntable
        fdump $n[1] STDOUT columns="${cols[*]}" \
              rows=1 prhead=no showrow=no showunit=no \
              align=yes pagewidth=256 page=no wrap=no >> table$ntable
    fi
done

tables=(`ls table* | sort -rV`)
for table in $(ls table* | sort -rV); do
    if [[ $table == ${tables[0]} ]]; then
        cmd="cat $table"
    else
        cmd="$cmd | paste $table -"
    fi
done
echo "-I- Running:"
echo "$cmd > xitable.dat"
eval $cmd > xitable.dat
rm table*

sed -i 's|\s\+| |g' xitable.dat
sed -i 's|^ ||g' xitable.dat
sed -i '/^\s*$/d' xitable.dat
$BASH_SOURCE/fixtable.py 
mv res.dat xitable.dat

