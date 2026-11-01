#!/bin/bash
# Blind DOVER(reps3, seed0)+DD scoring of codex-api-2 task-145 opaque package (repo 38f0891, SHA-verified) at their request #3491.
cd /home/nail/other_work/sclaw/swarm-work/rog-cc/t145_dover
LOCK=/tmp/rogcc_gpu.lock
DOVER=/home/nail/other_work/sclaw/swarm-work/rog-cc/ext/DOVER
echo START $(date -u)
flock "$LOCK" python3 /home/nail/other_work/sclaw/swarm-work/rog-cc/cosmos-swarm/tools/nv_scoreboard/score.py clips/*.mp4 --dover_dir "$DOVER" --device cuda --dover_reps 3 --seed 0 --out nv_t145_blind.json
echo "DONE rc=$? $(date -u)"
