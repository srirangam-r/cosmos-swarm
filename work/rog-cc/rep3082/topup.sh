#!/bin/bash
# Queue caps pending jobs at ~60 per owner: submit rep3082 jobs as slots free (q8 only: internals hooks).
Q=/home/nail/other_work/sclaw/agentic_colab/scripts/cosmos_queue.py
J=/home/nail/other_work/sclaw/swarm-work/rog-cc/rep3082_jobs.jsonl
D=/home/nail/other_work/sclaw/swarm-work/rog-cc/rep3082; mkdir -p $D; T=$D/topup_batch.jsonl; S=$D/topup_status.txt
for i in $(seq 1 90); do
  python3 $Q status --owner rog-cc > $S 2>/dev/null || { sleep 60; continue; }
  python3 - "$J" "$T" "$S" <<'PY'
import sys, json
J, T, S = sys.argv[1:4]
rows = [l.split() for l in open(S) if len(l.split()) >= 4]
have = {r[3] for r in rows}; pend = sum(r[1] == "pending" for r in rows)
rest = [l for l in open(J) if json.loads(l)["name"] not in have]
room = max(0, 56 - pend)
open(T, "w").write("".join(rest[:room]))
print(len(rest), "left;", min(room, len(rest)), "to submit; pending", pend, flush=True)
PY
  [ -s $T ] && python3 $Q submit $T --owner rog-cc --endpoints q8-0,q8-1,q8-2,q8-3,q8-4,q8-5,q8-6,q8-7 2>&1 | tail -1
  [ "$(grep -c ' r3082_' $S)" -ge 40 ] && { echo "all 40 in queue"; break; }
  sleep 60
done
