#!/bin/bash
# t336b readout on box-made clips (same steps as t336b_wait.sh tail + t336b_post.sh + t336b_post2.sh)
W=/home/nail/other_work/sclaw/swarm-work/dk1; R=$W/cosmos-swarm
ls $W/t336b/clips/t336b_*.mp4 | wc -l; mkdir -p $W/t336b/out
cd $R && python3 -I work/dk1/t336_region/analyze_b.py $W/t336b/clips $W/t336b/out 2>&1 | tail -20; echo PERIOD_B_DONE
until ! kill -0 3473286 2>/dev/null; do sleep 30; done
until [ $(nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits | head -1) -lt 1500 ]; do sleep 20; done
cd $R/tools/nv_scoreboard && $W/venv_dover/bin/python score.py $W/t336b/clips --dover_dir $W/DOVER --device cuda --dover_reps 3 --out $W/t336b/out/scores_t336b.json 2>&1 | tail -2
cd $R && python3 -I work/dk1/t336_region/quality_b.py $W/t336b/out/scores_t336b.json $W/t336b/out/quality_b.json; echo T336B_DONE
cd $W && python3 -I $R/work/dk2/t337c/outside.py $R/work/dk1/t336_region/boxes.json t336b/out/outside_t336b.json t336b/clips/t336b_*.mp4 2>&1 | tail -3
for s in 12 17 18 19; do python3 -I strips.py t336b/out/strip_real_$s.jpg rep6767/gen/t276_real_${s}_plain_s*.mp4 rep6767/gen/t276_real_${s}_nphys_s1.mp4 t336b/clips/t336b_real_${s}_*.mp4; done; echo POST_B_DONE
cd $R/tools/nv_scoreboard && $W/venv_dover/bin/python score.py $W/t336b/clips/t336b_*.mp4 --dover_dir $W/DOVER --device cuda --dover_reps 10 --per_clip_seed --out $W/t336b/out/scores_t336b_pcs10.json 2>&1 | tail -2
cd $R && python3 -I work/dk1/t336_region/quality_b2.py $W/t336b/out/scores_t336b_pcs10.json $W/t336b/out_refs_pcs10.json $W/t336b/out/quality_b2.json; echo POST2_DONE
