#!/bin/bash
# eye-QC strips (pendulum crop, every 6th frame) of every 'ok' clip, grouped per input; post-hoc QC, not part of the decision
cd /home/sha/swarm-work/rahul-api-2/t257
PY=/home/sha/swarm-work/rahul-api-2/.venv/bin/python
for inp in pend10 pend11 pend14; do
  clips=$($PY -I -c "
import json
m=json.load(open('meas.json'))
print(' '.join('clips/'+r['clip'] for r in m if r['input']=='$inp' and r['pend'].get('flag')=='ok'))")
  [ -n "$clips" ] && $PY -I ../t220/code/strip.py qc/ok_$inp.jpg $clips
done
ls -la qc/
