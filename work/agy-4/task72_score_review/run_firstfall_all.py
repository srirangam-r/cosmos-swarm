#!/usr/bin/env python3
"""Run referee-validated firstfall.py (20/20 PASS) on all 16 Brev A100 GAUGE ball clips:
8 baseline held-ball clips (box_ctrl) vs 8 mid-fall conditioned clips (box_mid).
"""
import os, sys, json, subprocess
import numpy as np

PYTHON_BIN = "/usr/bin/python3"
FIRSTFALL_PY = "/home/nail/swarm-work/agy-4/cosmos-swarm/tools/realball/firstfall.py"
CLIPS_DIR = "/home/nail/swarm-work/raj-3/brev_box/out"
WORK_DIR = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task72_score_review"
os.makedirs(WORK_DIR, exist_ok=True)

results = {"baseline_held": {}, "recipe_midfall": {}}

for b in (1, 2):
    for s in (1, 2, 3, 4):
        # Baseline held clip
        ctrl_name = f"box_ctrl_b{b}_noneg_s{s}"
        ctrl_path = os.path.join(CLIPS_DIR, f"{ctrl_name}.mp4")
        cmd_ctrl = [
            PYTHON_BIN, FIRSTFALL_PY, ctrl_path,
            "--fps", "24", "--ppm", "539.8",
        ]
        print(f"Running firstfall on {ctrl_name}...", flush=True)
        try:
            res = subprocess.run(cmd_ctrl, capture_output=True, text=True, check=True)
            out_str = res.stdout
            idx = out_str.find("{")
            if idx != -1:
                data = json.loads(out_str[idx:])
                results["baseline_held"][ctrl_name] = data
            else:
                results["baseline_held"][ctrl_name] = {"error": "no json", "raw": out_str}
        except subprocess.CalledProcessError as e:
            results["baseline_held"][ctrl_name] = {"error": str(e), "stderr": e.stderr, "stdout": e.stdout}

        # Recipe midfall clip
        mid_name = f"box_mid_b{b}_noneg_s{s}"
        mid_path = os.path.join(CLIPS_DIR, f"{mid_name}.mp4")
        cmd_mid = [
            PYTHON_BIN, FIRSTFALL_PY, mid_path,
            "--fps", "24", "--ppm", "539.8",
        ]
        print(f"Running firstfall on {mid_name}...", flush=True)
        try:
            res = subprocess.run(cmd_mid, capture_output=True, text=True, check=True)
            out_str = res.stdout
            idx = out_str.find("{")
            if idx != -1:
                data = json.loads(out_str[idx:])
                results["recipe_midfall"][mid_name] = data
            else:
                results["recipe_midfall"][mid_name] = {"error": "no json", "raw": out_str}
        except subprocess.CalledProcessError as e:
            results["recipe_midfall"][mid_name] = {"error": str(e), "stderr": e.stderr, "stdout": e.stdout}

out_file = os.path.join(WORK_DIR, "firstfall_16_clips_results.json")
with open(out_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"Saved firstfall results to {out_file}", flush=True)
