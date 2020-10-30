#!/bin/bash
files=(*/products/PNLightCurve.dat)
amount=${#files[@]}
perrow=3
maxrows=3
rows=$((amount/perrow))
[ $((rows*perrow)) -lt "$amount" ] && ((rows++))
if [ "$rows" -gt $maxrows ]; then
    rows=$maxrows
    amount=$((maxrows*perrow))
fi
cmd="xmgrace -pexec 'arrange($rows,$perrow,.1,.0,.15)'"
i=0
for f in "${files[@]}"; do
    cmd+=" -settype xydy"
    cmd+=" -graph $i $f"
    cmd+=" -pexec 'world ymin 0; world ymax 150'"
    cmd+=" -pexec 'world ymax 150'"
    cmd+=" -pexec 'xaxis ticklabel formula \"\$t-421974000\"'"
    cmd+=" -pexec 'yaxis tick major 50; yaxis tick minor 10'"
    [ $((i % perrow)) -gt 0 ] && cmd+=" -pexec 'yaxis ticklabel off'"
    ((i++))
    [ "$i" -eq "$amount" ] && break
done
eval "$cmd"
