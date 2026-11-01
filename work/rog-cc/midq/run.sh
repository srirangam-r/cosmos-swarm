#!/bin/bash
# usage: run.sh <clipdir> <ctldir> <out.json>  (originals first, then controls; one judge pass, combined question file)
W=/home/nail/other_work/sclaw/swarm-work/rog-cc; J=$W/cosmos-swarm/tools/hue_judge; Q=$W/cosmos-swarm/work/rog-cc/midq/midq_questions.json
args=(); for f in "$1"/*.mp4 "$2"/static_*.mp4 "$2"/trunc36_*.mp4; do args+=(--clip "$f" --sample midq_combo); done
flock /tmp/rogcc_gpu.lock python3 $J/hue_judge.py --questions $Q --offsets 0,0.5 --out "$3" "${args[@]}"
