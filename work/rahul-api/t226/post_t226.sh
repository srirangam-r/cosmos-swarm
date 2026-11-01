#!/bin/bash
# After stage_t226.sh (PID $STAGE_PID) exits: frozen measure_t226.py on all 72 clips in 6 parallel shards -> measures.json,
# then frozen analyze_t226.py -> results.json (P primaries; F/H dy tables are 'failed QC' per Amendment 6). No key access.
cd /home/sha/swarm-work/rahul-api/cosmos-swarm/work/rahul-api/t226
PY=/home/sha/swarm-work/rahul-api/.venv/bin/python; W=/home/sha/swarm-work/rahul-api/t226_scratch/shards
while kill -0 "${STAGE_PID:-0}" 2>/dev/null; do sleep 30; done
n=$(ls clips/t226_*.mp4 | wc -l); echo "$(date -u +%H:%M:%S) stage done; $n clips"
[ "$n" -lt 72 ] && { echo "only $n clips; stop"; exit 1; }
rm -rf $W; mkdir -p $W; i=0
for p in $(ls clips/t226_*.mp4 | sort); do d=$W/s$((i % 6)); mkdir -p $d; ln -s $(readlink -f $p) $d/; i=$((i+1)); done
for k in 0 1 2 3 4 5; do $PY measure_t226.py $W/s$k $W/m$k.json > $W/m$k.log 2>&1 & done; wait
$PY - <<'PY'
import json, glob
M = {}
for f in sorted(glob.glob('/home/sha/swarm-work/rahul-api/t226_scratch/shards/m*.json')): M.update(json.load(open(f)))
json.dump(M, open('measures.json', 'w'), indent=1); print(len(M), 'clips measured')
PY
$PY analyze_t226.py measures.json results.json > analyze_t226.log 2>&1; $PY explore_t226.py measures.json explore_results.json > explore_t226.log 2>&1
echo "$(date -u +%H:%M:%S) analyze done"
