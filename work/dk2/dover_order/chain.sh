#!/bin/bash
cd /home/nail/other_work/sclaw/swarm-work/dk2
P=t319/venv_gpu/bin/python; S=cosmos-swarm/tools/nv_scoreboard/score.py; B="--no_dd --dover_dir t319/ext/DOVER --device cuda"
rm -f drift/t336_r20.json drift/pcs_*.json
$P -I $S rev6747/dk1clips/t336_real_12_reg*.mp4 $B --dover_reps 20 --per_clip_seed --out drift/t336_r20.json > drift/t336_r20.log 2>&1
$P -I $S t319/gen/t276_real_12_plain_s1.mp4 t319/gen/t276_real_17_plain_s1.mp4 $B --dover_reps 3 --per_clip_seed --out drift/pcs_fwd.json > drift/pcs_fwd.log 2>&1
$P -I $S t319/gen/t276_real_17_plain_s1.mp4 t319/gen/t276_real_12_plain_s1.mp4 $B --dover_reps 3 --per_clip_seed --out drift/pcs_rev.json > drift/pcs_rev.log 2>&1
$P -I $S t319/gen/t276_real_12_plain_s[123].mp4 t319/gen/t276_real_12_nphys_s[123].mp4 $B --dover_reps 20 --per_clip_seed --out drift/ref12_r20.json > drift/ref12_r20.log 2>&1
touch drift/CHAIN_DONE
