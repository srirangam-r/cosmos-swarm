#!/bin/bash
# Amendment 3 (rahul-api-2): after auto226.sh finishes, re-run the frozen analyze on the a6k seeds only (s101-104).
cd /home/sha/swarm-work/rahul-api-2 || exit 1
PY=.venv/bin/python; T=cosmos-swarm/work/rahul-api-2/t226_pend
for i in $(seq 1 150); do [ -f t226/DONE ] && break; sleep 60; done
[ -f t226/DONE ] || { echo "no DONE"; exit 2; }
$PY -I $T/subset_seeds.py t226/p_meas.json t226/p_meas_a6k.json 101,102,103,104
$PY -I $T/readout.py analyze t226/p_meas_a6k.json t226/p_result_a6k.json --arms base,neutral,still,fast \
  --contrasts still:neutral,fast:neutral,base:neutral,still:base,fast:base
date -u > t226/DONE_a6k; echo "A6K DONE"
