#!/bin/bash
# Judge the real GAUGE continuation clips with the exact midq setup (follow-up to #2905).
W=/home/nail/other_work/sclaw/swarm-work/rog-cc; J=$W/cosmos-swarm/tools/hue_judge; Q=$W/cosmos-swarm/work/rog-cc/midq/midq_questions.json
cd $W/realref
args=(); for f in clips/*.mp4; do args+=(--clip "$f" --sample midq_combo); done
flock /tmp/rogcc_gpu.lock python3 $J/hue_judge.py --questions $Q --offsets 0,0.5 --out judge.json "${args[@]}"
echo "judge rc=$? $(date -u)"
