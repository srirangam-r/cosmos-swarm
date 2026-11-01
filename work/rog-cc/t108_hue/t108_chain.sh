#!/bin/bash
# Secondary (PREREG addendum A1): codex-1 task-108 ball3 F/QT s1-3 through the same midq judge + analyzer.
# Polls GB10 for QT s2/s3 (gives up 60 min), waits for the midq judge and t101 DOVER jobs, then judges.
W=/home/nail/other_work/sclaw/swarm-work/rog-cc; cd $W/t108_hue
R=swarm@board.tail0c526a.ts.net:jobs/codex-1/rep2460/
for i in $(seq 1 30); do
  n=$(ssh -o ConnectTimeout=10 swarm@board.tail0c526a.ts.net 'ls ~/jobs/codex-1/rep2460/t108_ball3_*_s[123].mp4 2>/dev/null | wc -l')
  echo "$(date -u +%T) remote t108 mp4s: $n"; [ "$n" -ge 6 ] && break; sleep 120
done
sleep 60; rsync -a --include='t108_ball3_*' --exclude='*' $R raw/
for f in raw/t108_ball3_*_s*.mp4; do b=$(basename $f .mp4); arm=$(echo $b | cut -d_ -f3); s=$(echo $b | cut -d_ -f4)
  ln -f $f clips/cause_${arm}_ball3_fps24_93f_${s}.mp4; done
sha256sum raw/*.mp4 > raw/SHA256SUMS
# controls with the SAME script as the main run (trunc36 of F/QT; static from F s1 f0). make_controls.sh
# hardcodes ball1/ball2 names for static, so build the ball3 static with its exact recipe.
bash $W/cosmos-swarm/work/rog-cc/midq/make_controls.sh clips ctl 2>/dev/null || true
ffmpeg -nostdin -loglevel error -y -i clips/cause_F_ball3_fps24_93f_s1.mp4 -frames:v 1 /tmp/t108_f0.png
ffmpeg -nostdin -loglevel error -y -loop 1 -framerate 24 -i /tmp/t108_f0.png -frames:v 93 -c:v libx264 -crf 12 -pix_fmt yuv420p ctl/static_cause_F_ball3_fps24_93f_s1.mp4
ls ctl
while kill -0 1521814 2>/dev/null || kill -0 1504700 2>/dev/null; do sleep 20; done
echo "$(date -u +%T) judging"
bash $W/cosmos-swarm/work/rog-cc/midq/run.sh clips ctl judge.json > judge.log 2>&1
python3 $W/cosmos-swarm/work/rog-cc/midq/analyze_midq.py judge.json --out summary.json > summary.txt 2>&1
echo "$(date -u +%T) DONE rc=$?"
