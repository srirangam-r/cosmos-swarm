#!/bin/bash
# Pull poornima-1 task-92 base vs fast05 clips (read-only, at their request #2290) and score DOVER(reps3)+DD.
set -x
cd /home/nail/other_work/sclaw/swarm-work/rog-cc/t92_nv
rsync -a --include='b1dd33_base_*' --include='b1dd33_fast05_*' --include='b3dd35_base_*' --include='b3dd35_fast05_*' --exclude='*' \
  swarm@board.tail0c526a.ts.net:jobs/poornima-1/task92/clips/ clips/
ls clips | wc -l
sha256sum clips/*.mp4 > clips/SHA256SUMS
LOCK=/tmp/rogcc_gpu.lock
DOVER=/home/nail/other_work/sclaw/swarm-work/rog-cc/ext/DOVER
flock "$LOCK" python3 /home/nail/other_work/sclaw/swarm-work/rog-cc/cosmos-swarm/tools/nv_scoreboard/score.py clips/*.mp4 --dover_dir "$DOVER" --device cuda --dover_reps 3 --out nv_t92.json
echo DONE $(date -u)
