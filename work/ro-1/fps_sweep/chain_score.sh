#!/bin/bash
# ro-1 task 22: after the sweep + measurement chain (PID 435799) finishes, score every clip on the NVIDIA scoreboard (CPU, nice).
# (1) at conditioned fps -> meas/nv_scores.json; (2) fps-12 clips re-labelled fps 24 (the 'condition 12, play 24' recipe) -> meas/nv_scores_play24.json
cd /home/rohith/swarm-work/ro-1/fps_sweep
while kill -0 435799 2>/dev/null; do sleep 30; done
export TORCH_HOME=/home/rohith/swarm-work/ro-1/scoreboard/torch_home OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 CUDA_VISIBLE_DEVICES=""
PY=/home/rohith/swarm-work/ro-1/py312/bin/python; S=/home/rohith/swarm-work/ro-1/cosmos-swarm/tools/nv_scoreboard/score.py; D=/home/rohith/swarm-work/ro-1/scoreboard/DOVER
nice -n 10 $PY -I $S out/*.mp4 --dover_dir $D --device cpu --dover_reps 3 --out meas/nv_scores.json > meas/nv_scores.log 2>&1
mkdir -p out_play24
for j in out/*fps12*.json; do b=$(basename $j .json); ln -sf ../out/$b.mp4 out_play24/${b}_play24.mp4
  $PY -I -c "import json,sys;d=json.load(open(sys.argv[1]));d['fps_cond']=d['fps'];d['fps']=24;d['name']+='_play24';json.dump(d,open(sys.argv[2],'w'),indent=1)" $j out_play24/${b}_play24.json; done
nice -n 10 $PY -I $S out_play24/*.mp4 --dover_dir $D --device cpu --dover_reps 3 --no_dover --out meas/nv_scores_play24.json > meas/nv_scores_play24.log 2>&1
