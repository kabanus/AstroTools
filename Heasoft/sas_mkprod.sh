#!/bin/bash

help_msg="-I- Usage: sas_mkprod.sh --product=[lightcurve] [--binsize=<int>] [--source=<xxx>] device observation-dir [observation-dir ...]"

printExit () {
    printf -- '-E- %s\n' "$1"
    exit 1
}

getFirstSource () {
    obsdir=$1
    glob=$2
    # shellcheck disable=SC2086
    read -ra files < <(echo "$obsdir"/$glob | sort -V)
    first=${files[0]}
    echo "${first:((${#first}-7)):3}"
}

if [ -z "$LHEASOFT" ]; then
    printExit "-E- This script must be run within a HEADAS environment. Please run heainit."
fi

source_num="first"
. ~/sources/get_options.bash
[ $# -lt 2 ] || [ "${OPTS[h]}" ] || [ "${OPTS[help]}" ] && printExit "$help_msg"
device=$1
binsize=${OPTS[binsize]:-100}
if [ -n "${OPTS[source]}" ]; then
    source_num=$(printf "%03d" "${OPTS[source]}" 2> /dev/null)
    [ "$source_num" = "000" ] || [ ${#source_num} -gt 4 ] && printExit "-E- Source number must be an integer < 999 ."
fi
case "$device" in RGS) ;; PN) ;; MOS) ;; *)
        printExit "-E- Device $device illegal. Must be one of RGS, PN, MOS."
esac

declare -A failures
for obsdir in "${@:2}"; do
    export SAS_ODF=$obsdir/odf
    export SAS_CCF_PATH=$obsdir/ccf
    export SAS_CCF=$obsdir/data/ccf.cif
    PPS=$obsdir/pps
    OUT=$obsdir/products

    . "$SASDIR/setsas.sh"

    if [ ! -f "$SAS_CCF" ]; then
        printf -- '-I- Generating CIF\n'
        cifbuild fullpath=yes
    fi

    printf -- '-I- Ingesting ODF\n'
    odfingest odfdir="$SAS_ODF" outdir="$SAS_ODF"

    mkdir -p "$OUT"
    case "${OPTS[product]}" in
        lightcurve)
            glob="*${device}S*EVLI*"
            [ "$source_num" = "first" ] && source_num=$(getFirstSource "$PPS" "$glob")
            glob=$PPS/$glob${source_num}.FTZ
            # shellcheck disable=SC2206
            eventlist=($glob)
            if [ ${#eventlist[@]} -gt 1 ]; then
                failures+=(["$obsdir"]="Found multiple matches for $glob: ${eventlist[*]}")
                continue
            fi

            eventfile=${eventlist[0]}
            if ! [ -f "$eventfile" ]; then
                failures+=(["$obsdir"]="Could not find file matching $PPS/$glob${source_num}.FTZ")
                continue 
            fi
            echo "-I- Using event file: ${eventfile}"

            [ ${#eventlist[@]} -gt 1 ] && printExit "-E- Found no or multiple event files: ${eventlist[*]}"
            events="${eventlist[0]}"
            evselect table="$events":EVENTS withrateset=yes rateset="$OUT/${device}LightCurve.fits" maketimecolumn=yes timecolumn=TIME timebinsize="$binsize" makeratecolumn=yes
            ftlist "$OUT/${device}LightCurve.fits"[RATE] columns=TIME,RATE,ERROR colheader=no rownum=no T > "$OUT/PNLightCurve.dat"
            ;;
        *)
            printExit "No such product '${OPTS[product]}', please select one of lightcurve, ."
    esac
done

[ ${#failures[@]} -gt 0 ] && echo "-E- Failures:"
for failed_obs in "${!failures[@]}"; do
    echo "    $failed_obs ${failures[$failed_obs]}"
done
