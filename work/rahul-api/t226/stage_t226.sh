#!/bin/bash
# Amendment 3 replacement for wait_t226.sh. Fetch t226 clips until none pending/running; then blindset/ = clips + 7 known-
# answer controls (symlinks); make random-ID strips; commit + push strips, key hash and checksums. No measurement.
cd /home/sha/swarm-work/rahul-api/cosmos-swarm/work/rahul-api/t226
PY=/home/sha/swarm-work/rahul-api/.venv/bin/python; CTRL=/home/sha/swarm-work/rahul-api/t226_ctrl
while true; do
  out=$(python3 ../t210/fetch_t210.py clips t226_ 2>&1); echo "$(date -u +%H:%M:%S) $out"
  if echo "$out" | grep -q "pending/running 0;" && ! kill -0 "${SUBMIT_PID:-0}" 2>/dev/null; then break; fi
  sleep 60
done
n=$(ls clips/t226_*.mp4 | wc -l); echo "$(date -u +%H:%M:%S) fetched $n clips"
if [ "$n" -lt 72 ]; then echo "only $n clips; not making strips"; exit 1; fi
mkdir -p blindset && (cd blindset && ln -sf ../clips/t226_*.mp4 . && ln -sf $CTRL/t226_*_ka*.mp4 .)
$PY blind_t226.py make blindset || exit 1
sha256sum clips/t226_*.mp4 > clips_SHA256SUMS; (cd $CTRL && sha256sum t226_*_ka*.mp4) > ctrl_SHA256SUMS
echo "$(date -u +%H:%M:%S) strips made: $(ls strips/*.jpg | wc -l)"
git add strips blind_key.sha256 clips_SHA256SUMS ctrl_SHA256SUMS
git -c user.name=rahul-api -c user.email=rahul-api@swarm commit -q -m "t226: blind strips (72 clips + 7 known-answer controls), key sha256, checksums

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>" -- strips blind_key.sha256 clips_SHA256SUMS ctrl_SHA256SUMS
for i in 1 2 3; do git pull -q --rebase --autostash && git push -q && { echo "$(date -u +%H:%M:%S) pushed $(git rev-parse --short HEAD)"; break; }; sleep 20; done
echo done
