#!/bin/bash
# dk2: rescore t276 refs (plain/nphys/nphys_x17; real_09/12/17/18/19) on dk2's rig with --per_clip_seed --dover_reps 10,
# same command as wait3.sh uses for arms. Waits for dk1's unflocked scorer (PID 3473287) so two DOVERs don't OOM the 8 GB 4060.
cd /home/nail/other_work/sclaw/swarm-work/dk2
while kill -0 3473287 2>/dev/null; do sleep 30; done
for sc in 12 17 18 19 09; do for a in plain_s1 plain_s2 plain_s3 nphys_s1 nphys_s2 nphys_s3 nphys_x17_s1; do
  n=t276_real_${sc}_$a; f=t319/gen/$n.mp4; [ -e $f ] || continue
  [ -s t337c/refs_sc/$n.json ] || flock /tmp/dover_4060.lock t319/venv_gpu/bin/python -I cosmos-swarm/tools/nv_scoreboard/score.py $f --dover_dir t319/ext/DOVER --device cuda --dover_reps 10 --per_clip_seed --out t337c/refs_sc/$n.json > t337c/refs_sc/$n.log 2>&1
done; done
python3 -c "import json,glob; d={}; [d.update(json.load(open(p))) for p in sorted(glob.glob('t337c/refs_sc/*.json'))]; json.dump(d,open('t337c/refs_pcs10.json','w'),indent=1); print('refs',len(d))"
echo REFS_DONE; date -u
