#!/bin/bash
# Wait for poornima-1 task-101 clips on GB10 (#2427/#2447), pull them read-only, score DOVER(reps3)+DD, analyze.
cd /home/nail/other_work/sclaw/swarm-work/rog-cc/t101_nv
SRC=swarm@board.tail0c526a.ts.net:jobs/poornima-1/task101/clips/
END=$(( $(date +%s) + 100*60 ))
prev=-1; stable=0
while [ $(date +%s) -lt $END ]; do
  n=$(ssh -o ConnectTimeout=10 swarm@board.tail0c526a.ts.net 'ls ~/jobs/poornima-1/task101/clips/*.mp4 2>/dev/null | wc -l')
  echo "$(date -u +%T) remote mp4s: $n"
  if [ "$n" = "$prev" ] && [ "$n" -ge 1 ]; then stable=$((stable+1)); else stable=0; fi
  prev=$n
  # 32 clips unchanged over one poll, or >=24 unchanged over 3 polls (6 min)
  if [ "$n" -ge 32 ] && [ $stable -ge 1 ]; then break; fi
  if [ "$n" -ge 24 ] && [ $stable -ge 3 ]; then break; fi
  sleep 120
done
mkdir -p clips
rsync -a --include='*.mp4' --include='*.json' --exclude='*' $SRC clips/
ls clips/*.mp4 | wc -l
sha256sum clips/*.mp4 > clips/SHA256SUMS
python3 f0check.py clips ../t92_nv/clips > f0check.json
LOCK=/tmp/rogcc_gpu.lock
DOVER=/home/nail/other_work/sclaw/swarm-work/rog-cc/ext/DOVER
flock "$LOCK" python3 /home/nail/other_work/sclaw/swarm-work/rog-cc/cosmos-swarm/tools/nv_scoreboard/score.py clips/*.mp4 --dover_dir "$DOVER" --device cuda --dover_reps 3 --out nv_t101.json
python3 analyze_t101.py nv_t101.json > summary_t101.json
echo DONE $(date -u)
