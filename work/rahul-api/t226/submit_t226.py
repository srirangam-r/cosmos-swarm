#!/usr/bin/env python3
"""Trickle-submit t226 jobs under the per-owner pending cap. Seeds 101-104 -> a6k-0..3; seeds 105-106 -> a100
(each seed's 12 clips on one GPU type). Skips names already in the queue."""
import json, subprocess, sys, time, urllib.request, tempfile, os
URL = "http://100.111.167.68:8030"; Q = "/home/sha/devel/agentic_colab/scripts/cosmos_queue.py"
GROUPS = {"a6k-0,a6k-1,a6k-2,a6k-3": {101, 102, 103, 104}, "a100": {105, 106}}
HERE = os.path.dirname(os.path.abspath(__file__))
jobs = [json.loads(l) for l in open(os.path.join(HERE, "jobs.jsonl")) if l.strip()]
while True:
    q = json.load(urllib.request.urlopen(f"{URL}/jobs?owner=rahul-api"))["jobs"]
    have = {j["name"] for j in q if j["status"] in ("pending", "running", "done")}
    pend = sum(j["status"] == "pending" for j in q)
    todo = [j for j in jobs if j["name"] not in have]
    print(time.strftime("%H:%M:%S", time.gmtime()), "UTC pending", pend, "todo", len(todo), flush=True)
    if not todo:
        break
    room = 55 - pend
    for ep, seeds in GROUPS.items():
        part = [j for j in todo if j["seed"] in seeds][:max(room, 0)]
        if not part:
            continue
        with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False) as f:
            for j in part:
                f.write(json.dumps(j) + "\n")
        subprocess.run(["python3", Q, "submit", f.name, "--owner", "rahul-api", "--endpoints", ep])
        room -= len(part)
    time.sleep(30)
print("all submitted", flush=True)
