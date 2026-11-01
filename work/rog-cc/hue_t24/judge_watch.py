#!/usr/bin/env python3
"""Poll GB10 ~/jobs/rahul-3/hue_clips/<arm>/, pull each arm once it has 32 stable clips, judge with tools/hue_judge (2B, 16f, offsets 0,0.5)."""
import os, re, subprocess, time, glob, json, sys
HOST = "swarm@board.tail0c526a.ts.net"; REM = "~/jobs/rahul-3/hue_clips"
ARMS = ["base", "loraC", "loraA", "baseL", "loraB"]
ROOT = os.path.expanduser("~/other_work/sclaw/swarm-work/rog-cc/hue_t24")
JUDGE = os.path.expanduser("~/other_work/sclaw/swarm-work/rog-cc/cosmos-swarm/tools/hue_judge/hue_judge.py")
QS = os.path.expanduser("~/other_work/sclaw/swarm-work/rog1/data/hue/hue-v1p2-t2v-public.json")
NEED = 32; DEADLINE = time.time() + 6.5 * 3600
pat = re.compile(r"^((?:physics|robot)_\d+)_s(\d+)\.mp4$")
last = {}; nstable = {}
def listing(arm):
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", HOST, f"cd {REM}/{arm} 2>/dev/null && ls -l --time-style=+%s *.mp4 2>/dev/null | awk '{{print $5, $7}}'"], capture_output=True, text=True, timeout=60)
    return tuple(sorted(l for l in r.stdout.splitlines() if l.strip()))
while time.time() < DEADLINE:
    todo = [a for a in ARMS if not os.path.exists(f"{ROOT}/res/{a}.json.done")]
    if not todo: break
    for arm in todo:
        try: L = listing(arm)
        except Exception as e: print("ls fail", arm, e, flush=True); continue
        print(time.strftime("%H:%M:%S"), arm, len(L), "clips", flush=True)
        nstable[arm] = nstable.get(arm, 0) + 1 if (last.get(arm) == L and L) else 0
        last[arm] = L
        # judge when complete and stable for 1 poll, or >=24 clips stable for 3 polls (15 min; a few clips failed)
        if not ((len(L) >= NEED and nstable[arm] >= 1) or (len(L) >= 24 and nstable[arm] >= 3)): continue
        d = f"{ROOT}/clips/{arm}"; os.makedirs(d, exist_ok=True); os.makedirs(f"{ROOT}/res", exist_ok=True)
        subprocess.run(["rsync", "-a", f"{HOST}:{REM}/{arm}/", d + "/"], check=True, timeout=1800)
        args = []
        for p in sorted(glob.glob(d + "/*.mp4")):
            m = pat.match(os.path.basename(p))
            if m: args += ["--clip", p, "--sample", m.group(1)]
        out = f"{ROOT}/res/{arm}.json"
        print("judging", arm, len(args) // 4, flush=True)
        rc = subprocess.run(["python3", JUDGE, "--questions", QS, "--offsets", "0,0.5", "--out", out] + args).returncode
        if rc == 0: open(out + ".done", "w").write(time.strftime("%FT%T"))
        else: print("judge failed", arm, rc, flush=True)
    time.sleep(300)
print("watcher exit", flush=True)
