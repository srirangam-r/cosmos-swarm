#!/bin/bash
# Task 133 runner: fetch queue clips -> HUE judge (base,R) -> DOVER/DD (base,R) -> analyze -> judge N -> NV N -> analyze.
set -u
W=/home/nail/other_work/sclaw/swarm-work/rog-cc; ES=$W/endstate; REPO=$W/cosmos-swarm
Q=/home/nail/other_work/sclaw/agentic_colab/scripts/cosmos_queue.py
JUDGE=$REPO/tools/hue_judge/hue_judge.py; QS=$W/../rog1/data/hue/hue-v1p2-t2v-public.json
NVS=$REPO/tools/nv_scoreboard/score.py; DOVER=$W/ext/DOVER; LOCK=/tmp/rogcc_gpu.lock
mkdir -p $ES/clips $ES/res $ES/res_nv; cd $W
END=$(( $(date +%s) + 95*60 ))
while :; do
  python3 $Q fetch --owner rog-cc --out $ES/clips >> $ES/fetch.log 2>&1
  n=$(ls $ES/clips/es_*.mp4 2>/dev/null | wc -l); echo "$(date -u +%T) fetched $n/144"
  [ "$n" -ge 144 ] && break
  [ "$(date +%s)" -gt "$END" ] && { echo "fetch deadline, proceeding with $n"; break; }
  sleep 60
done
judge() { a=$1; args=(); for f in $ES/clips/es_${a}_*.mp4; do s=$(basename $f .mp4); s=${s#es_${a}_}; s=${s%_s[0-9]}; args+=(--clip $f --sample $s); done
  echo "$(date -u +%T) judging $a $(( ${#args[@]} / 4 ))"
  flock $LOCK python3 $JUDGE --questions $QS --offsets 0,0.5 --out $ES/res/$a.json "${args[@]}" > $ES/judge_$a.log 2>&1 && date -u +%FT%T > $ES/res/$a.json.done
  echo "$(date -u +%T) judge $a rc=$?"; }
nv() { a=$1; echo "$(date -u +%T) nv $a"
  flock $LOCK python3 $NVS $ES/clips/es_${a}_*.mp4 --dover_dir $DOVER --device cuda --dover_reps 1 --out $ES/res_nv/$a.json > $ES/nv_$a.log 2>&1 && date -u +%FT%T > $ES/res_nv/$a.json.done
  echo "$(date -u +%T) nv $a rc=$?"; }
ana() { python3 $REPO/work/rog-cc/endstate_t2v/analyze_es.py $ES --out $ES/summary.json > /dev/null 2> $ES/summary.txt; echo "$(date -u +%T) analyze rc=$?"; }
judge base; judge R; nv base; nv R; ana
judge N; nv N; ana
echo "$(date -u +%T) DONE"
