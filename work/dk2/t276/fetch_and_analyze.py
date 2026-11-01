#!/usr/bin/env python3
"""
Targeted fetcher and analyzer for Task 276 clips.
Downloads only t276_* jobs for owner rahul-5-agy directly into work/dk2/t276/clips/,
and once all 24 jobs finish, executes analyze_t276.py.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
import urllib.request

REPO_ROOT = Path(__file__).resolve().parents[3]
T276_DIR = Path(__file__).resolve().parent
CLIPS_DIR = T276_DIR / "clips"
OUT_DIR = T276_DIR / "out"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

PYTHON_EXE = "/home/sha/swarm-work/rahul-5-agy/.venv/bin/python3"
QUEUE_URL = "http://board.tail0c526a.ts.net:8030"

TOTAL_EXPECTED = 24 # 18 nphys + 6 nphys_x17

def fetch_single_job(j):
    name = j["name"]
    jid = j["id"]
    mp4_path = CLIPS_DIR / f"{name}.mp4"
    json_path = CLIPS_DIR / f"{name}.json"
    
    if not mp4_path.exists():
        with urllib.request.urlopen(f"{QUEUE_URL}/jobs/{jid}/mp4", timeout=60) as resp:
            mp4_path.write_bytes(resp.read())
    
    if not json_path.exists():
        json_path.write_text(json.dumps(j.get("sidecar", {}), indent=1))
        
    if j.get("qc"):
        qc_path = CLIPS_DIR / f"{name}.qc.json"
        if not qc_path.exists():
            qc_path.write_text(json.dumps(j["qc"], indent=1))

    for rel in j.get("sidecar", {}).get("relayed", []):
        dest = CLIPS_DIR / (f"{name}.server.json" if rel == "server_sidecar.json" else f"{name}.{Path(rel).name}")
        if not dest.exists():
            try:
                with urllib.request.urlopen(f"{QUEUE_URL}/jobs/{jid}/files/{rel}", timeout=30) as resp:
                    dest.write_bytes(resp.read())
            except Exception as e:
                pass

def main():
    print("[Task 276] Starting targeted fetch and analyze loop...", flush=True)
    
    while True:
        try:
            req = urllib.request.Request(f"{QUEUE_URL}/jobs?owner=rahul-5-agy")
            with urllib.request.urlopen(req, timeout=30) as r:
                jobs = json.loads(r.read())["jobs"]
            
            t276_jobs = [j for j in jobs if j["name"].startswith("t276_")]
            done = [j for j in t276_jobs if j["status"] == "done"]
            failed = [j for j in t276_jobs if j["status"] == "failed"]
            running = [j for j in t276_jobs if j["status"] == "running"]
            pending = [j for j in t276_jobs if j["status"] == "pending"]

            print(f"[Queue status] Done: {len(done)} | Running: {len(running)} | Pending: {len(pending)} | Failed: {len(failed)}", flush=True)

            for j in done:
                fetch_single_job(j)

            downloaded = list(CLIPS_DIR.glob("t276_*.mp4"))
            plain_count = len([p for p in downloaded if "_plain_" in p.name])
            nphys_count = len([p for p in downloaded if "_nphys_s" in p.name])
            x17_count = len([p for p in downloaded if "_nphys_x17_" in p.name])
            print(f"[Clips in {CLIPS_DIR.name}] Plain: {plain_count}/18 | Nphys: {nphys_count}/18 | X17: {x17_count}/6 (Total: {len(downloaded)}/42)", flush=True)

            if len(done) + len(failed) >= TOTAL_EXPECTED:
                print("[Task 276] All jobs finished! Running analyze_t276.py...", flush=True)
                cmd = [PYTHON_EXE, "-I", str(T276_DIR / "analyze_t276.py"), str(CLIPS_DIR), str(OUT_DIR)]
                res = subprocess.run(cmd, capture_output=True, text=True)
                print(res.stdout, flush=True)
                if res.stderr:
                    print("[STDERR]\n", res.stderr, flush=True)
                print("[Task 276] Finished analysis successfully!", flush=True)
                break

            time.sleep(10)
        except Exception as e:
            print(f"[Warning] Error: {e}", file=sys.stderr, flush=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
