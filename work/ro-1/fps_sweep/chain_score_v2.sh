#!/bin/bash
# ro-1 task 22 (v2, after codex-1 score.py fix 2e8f659 which scores at CONTAINER fps):
# (1) all clips at conditioned fps -> meas/nv_scores.json
# (2) fps-12 clips losslessly remuxed to a 24-fps container (setts bsf, pixel-identical) = 'condition 12, play 24' recipe -> meas/nv_scores_play24.json
cd /home/rohith/swarm-work/ro-1/fps_sweep
while kill -0 435799 2>/dev/null; do sleep 30; done
export TORCH_HOME=/home/rohith/swarm-work/ro-1/scoreboard/torch_home OMP_NUM_THREADS=12 MKL_NUM_THREADS=12 CUDA_VISIBLE_DEVICES=""
PY=/home/rohith/swarm-work/ro-1/py312/bin/python; S=/home/rohith/swarm-work/ro-1/cosmos-swarm/tools/nv_scoreboard/score.py; D=/home/rohith/swarm-work/ro-1/scoreboard/DOVER
FF=/home/rohith/swarm-work/ro-1/py312/lib/python3.12/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2
nice -n 10 $PY -I $S out/*.mp4 --dover_dir $D --device cpu --dover_reps 3 --out meas/nv_scores.json > meas/nv_scores.log 2>&1
rm -rf out_play24; mkdir -p out_play24
for j in out/*fps12*.json; do b=$(basename $j .json)
  $FF -y -v error -i out/$b.mp4 -c copy -bsf:v "setts=ts=TS/2:duration=DURATION/2" -video_track_timescale 24 out_play24/${b}_play24.mp4
  $PY -I -c "import json,sys;d=json.load(open(sys.argv[1]));d['cond_fps']=d['fps'];d['fps_cond']=d['fps'];d['play_fps']=24;d['fps']=24;d['name']+='_play24';d['remux']='setts ts/2 lossless';json.dump(d,open(sys.argv[2],'w'),indent=1)" $j out_play24/${b}_play24.json; done
nice -n 10 $PY -I $S out_play24/*.mp4 --dover_dir $D --device cpu --dover_reps 3 --out meas/nv_scores_play24.json > meas/nv_scores_play24.log 2>&1
