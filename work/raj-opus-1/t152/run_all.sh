#!/bin/bash
# waits for venv + ckpt, then runs Visual Chronometer on reference clips and task-139 clips
E=/home/nail/swarm-work/raj-opus-1/ext; R=/home/nail/swarm-work/raj-opus-1/cosmos-swarm; O=/home/nail/swarm-work/raj-opus-1/t152
until grep -q VENV_OK $E/venv_install.log && [ "$(stat -c %s $E/vc/inference/ckpts/vc_common_10_60fps.ckpt)" = 1846470358 ]; do
  grep -qi "error" $E/venv_install.log && { echo VENV_FAIL; exit 1; }; sleep 10; done
echo "ready $(date -u +%T)"
PY=$E/venv/bin/python
$PY -I $R/work/raj-opus-1/t152/run_vc.py $E/vc/inference $O/vc_ref.json \
  $E/vc/inference/demo_videos/gymnast_24fps.mp4 $E/vc/inference/demo_videos/gymnast_30fps.mp4 $E/vc/inference/demo_videos/gymnast_50fps.mp4 \
  $R/work/agy-4/task72_score_review/real_control_clips/real_ball_{1,2,3,4}_f0_93f.mp4 \
  $R/work/rog-cc/ratio_audit/realref_clips/real_ball1_dd33_93f.mp4 $R/work/rog-cc/ratio_audit/realref_clips/real_ball2_dd35_93f.mp4 $R/work/rog-cc/ratio_audit/realref_clips/real_ball3_dd34_93f.mp4
echo "ref done $(date -u +%T)"
$PY -I $R/work/raj-opus-1/t152/run_vc.py $E/vc/inference $O/vc_t139.json /home/nail/swarm-work/raj-opus-1/t139/clips/t139_*.mp4
echo "t139 done $(date -u +%T)"
