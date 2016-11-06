#!/bin/bash

for elem in */; do
    for ion in $elem/*/; do
        lines=$(($(cat `find $ion -name "A*" -o -name "lines*"` | wc -l)-1))
        res=$(grep -e "^$lines " massandedge.data | wc -l)
        echo "$ion has $lines lines and found $res"
    done
done

