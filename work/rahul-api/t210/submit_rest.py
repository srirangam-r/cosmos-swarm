#!/usr/bin/env python3
"""Trickle-submit jobs from a jsonl to the queue under the 60-pending-per-owner cap; skips names already in the queue."""
import json, subprocess, sys, time, urllib.request, tempfile
URL = "http://100.111.167.68:8030"; Q = "/home/sha/devel/agentic_colab/scripts/cosmos_queue.py"
EP = "q8-0,q8-1,q8-2,q8-3,q8-4,q8-5,q8-6,q8-7"
jobs = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
while True:
    q = json.load(urllib.request.urlopen(f"{URL}/jobs?owner=rahul-api"))["jobs"]
    have = {j["name"] for j in q if j["status"] in ("pending", "running", "done")}
    pend = sum(j["status"] == "pending" for j in q)
    todo = [j for j in jobs if j["name"] not in have]
    print(time.strftime("%H:%M:%S"), "pending", pend, "todo", len(todo), flush=True)
    if not todo:
        break
    room = 55 - pend
    if room > 0:
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            for j in todo[:room]:
                f.write(json.dumps(j) + "\n")
        subprocess.run(["python3", Q, "submit", f.name, "--owner", "rahul-api", "--endpoints", EP])
    time.sleep(20)
print("all submitted", flush=True)
