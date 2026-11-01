#!/usr/bin/env python3
"""Fetch only this task's (t210_*) finished queue jobs: <out>/<name>.mp4 + <name>.json sidecar."""
import json, sys, urllib.request
from pathlib import Path
URL = "http://100.111.167.68:8030"
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
jobs = json.load(urllib.request.urlopen(f"{URL}/jobs?owner=rahul-api"))["jobs"]
got = left = fail = 0
for j in jobs:
    if not j["name"].startswith("t210_"):
        continue
    if j["status"] != "done":
        left += j["status"] in ("pending", "running"); fail += j["status"] == "failed"
        if j["status"] == "failed": print("FAILED", j["name"], j.get("error"), file=sys.stderr)
        continue
    mp4 = out / f"{j['name']}.mp4"
    if mp4.exists():
        continue
    (out / f"{j['name']}.json").write_text(json.dumps({**j.get("sidecar", {}), "queue_job_id": j["id"]}, indent=1))
    mp4.write_bytes(urllib.request.urlopen(f"{URL}/jobs/{j['id']}/mp4").read())
    got += 1
print(f"got {got}; pending/running {left}; failed {fail}")
