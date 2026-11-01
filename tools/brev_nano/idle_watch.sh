#!/bin/bash
# Run on sha-devel. Deletes a Brev box (and stops its tunnel loop) when its endpoints serve no clip for IDLE_MIN
# minutes, or when the box's spend reaches CAP_USD. Never deletes while any endpoint reports busy.
# Usage: idle_watch.sh <box> <usd_per_h> <start_epoch> <tunnel_loop_pid> <url> [<url> ...]
# Env: IDLE_MIN (default 40), CAP_USD (default 60), POLL (default 120 s). Stop the watcher: touch ~/STOP_<box>.
B=$1; RATE=$2; T0=$3; TPID=$4; shift 4; URLS="$@"
IDLE_MIN=${IDLE_MIN:-40}; CAP=${CAP_USD:-60}; POLL=${POLL:-120}
last_total=-1; last_change=$(date +%s)
while true; do
  [ -f ~/STOP_$B ] && { echo "$(date -u +%FT%TZ) stop file, watcher exits (box kept)"; exit 0; }
  total=0; busy=0
  for u in $URLS; do
    h=$(curl -s -m 10 $u/health)
    s=$(echo "$h" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d["served"], int(d["busy"]) + d.get("waiting",0))' 2>/dev/null)
    [ -z "$s" ] && { echo "$(date -u +%FT%TZ) $u unreachable"; continue; }
    total=$((total + ${s% *})); busy=$((busy + ${s#* }))
  done
  now=$(date +%s)
  if [ "$total" != "$last_total" ] || [ "$busy" -gt 0 ]; then last_total=$total; last_change=$now; fi
  idle=$(( (now - last_change) / 60 ))
  usd=$(python3 -c "print(round(($now-$T0)/3600*$RATE,2))")
  echo "$(date -u +%FT%TZ) served=$total busy=$busy idle_min=$idle spend_usd=$usd"
  if [ "$idle" -ge "$IDLE_MIN" ] || python3 -c "import sys; sys.exit(0 if $usd >= $CAP else 1)"; then
    echo "$(date -u +%FT%TZ) DELETING $B (idle ${idle} min, spend \$$usd)"
    kill $TPID 2>/dev/null; pkill -f -- "-N -T .* $B\$" 2>/dev/null
    brev delete $B && echo "$(date -u +%FT%TZ) DELETED $B" ; exit 0
  fi
  sleep $POLL
done
