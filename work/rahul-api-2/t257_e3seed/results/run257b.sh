#!/bin/bash
# t257 v2: retry fetch until all 72 E3 clips are on disk (max 40 tries x 60 s), THEN hash, measure, analyze (frozen e3seed.py a75e1c0).
cd /home/sha/swarm-work/rahul-api-2/t257
Q=/home/sha/devel/agentic_colab/scripts/cosmos_queue.py
E=/home/sha/swarm-work/rahul-api-2/cosmos-swarm/work/rahul-api-2/t257_e3seed/e3seed.py
PY=/home/sha/swarm-work/rahul-api-2/.venv/bin/python
for i in $(seq 1 40); do
  n=$(ls clips/N_E3_*.mp4 2>/dev/null | wc -l); echo "try $i: $n clips $(date -u +%H:%M:%S)"
  [ "$n" -ge 72 ] && break
  for o in raj-noise-f raj-noise-g; do timeout 600 python3 $Q fetch --owner $o --out clips 2>&1 | tail -2; done
  n=$(ls clips/N_E3_*.mp4 2>/dev/null | wc -l); [ "$n" -ge 72 ] && break
  sleep 60
done
n=$(ls clips/N_E3_*.mp4 | wc -l)
if [ "$n" -lt 72 ]; then echo "FETCH INCOMPLETE: $n/72"; exit 1; fi
# drop truncated files: every clip must decode to 93 frames
$PY -I -c "
import cv2,glob,sys
bad=[p for p in sorted(glob.glob('clips/N_E3_*.mp4')) if int(cv2.VideoCapture(p).get(cv2.CAP_PROP_FRAME_COUNT))!=93]
print('bad frame counts:',bad); sys.exit(1 if bad else 0)" || { echo "TRUNCATED CLIPS"; exit 1; }
(cd clips && sha256sum N_E3_*.mp4 > ../E3_SHA256SUMS)
$PY -I $E measure clips meas.json
$PY -I $E analyze meas.json result.json
touch DONE
