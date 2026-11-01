#!/usr/bin/env python3
"""Run official NVIDIA scoreboard (DOVER + RAFT Dynamic Degree) on Brev A100 GAUGE ball clips:
Baseline (held frame 0) vs Recipe Fix (mid-fall released frame) across seeds 1-4 for Ball 1 & 2.
"""
import subprocess, sys, os, json, time

PYTHON_BIN = "/home/nail/swarm-work/raj-4/venv_cuda/bin/python"
SCORE_PY = "/home/nail/swarm-work/agy-3/cosmos-swarm/tools/nv_scoreboard/score.py"
DOVER_DIR = "/home/nail/swarm-work/raj-4/ext/DOVER"
CLIPS_DIR = "/home/nail/swarm-work/raj-3/brev_box/out"
WORK_DIR = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task68_nv_scoreboard"

ctrl_clips = [
    os.path.join(CLIPS_DIR, f"box_ctrl_b{b}_noneg_s{s}.mp4")
    for b in (1, 2) for s in (1, 2, 3, 4)
]
mid_clips = [
    os.path.join(CLIPS_DIR, f"box_mid_b{b}_noneg_s{s}.mp4")
    for b in (1, 2) for s in (1, 2, 3, 4)
]

print("=== Starting Baseline Held-Ball Scoring (8 clips) ===", flush=True)
t0 = time.time()
cmd_ctrl = [
    PYTHON_BIN, SCORE_PY,
    *ctrl_clips,
    "--dover_dir", DOVER_DIR,
    "--device", "cuda",
    "--out", os.path.join(WORK_DIR, "scores_baseline_held.json")
]
subprocess.run(cmd_ctrl, check=True)
print(f"Baseline scoring finished in {time.time()-t0:.1f}s", flush=True)

print("=== Starting Recipe Mid-Fall Scoring (8 clips) ===", flush=True)
t1 = time.time()
cmd_mid = [
    PYTHON_BIN, SCORE_PY,
    *mid_clips,
    "--dover_dir", DOVER_DIR,
    "--device", "cuda",
    "--out", os.path.join(WORK_DIR, "scores_recipe_midfall.json")
]
subprocess.run(cmd_mid, check=True)
print(f"Recipe scoring finished in {time.time()-t1:.1f}s", flush=True)

print("=== All 16 clips scored successfully! ===", flush=True)
