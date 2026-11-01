#!/bin/bash
# Task 255 E3 on a GPU box (dk1). Runs everything on-box against 127.0.0.1: no tunnels, nothing public.
# Usage (on the box, from ~/jobs/dk1/e3 after `rsync` of this dir + tools/cosmos_local + devset_bridge):
#   bash run_onbox.sh <python-with-torch+diffusers> <Cosmos3-Nano model dir> [port=8012]
# Layout expected in the cwd: cosmos_local/ (tools/cosmos_local @ HEAD), devset_bridge/, jobs.jsonl, action_cfg.py,
#   server_action_cfg.patch, client wrapper below. Output: clips/ (mp4 + client json + <name>.server.json).
set -euo pipefail
PY=$1; MODEL=$2; PORT=${3:-8012}
cd "$(dirname "$0")"
W=$PWD
cp action_cfg.py cosmos_local/
( cd cosmos_local && (patch -p3 --dry-run -s < ../server_action_cfg.patch >/dev/null 2>&1 && patch -p3 -s < ../server_action_cfg.patch) \
    || grep -q "import action_cfg" server.py )
# rewrite the local image paths in jobs.jsonl to this box's devset copy
"$PY" -I -c "
import json,sys,os
w=sys.argv[1]
with open(os.path.join(w,'jobs_box.jsonl'),'w') as f:
    for l in open(os.path.join(w,'jobs.jsonl')):
        j=json.loads(l); p=j['image'].split('devset_bridge/')[1]; j['image']=os.path.join(w,'devset_bridge',p); f.write(json.dumps(j)+'\n')
" "$W"
mkdir -p clips srv
if ! curl -sf "http://127.0.0.1:$PORT/health" | grep -q action_cfg; then
  COSMOS_OFFLOAD=0 COSMOS_LABEL=dk1-e3 nohup "$PY" cosmos_local/server.py --host 127.0.0.1 --port "$PORT" \
      --model "$MODEL" --out "$W/srv" > server.log 2>&1 &
  echo $! > server.pid
  for i in $(seq 1 120); do curl -sf "http://127.0.0.1:$PORT/health" | grep -q action_cfg && break; sleep 10; done
fi
curl -sf "http://127.0.0.1:$PORT/health" | grep -q action_cfg || { echo "server not up with action_cfg"; exit 1; }
"$PY" -I cosmos_local/client.py jobs_box.jsonl --url "http://127.0.0.1:$PORT" --out clips
# attach each job's server sidecar (sigmas, noise, action_cfg guided steps) as <name>.server.json
"$PY" -I -c "
import json,glob,os,shutil
for p in glob.glob('clips/t255e3_*.json'):
    if p.endswith('.server.json'): continue
    cid=json.load(open(p)).get('server_clip_id'); s=os.path.join('srv',f'{cid}.json')
    if cid and os.path.exists(s): shutil.copy(s, p[:-5]+'.server.json')
"
echo E3_DONE
