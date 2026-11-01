#!/usr/bin/env python3
"""Poll GB10 ~/jobs/rahul-3/eval_clips/ (blinded task-24 GAUGE-ball clips), pull ONLY *.mp4 (stay blind), and score new
clips with tools/nv_scoreboard (DOVER x3 + VBench DD) on the local GPU under a shared flock (the HUE judge uses the same lock).
PREREG.md addendum A2. Usage: gauge_nv_watch.py ROOT [hours]"""
import os, sys, glob, json, subprocess, time
HOST = "swarm@board.tail0c526a.ts.net"; REM = "jobs/rahul-3/eval_clips/"
ROOT = sys.argv[1]; HOURS = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
HERE = os.path.dirname(os.path.abspath(__file__))
NV = os.path.join(HERE, "../../../tools/nv_scoreboard/score.py")
DOVER = os.path.expanduser("~/other_work/sclaw/swarm-work/rog-cc/ext/DOVER"); LOCK = "/tmp/rogcc_gpu.lock"
CL, OUT = f"{ROOT}/clips", f"{ROOT}/res/gauge_nv.json"; os.makedirs(CL, exist_ok=True); os.makedirs(f"{ROOT}/res", exist_ok=True)
end = time.time() + HOURS * 3600
while time.time() < end:
    try:
        subprocess.run(["rsync", "-a", "--include=*.mp4", "--exclude=*", f"{HOST}:{REM}", CL + "/"], check=True, timeout=1200)
    except Exception as e:
        print(time.strftime("%H:%M:%S"), "rsync fail", e, flush=True); time.sleep(300); continue
    done = set(json.load(open(OUT))) if os.path.exists(OUT) else set()
    # only clips untouched for >60 s (avoid half-copied files)
    new = [p for p in sorted(glob.glob(CL + "/*.mp4")) if os.path.basename(p) not in done and time.time() - os.path.getmtime(p) > 60]
    print(time.strftime("%H:%M:%S"), "clips", len(done) + len(new), "new", len(new), flush=True)
    if new:
        rc = subprocess.run(["flock", LOCK, "python3", NV, *new, "--dover_dir", DOVER, "--device", "cuda", "--dover_reps", "3", "--out", OUT]).returncode
        print(time.strftime("%H:%M:%S"), "scored rc", rc, flush=True)
    time.sleep(600)
print("watcher exit", flush=True)
