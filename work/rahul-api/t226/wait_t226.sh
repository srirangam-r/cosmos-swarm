#!/bin/bash
# Fetch t226 clips until none pending/running, then make blind strips (no measurement: code strips blind first).
cd /home/sha/swarm-work/rahul-api/cosmos-swarm/work/rahul-api/t226
PY=/home/sha/swarm-work/rahul-api/.venv/bin/python
while true; do
  out=$(python3 ../t210/fetch_t210.py clips t226_ 2>&1); echo "$(date -u +%H:%M:%S) $out"
  if echo "$out" | grep -q "pending/running 0;" && ! pgrep -f submit_t226.py >/dev/null; then break; fi
  sleep 60
done
n=$(ls clips/t226_*.mp4 | wc -l); echo "$(date -u +%H:%M:%S) fetched $n clips"
[ "$n" -ge 72 ] && $PY blind_t226.py make clips && sha256sum clips/t226_*.mp4 > clips_SHA256SUMS && echo "strips made"
echo done
