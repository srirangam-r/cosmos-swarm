#!/usr/bin/env python3
"""
Scores all 8 true-color clips (control vs RoPE 0.7x across seeds 1-4)
using tools/nv_scoreboard/score.py with 3 DOVER reps and RAFT Dynamic Degree.
Saves results to scores_task90_truecolor.json.
"""
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent / "results"
DOVER_DIR = "/home/rohith/swarm-work/ro-1/scoreboard/DOVER"
PYTHON = "/home/rohith/swarm-work/ro-1/py312/bin/python"
SCORE_SCRIPT = str(Path(__file__).resolve().parents[3] / "tools" / "nv_scoreboard" / "score.py")

clips = sorted(glob.glob(str(RESULTS_DIR / "gauge_b1_*_true.mp4")))
print(f"Scoring {len(clips)} true-color clips with DOVER (reps=3) and DD on GPU 1...")

all_results = {}
for clip_path in clips:
    name = Path(clip_path).name
    print(f"\n--- Scoring {name} ---", flush=True)
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = "1"
    env["PYTHONPATH"] = DOVER_DIR

    cmd = [
        PYTHON,
        SCORE_SCRIPT,
        clip_path,
        "--dover_dir", DOVER_DIR,
        "--dover_reps", "3",
        "--seed", "42"
    ]
    res = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Error scoring {name}: {res.stderr}", flush=True)
        continue

    # Parse JSON from last line of stdout
    lines = [line.strip() for line in res.stdout.strip().split("\n") if line.strip().startswith("{")]
    if lines:
        try:
            score_data = json.loads(lines[-1])
            all_results[name] = score_data
            print(f"Done {name}: Fused={score_data.get('dover_fused'):.4f}, DD={score_data.get('dd_norm'):.2f}", flush=True)
        except Exception as e:
            print(f"JSON parse error for {name}: {e}\nOutput was: {lines[-1]}", flush=True)
    else:
        print(f"No JSON found in output for {name}:\n{res.stdout}", flush=True)

out_file = RESULTS_DIR / "scores_task90_truecolor.json"
with open(out_file, "w") as f:
    json.dump(all_results, f, indent=2)

print(f"\nSuccessfully wrote {len(all_results)} scores to {out_file}!")
