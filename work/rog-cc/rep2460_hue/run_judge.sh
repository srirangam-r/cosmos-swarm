#!/bin/bash
# HUE plausibility judge (scoreboard item 3) on F vs QT timed-settle clips (#2460 replications). Usage: run_judge.sh <clip_dir> <out.json>
# Same judge/questions/offsets as the D1 numbers (#1871). Arm key is applied only after judging (analyze step).
W=/home/nail/other_work/sclaw/swarm-work/rog-cc
J=$W/cosmos-swarm/tools/hue_judge
args=(); for f in "$1"/*.mp4; do args+=(--clip "$f" --sample gauge_ball); done
flock /tmp/rogcc_gpu.lock python3 $J/hue_judge.py --questions $J/gauge_questions.json --offsets 0,0.5 --out "$2" "${args[@]}"
