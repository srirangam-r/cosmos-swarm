#!/bin/bash
# Fallback for q8 outage (#6964). At 21:35 UTC: if no queue endpoint is up, rent 1xH100, run t336b on-box, copy back, delete box.
W=/home/nail/other_work/sclaw/swarm-work/dk1; Q=/home/nail/other_work/sclaw/agentic_colab/scripts/cosmos_queue.py; N=dk1-336b
log(){ echo "$(date -u +%T) $*"; }
until [ $(date -u +%H%M) -ge 2135 ]; do sleep 30; done
[ -f $W/NO_BOX ] && { log "NO_BOX present, abort"; exit 0; }
if python3 $Q status 2>&1 | grep -E "^endpoint" | grep -vq " down "; then log Q8_BACK; exit 0; fi
log "queue still down; creating $N"
ok=0
for T in gpu_1x_h100_sxm5 scaleway_H100; do
  timeout 300 brev create $N --type $T -d --startup-script @$W/t266/bootstrap_dk1.sh 2>&1 | tail -3
  for i in $(seq 1 40); do st=$(timeout 60 brev ls 2>/dev/null | awk -v n=$N '$1==n{print $2}'); log "status $st"; [ "$st" = RUNNING ] && { ok=1; break; }; echo "$st" | grep -qE "FAIL|DELET" && break; sleep 30; done
  [ $ok = 1 ] && { log "RUNNING on $T"; break; }
  timeout 120 brev delete $N 2>&1 | tail -1; sleep 20
done
[ $ok = 1 ] || { log CREATE_FAILED; exit 1; }
T0=$(date +%s); DEADLINE=$((T0+9000))   # 2.5 h hard cap
timeout 120 brev refresh >/dev/null 2>&1
for i in $(seq 1 120); do ssh -o StrictHostKeyChecking=no -o ConnectTimeout=20 $N 'test -f ~/nano/READY' 2>/dev/null && break; ssh -o ConnectTimeout=20 $N 'tail -1 ~/nano/setup.log; ls ~/nano' 2>/dev/null | tr '\n' ' '; echo; sleep 30; done
ssh $N 'test -f ~/nano/READY' || { log NOT_READY; timeout 300 brev delete $N; exit 1; }
log READY; rsync -az $W/box336b/ $N:jobs/dk1/box336b/
ssh -n $N 'cd ~/jobs/dk1/box336b && nohup bash run_onbox_q.sh ~/nano/venv312/bin/python ~/nano/models/Cosmos3-Nano jobs_dk2.jsonl > run.log 2>&1 &'
for i in $(seq 1 120); do ssh $N 'test -f ~/jobs/dk1/box336b/SUBMITTED' 2>/dev/null && break; sleep 30; done
ssh $N 'test -f ~/jobs/dk1/box336b/SUBMITTED' || { log "box never accepted jobs"; ssh $N 'tail -30 ~/jobs/dk1/box336b/run.log ~/jobs/dk1/box336b/server.log'; timeout 300 brev delete $N; exit 1; }
log "box accepted jobs; cancelling shared-queue t336b jobs + stopping old waiters"
kill 3389385 3464751 3475204 3364514 2>/dev/null
ids=$(python3 -c "
import sys; sys.path.insert(0,'/home/nail/other_work/sclaw/agentic_colab/scripts')
from cosmos_queue import call, DEFAULT_URL
names={__import__('json').loads(l)['name'] for l in open('$W/box336b/repo/jobs_dk2.jsonl')}
a=[j['id'] for j in call(f'{DEFAULT_URL}/jobs?owner=dk1')['jobs'] if j['name'].startswith('t336b_') and j['status']=='pending']
b=[j['id'] for j in call(f'{DEFAULT_URL}/jobs?owner=dk2')['jobs'] if j['name'] in names and j['status']=='pending']
print(' '.join(a+b))")
[ -n "$ids" ] && python3 $Q cancel $ids 2>&1 | tail -2
until ssh $N 'grep -q BOX_DONE ~/jobs/dk1/box336b/run.log' 2>/dev/null || [ $(date +%s) -gt $DEADLINE ]; do ssh $N 'ls ~/jobs/dk1/box336b/qroot | wc -l; grep -c "done" ~/jobs/dk1/box336b/queue.log' 2>/dev/null | tr '\n' ' '; echo; sleep 60; done
ssh $N 'cd ~/jobs/dk1/box336b && grep -q BOX_DONE run.log || python3 -I fetch_box.py dk1 t336b_ clips'
mkdir -p $W/t336b/clips $W/t336b/box_logs
rsync -az $N:jobs/dk1/box336b/clips/ $W/t336b/clips/; ssh $N 'cd ~/jobs/dk1/box336b && python3 -I fetch_box.py dk2 t3 clips_extra' ; rsync -az --ignore-existing $N:jobs/dk1/box336b/clips_extra/ /home/nail/other_work/sclaw/swarm-work/dk2/t319/clips_dk2/; rsync -az $N:jobs/dk1/box336b/{run.log,server.log,queue.log} $W/t336b/box_logs/
rsync -az $N:jobs/dk1/box336b/srv/ $W/t336b/box_logs/srv/ 2>/dev/null
log "copied $(ls $W/t336b/clips/t336b_*.mp4 | wc -l) clips; deleting box"
timeout 300 brev delete $N 2>&1 | tail -1; timeout 60 brev ls
log BOX_COPIED_DELETED
bash $W/box_chain.sh > $W/box_chain.log 2>&1
log LAUNCH_ALL_DONE
