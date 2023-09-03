#!/bin/bash
# =========================================================================
# Get summary of ALICE runs from BKP
#
# Author: R.Divia`, CERN/ALICE
# Version: v1 13/06/2023
# =========================================================================
# Temporary files used to cache the detailed data
DATA="/tmp/`basename $0`.$$"

# List of ALICE detectors
# DETS="CPV EMC FDD FT0 FV0 HMP ITS MCH MFT MID PHS TOF TPC TRD TST ZDC"
DETS="CPV EMC FDD FT0 FV0 HMP ITS MCH MFT MID PHS TOF TPC TRD ZDC"

# Separator for the CSV output
SEP_CSV=","
SEP="|"

# =========================================================================
usage() {
   printf "Usage: %s [OPTION...]\n" "`basename $0`"
   printf "   -d     \tDebug\n"
   printf "   -f Date\tStarting date/time (default: 7 days ago)\n"
   printf "   -t Date\tEnding date/time (default: NOW)\n"
   printf "   -F FillNo\tNumber of the fill(s) (comma-separated) (disables date/time-based selection)\n"
   printf "   -D seconds\tMinimum run duration (in seconds)\n"
   printf "   -s selection\tfields selection (comma-separated)\n"
}

from="-7 days"
to="now"
dbg=0
minDuration=0
fillNo=0
selection=""
while getopts f:t:F:D:s:dh? flag; do
   case "${flag}" in
      f) from="${OPTARG}";;
      t) to="${OPTARG}";;
      F) fillNo="${OPTARG}";;
      D) minDuration="${OPTARG}";;
      d) dbg=1;;
      s) selection="${OPTARG}";;
      h|*) usage; exit 1;;
   esac
done

# Selection by FILL NUMBER overrides any time-based selection
if (( fillNo > 0 )); then
   from=""
   to=""
fi

if (( dbg )); then
   printf "`basename $0` starting\t"
   printf "\tfrom:'%s' to:'%s' fillNo:'%d'\n" "${from}" "${to}" "${fillNo}"
fi >&2

O=""
if [ "${from}${to}" ]; then
   O="filter[o2start][from]=`date --date=\"${from}\" +%s`000&filter[o2start][to]=`date --date=\"${to}\" +%s`999"
fi

if (( fillNo > 0 )); then
   O="filter[fillNumbers]=${fillNo}"   
fi

URL="https://ali-bookkeeping.cern.ch/api/runs?$O&page[offset]=0&page[limit]=999"
echo $URL
(( dbg )) && printf "URL:\"%s\"\n" "${URL}" >&2

wget -q "${URL}" -O ${DATA} --no-check-certificate

LINE+=$(printf "Run Number${SEP}")
LINE+=$(printf "O2 start${SEP}")
LINE+=$(printf "O2 end${SEP}")
LINE+=$(printf "Start time${SEP}")
LINE+=$(printf "End time${SEP}")
LINE+=$(printf "TRG start${SEP}")
LINE+=$(printf "TRG end${SEP}")
LINE+=$(printf "Run duration${SEP}")
LINE+=$(printf "Env ID${SEP}")
LINE+=$(printf "Run type${SEP}")
LINE+=$(printf "Definition${SEP}")
LINE+=$(printf "Run quality${SEP}")
LINE+=$(printf "Fill #${SEP}")
LINE+=$(printf "Stable Beams duration${SEP}")
LINE+=$(printf "Period${SEP}")
LINE+=$(printf "PDP workflow parameters${SEP}")
LINE+=$(printf "EOR reasons(s)${SEP}")
LINE+=$(printf "# Detectors${SEP}")
LINE+=$(printf "# FLPs${SEP}")
LINE+=$(printf "# EPNs${SEP}")
LINE+=$(printf "TF File Size${SEP}")
LINE+=$(printf "CTF File Size${SEP}")
for d in ${DETS}; do
   LINE+=$(printf "$d IN${SEP}")
done
LINE+=$(printf "\n")

if [ x"$selection" = "x" ]; then
    echo $LINE | tr "$SEP" "${SEP_CSV}"
else
    echo $LINE | cut -d"$SEP" -f $selection | tr "$SEP" "${SEP_CSV}"
fi

RUNS="`jq .data[].runNumber ${DATA} | tac`"
NRUNS=$(( `echo "${RUNS}" | wc -l` ))
if (( NRUNS > 998 )); then
   echo "Too many runs, please reduce the time range" >&2
   exit 1
fi

sanitize() {
   printf "%s" "$*" | tr "${SEP}" "_"
}

isNum() {
  [ "$*" != "" -a "${*//[0-9]/}" = "" ]
}

timeToDate() {
   local t=$(($* / 1000))
   (( t > 0 )) && printf "%s" "`date --date "@$t" +'%m/%d/%Y %T'`"
   printf "${SEP}"
}

printNum() {
   [ "$*" != "null" ] && printf "%s" "$*" | tr -d "\""
   [ "$*" = "null" ] && printf "0"
   printf "${SEP}"
}

printStr() {
   printf "%s" "$*" | tr -d "\""
   printf "${SEP}"
}

n=${NRUNS}
for runNumber in ${RUNS}; do
   n=$((n-1))
   
   (( dbg )) && echo "=============================================================================" >&2
   (( dbg )) && jq .data[$n] ${DATA} >&2
   
   if (( `jq .data[$n].runNumber ${DATA}` != runNumber )); then
     printf "Run number mismatch, fatal error\n" >&2
     exit 1
   fi

   nDetectors=$(( `jq .data[$n].nDetectors ${DATA}` ))
   
   runDuration=$(( `jq .data[$n].runDuration ${DATA}` / 1000 ))
   
#printf "nDetectors:%d runDuration:%d\n" ${nDetectors} ${runDuration} >&2
   (( nDetectors < 2 )) && continue
   
   (( runDuration < minDuration )) && continue

#printf "Passed\n" >&2

   LINE=""
   
   LINE+=$(printf "${runNumber}${SEP}")
     
   LINE+=$(timeToDate `jq .data[$n].timeO2Start ${DATA}`)
   LINE+=$(timeToDate `jq .data[$n].timeO2End ${DATA}`)
     
   LINE+=$(timeToDate `jq .data[$n].startTime ${DATA}`)
   LINE+=$(timeToDate `jq .data[$n].endTime ${DATA}`)
     
   LINE+=$(timeToDate `jq .data[$n].timeTrgStart ${DATA}`)
   LINE+=$(timeToDate `jq .data[$n].timeTrgEnd ${DATA}`)
     
   #(( runDuration > 0 )) && printf "%d" ${runDuration}
   LINE+=$(printf '%02d:%02d:%02d' $((runDuration/3600)) $((runDuration%3600/60)) $((runDuration%60)))
   LINE+=$(printf "${SEP}")
     
   #printf "%s${SEP}" "`jq .data[$n].environmentId ${DATA}`"
   LINE+=$(printStr `jq .data[$n].environmentId ${DATA}`)
     
   #printf "%s${SEP}" "`jq .data[$n].runType.name ${DATA}`"
   LINE+=$(printStr `jq .data[$n].runType.name ${DATA}`)
     
   #printf "%s${SEP}" "`jq .data[$n].definition ${DATA}`"
   LINE+=$(printStr `jq .data[$n].definition ${DATA}`)
     
   #printf "%s${SEP}" "`jq .data[$n].runQuality ${DATA}`"
   LINE+=$(printStr `jq .data[$n].runQuality ${DATA}`)
     
   LINE+=$(printNum `jq .data[$n].fillNumber ${DATA}`)
     
   LINE+=$(printNum `jq .data[$n].lhcFill.stableBeamsDuration ${DATA}`)
   stableBeamsDuration=$(( `jq .data[$n].stableBeamsDuration ${DATA}` / 1000 ))
   #printf '%02d:%02d:%02d' $((stableBeamsDuration/3600)) $((stableBeamsDuration%3600/60)) $((stableBeamsDuration%60))
   #printf "${SEP}"
     
   #printf "%s${SEP}" "`jq .data[$n].lhcPeriod ${DATA}`"
   LINE+=$(printStr `jq .data[$n].lhcPeriod ${DATA}`)
     
   LINE+=$(printf "%s${SEP}" "`jq .data[$n].pdpWorkflowParameters ${DATA}`")
     
   eorReasons="`jq .data[$n].eorReasons ${DATA}`"
   LINE+=$(printf "\"%s\"${SEP}" "`sanitize ${eorReasons}`")

   LINE+=$(printf "%d${SEP}" ${nDetectors})
     
   #printf "%d${SEP}" `jq .data[$n].nFlps ${DATA}`
   LINE+=$(printNum `jq .data[$n].nFlps ${DATA}`)
     
   #printf "%d${SEP}" `jq .data[$n].nEpns ${DATA}`
   LINE+=$(printNum `jq .data[$n].nEpns ${DATA}`)
     
   LINE+=$(printNum `jq .data[$n].tfFileSize ${DATA}`)
     
   LINE+=$(printNum `jq .data[$n].ctfFileSize ${DATA}`)
     
   detectors="`jq .data[$n].detectors ${DATA}`"
   for d in ${DETS}; do
     if echo "${detectors}" | grep -qn $d; then
       LINE+=$(printf "1${SEP}")
     else
       LINE+=$(printf "0${SEP}")
     fi
   done

   LINE+=$(printf "\n")

   if [ x"$selection" = "x" ]; then
       echo $LINE | tr "$SEP" "${SEP_CSV}"
   else
       echo $LINE | cut -d"$SEP" -f $selection | tr "$SEP" "${SEP_CSV}"
   fi
   
done

#rm -f ${DATA}
