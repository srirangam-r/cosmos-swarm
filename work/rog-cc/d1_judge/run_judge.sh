#!/bin/bash
# Judge the Deliverable-1 recipe clips + real input control (PREREG A3). Shares the GPU lock with the task-24 watchers.
W=/home/nail/other_work/sclaw/swarm-work/rog-cc
J=$W/cosmos-swarm/tools/hue_judge
args=()
for f in $W/d1_judge/clips/box_{ctrl,mid}_b{1,2}_noneg_s{1,2,3,4}.mp4 $W/rev1616_ctrl/clips/real{ball,mid}_{1,2}.mp4; do
  args+=(--clip "$f" --sample gauge_ball); done
flock /tmp/rogcc_gpu.lock python3 $J/hue_judge.py --questions $J/gauge_questions.json --offsets 0,0.5 --out $W/d1_judge/judge.json "${args[@]}"
