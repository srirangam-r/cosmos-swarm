#!/bin/bash
# dk1 t336b on a rented H100 while q8 is down. Everything binds to 127.0.0.1.
# server.py = tools/cosmos_local @d66b830 (md5 04e8e0de81 = q8's deployed server_rev); requests go through a private
# copy of scripts/cosmos_queue_server.py so they are byte-identical to the shared queue's.
# usage (on the box, in this dir): bash run_onbox_q.sh <python> <model dir> [extra jobs.jsonl relative to repo/ ...]
set -uo pipefail
PY=$1; MODEL=$2; shift 2
cd "$(dirname "$0")"; W=$PWD; mkdir -p srv qroot clips
if ! curl -sf http://127.0.0.1:8012/health >/dev/null; then
  COSMOS_OFFLOAD=0 COSMOS_LABEL=dk1-box336b nohup "$PY" cosmos_local/server.py --host 127.0.0.1 --port 8012 --model "$MODEL" --out "$W/srv" > server.log 2>&1 &
  echo $! > server.pid
  for i in $(seq 1 180); do curl -sf http://127.0.0.1:8012/health >/dev/null && break; sleep 10; done
fi
curl -sf http://127.0.0.1:8012/health || { echo "server not up"; tail -30 server.log; exit 1; }
nohup python3 -I repo/scripts/cosmos_queue_server.py --host 127.0.0.1 --port 8030 --root "$W/qroot" --endpoint box336b=http://127.0.0.1:8012 > queue.log 2>&1 &
echo $! > queue.pid; sleep 3
Q="python3 -I scripts/cosmos_queue.py --url http://127.0.0.1:8030"
cd repo
if [ ! -f ../SUBMITTED ]; then
  $Q submit work/dk1/t336_region/jobs_b.jsonl --owner dk1 && for f in "$@"; do $Q submit "$f" --owner "${OWNER_EXTRA:-dk2}"; done && touch ../SUBMITTED
fi
while $Q status 2>&1 | grep -qE "pending|running"; do sleep 30; done
$Q status
cd .. && python3 -I fetch_box.py dk1 t336b_ clips && cd repo
cd .. && { [ $# -gt 0 ] && python3 -I fetch_box.py "${OWNER_EXTRA:-dk2}" t3 clips_extra; } ; cd repo
echo BOX_DONE
