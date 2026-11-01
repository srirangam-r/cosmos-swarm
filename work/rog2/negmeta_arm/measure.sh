#!/bin/bash
# usage: measure.sh CLIPS_DIR OUT_DIR   (firstfall v1 per clip, seed on gripper-held ball at frame 0; plus 2 tmax variants)
C=$1; O=$2; mkdir -p $O/qc
for f in $C/negmeta_*.mp4; do n=$(basename $f .mp4); [ -f $O/$n.json ] && continue
  python3 -I tools/realball/firstfall.py $f --fps 24 --ppm 539.8 --point 281,115 --pframe 0 --qc $O/qc/$n.png > $O/$n.json 2> $O/$n.err
done
