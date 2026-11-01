#!/usr/bin/env python3
import json
import subprocess
from pathlib import Path

WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORK_DIR.parents[2]
CLIPS_DIR = WORK_DIR / "clips"
FIRSTFALL_PY = REPO_ROOT / "tools/realball/firstfall.py"
PYTHON_BIN = "/home/rohith/swarm-work/ro-1/py312/bin/python"

clips = sorted(list(CLIPS_DIR.glob("*.mp4")))
ff_results = {}

for c in clips:
    print(f"Running firstfall on {c.name}...")
    cmd = [
        PYTHON_BIN, str(FIRSTFALL_PY),
        str(c),
        "--fps", "24",
        "--ppm", "539.8"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    try:
        j = json.loads(res.stdout)
        ff_results[c.stem] = {
            "g": j.get("g"),
            "g_sd": j.get("g_sd"),
            "r2": j.get("r2"),
            "flag": j.get("flag"),
            "fall_px": j.get("fall_px"),
            "fall_time_s": j.get("fall_time_s"),
            "n_fit": j.get("n_fit"),
            "t0": j.get("t0")
        }
    except Exception as e:
        ff_results[c.stem] = {"error": str(e), "raw": res.stdout[:200]}

out_path = WORK_DIR / "firstfall_24_clips_results.json"
with open(out_path, "w") as f:
    json.dump(ff_results, f, indent=2)

print(f"Done! Saved {len(ff_results)} firstfall results to {out_path}")
