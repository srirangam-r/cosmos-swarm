#!/bin/bash
# usage: batch.sh s_from s_to  -> zoom sheets b1/b2 per seed into oc/qcsheets_amd3/z<seed>.jpg (only complete clips with sidecar)
cd /home/sha/swarm-work/rahul-api-2
for s in $(seq $1 $2); do
  a=oc/nano_amd3/oc_A_ball1_s$s; b=oc/nano_amd3/oc_A_ball2_s$s
  if [ -f $a.json ] && [ -f $b.json ]; then .venv/bin/python -I oc/zsheet.py oc/qcsheets_amd3 z$s- $a.mp4 $b.mp4 && echo "s$s ok"; else echo "s$s missing"; fi
done
