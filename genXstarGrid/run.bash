#!/bin/bash
#Assume heasarc!
sdir=$(dirname $(realpath $BASH_SOURCE))
source ~/sources/get_params.bash
if [ -n "${flags[h]}" ]; then
    echo "-I- Usage genXstarGrid [-h] [-p] [xstar_flag=val ...] <xilist | -t | -s [xout_spect1.fits]>".
    echo "-I- Run in directory containing parameter.dat. Use -p flag to print parameter names."
    echo "-I- If one than more core available, uses all except 1, unless use_procs=<num> definde."
    echo "-I- If -t is specified generate a list of xi-temperature. Must be in directory containing logxi_ folders."
    echo "-I- If -s is specified Extract the spectrum into a text file."
    echo "-I- You can use a=b to set xstar hidden parameter a to b. Note by default niter=99."
    exit 0
fi
xis="${rest[@]}"
if [ -n "${flags[p]}" ]; then
    cat $sdir/parameter.names
    exit 0
fi
if [ -s ${flags[s]} ]; then
    [ -z $xis ] && xis=xout_spect1.fits
    ftlist ${xis}[2] columns=energy,emit_outward rownum=no colheader=no T > ${xis%.*}
    exit 1
fi
if [ -n "${flags[t]}" ]; then
    grep -FA2 'log(t)' logxi_*/xout_step.log | awk '{if(NR%4==3) {match($1,/logxi_([^/]*)/,a); print a[1]" "$8}}' | sort -n
    exit 0
fi
if [ ${#xis[@]} -eq 0 ]; then
    echo "-E- Must provide at least one xi for calculation."
    exit 1
fi
if [[ ! -f parameter.dat ]]; then
    echo -E- Expecting parameter.dat in working directory to generate XSTAR data. Check script directory for parameter names.
    exit 1
fi

unset params[use_procs]
[ -z "$use_procs" ] && use_procs=$(($(nproc)-1))
[ "$use_procs" -eq 0 ]  && use_procs=1
[ -z "${params[niter]}" ] && params[niter]=99
echo "PARAMS: ${params[*]}"

xflags=""
for flag in ${!params[*]}; do
    xflags="$xflags $flag=${params[$flag]}" 
done

procs=$use_procs
current_pids=()
for x in ${*}; do
    if [[ $procs > 0 ]]; then
        mkdir -p logxi_$x
        cd logxi_$x 
        cp ../parameter.dat .
        sed -i "7s/^/..\//" parameter.dat
        sed -i "12s/.*/$x/" parameter.dat 
        xstar $xflags < parameter.dat &
        current_pids=($current_pids $!)
        cd ..
        ((procs-=1))
    else
        #Slower since you wait for all processes, instead of continuing by ones.
        for pid in ${current_pids[*]}; do
            wait $pid
        done
        procs=$use_procs
        current_pids=()
    fi
done
for pid in ${current_pids[*]}; do
    wait $pid
done

$sdir/makeTable.bash 

