#!/bin/bash
# ro-1 task22: score each v7 (REC/RECT) and v8 (prompt-switch) clip with nv_scoreboard (CPU) as it lands,
# plus late-motion strips. Stops when chain_v8 (826016, which waits on v7) is done and all clips are scored.
cd /home/rohith/swarm-work/ro-1
export TORCH_HOME=/home/rohith/swarm-work/ro-1/scoreboard/torch_home OMP_NUM_THREADS=16 CUDA_VISIBLE_DEVICES=""
while true; do
  for f in fps_sweep/out_cause7/*.mp4 fps_sweep/out_cause8/*.mp4; do
    [ -f "$f" ] || continue
    b=$(basename $f .mp4); [ -f nv_v7/$b.score.json ] && continue
    nice -n 10 py312/bin/python -I cosmos-swarm/tools/nv_scoreboard/score.py $f --dover_dir scoreboard/DOVER --device cpu --dover_reps 3 --out nv_v7/$b.score.json >> nv_v7/score.log 2>&1
    py312/bin/python -I cause_v5/strip.py $f nv_v7/$b.strip.jpg >> nv_v7/strip.log 2>&1
  done
  if ! kill -0 826016 2>/dev/null; then
    n=$(ls fps_sweep/out_cause7/*.mp4 fps_sweep/out_cause8/*.mp4 2>/dev/null | wc -l); s=$(ls nv_v7/*.score.json 2>/dev/null | wc -l)
    [ "$s" -ge "$n" ] && break
  fi
  sleep 30
done
echo DONE >> nv_v7/score.log
