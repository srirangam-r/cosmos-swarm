#!/bin/bash
# rahul-api-2: wait for all 24 t226_P clips, then run the frozen pendulum readout (primary + rodtrack secondary).
# Log: t226/auto226.log. Outputs: t226/p_meas.json, p_result.json, rt_P.json, rt_qc/, p_rodsec.json, DONE marker.
cd /home/sha/swarm-work/rahul-api-2 || exit 1
PY=.venv/bin/python
T=cosmos-swarm/work/rahul-api-2/t226_pend
for i in $(seq 1 120); do
  python3 -I $T/fetch_p.py t226/clips
  n=$(ls t226/clips/t226_P_*.mp4 2>/dev/null | wc -l)
  echo "$(date -u +%H:%M:%S) have $n/24"
  [ "$n" -ge 24 ] && break
  sleep 120
done
n=$(ls t226/clips/t226_P_*.mp4 2>/dev/null | wc -l)
[ "$n" -lt 24 ] && { echo "TIMEOUT with $n/24"; exit 2; }
sha256sum t226/clips/t226_P_*.mp4 > t226/clips_SHA256SUMS
$PY -I $T/readout.py measure t226/clips t226/p_meas.json --glob 't226_P_*.mp4'
$PY -I $T/readout.py analyze t226/p_meas.json t226/p_result.json --arms base,neutral,still,fast \
  --contrasts still:neutral,fast:neutral,base:neutral,still:base,fast:base
mkdir -p t226/rt_qc
$PY -I cosmos-swarm/work/kiro-1/t191/rodtrack.py t226/rt_P.json t226/rt_qc t226/clips/t226_P_*.mp4
$PY -I $T/rodsec.py t226/rt_P.json t226/p_meas.json t226/p_rodsec.json \
  --contrasts still:neutral,fast:neutral,base:neutral,still:base,fast:base
date -u > t226/DONE
echo "ALL DONE"
