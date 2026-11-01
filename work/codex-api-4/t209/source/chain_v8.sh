#!/bin/bash
# ro-1 v8: after v7 finishes, deploy srv/server_next.py (adds prompt_switch; otherwise identical), health-check with
# rollback, then run the prompt-switch probe jobs_v8.jsonl -> out_cause8.
cd /home/rohith/swarm-work/ro-1/fps_sweep
while kill -0 777596 2>/dev/null; do sleep 20; done
S=../srv; URL=http://100.77.182.40:8021
# wait until the server is idle
for k in $(seq 1 60); do curl -s -m 5 $URL/health | grep -q '"busy":false' && break; sleep 10; done
cp $S/server.py $S/server_v1_backup.py && cp $S/server_next.py $S/server.py
echo "deploy $(date -u +%T)"; pkill -f '^/home/rohith/swarm-work/ro-1/py312/bin/python server.py --host' ; sleep 30
ok=0; for k in $(seq 1 30); do curl -s -m 5 $URL/health | grep -q served && { ok=1; break; }; sleep 10; done
if [ $ok = 0 ]; then echo "ROLLBACK $(date -u +%T)"; cp $S/server_v1_backup.py $S/server.py; pkill -f '^/home/rohith/swarm-work/ro-1/py312/bin/python server.py --host'; sleep 60; curl -s -m 5 $URL/health; echo; echo FAILED; exit 1; fi
echo "server up $(date -u +%T)"
nice -n 10 ../py312/bin/python -I client.py jobs_v8.jsonl --url $URL --out out_cause8 > client_v8.log 2>&1
../py312/bin/python -I - >> chain_v8.out 2>&1 <<'PY'
import av, numpy as np
def rd(p):
    c=av.open(p); a=np.stack([f.to_ndarray(format='rgb24') for f in c.decode(video=0)]); c.close(); return a.astype(np.int16)
for s in (3,5):
    a=rd(f'out_cause8/v8_SWfull_ball1_fps24_93f_s{s}.mp4'); b=rd(f'out_cause5/cause5_QT_ball1_fps24_93f_s{s}.mp4')
    print('hookcheck s',s,'maxabs',int(np.abs(a-b).max()),'mean',float(np.abs(a-b).mean()))
PY
echo DONE
