#!/usr/bin/env python3
"""agy-5 task 170: late-only arms of the v12 settle steer (#3082/#3669).
Same vectors (raj-opus-1 steer128 @ repo), prompts, inputs, settings and seeds as rog-cc rep3082 (#3669);
only step_range / vector differ. A0, S12a4all, S12a4e, QT, R12a4all already exist (rog-cc) and are NOT resubmitted.
Usage: make_jobs.py <steer128 dir> jobs.jsonl"""
import json, sys, os
import numpy as np
src, out = sys.argv[1], sys.argv[2]
P = json.load(open(os.path.join(src, "prompts.json")))
V = {"v12": np.load(os.path.join(src, "v_L12_s0s5.npy")), "r12": np.load(os.path.join(src, "rand_L12.npy"))}
for k, v in V.items():
    assert v.shape == (24, 4096), (k, v.shape)
IMG = {"ball1": os.path.abspath(os.path.join(src, "gauge_ball1_dd33_832x480.png")),
       "ball2": os.path.abspath(os.path.join(src, "gauge_ball2_dd35_832x480.png"))}
ARMS = {"L10": ("v12", 4.0, [10, 35]),   # late-only: steps >= 10 (complement of rog-cc's S12a4e [0,10))
        "L20": ("v12", 4.0, [20, 35]),   # later-only: steps >= 20
        "RL10": ("r12", 4.0, [10, 35])}  # equal-norm random, late-only (control for L10)
SEEDS = [10, 11, 12, 13]
n = 0
with open(out, "w") as f:
    for s in SEEDS:
        for inp in ["ball1", "ball2"]:
            for arm, (vk, a, sr) in ARMS.items():
                ep = {"client": "agy-5", "internals": {"steer": {"alpha": a, "step_range": sr, "passes": "cond",
                      "vectors": [{"layer": 12, "values": [[float(f"{x:.4g}") for x in row] for row in V[vk]]}]}}}
                f.write(json.dumps({"name": f"t170_{arm}_{inp}_s{s}", "arm": arm, "input": inp, "image": IMG[inp],
                    "prompt": P["F"], "negative_prompt": None, "width": 832, "height": 480, "num_frames": 93, "fps": 24,
                    "steps": 35, "guidance": 6.0, "flow_shift": 10.0, "seed": s, "extra_params": ep,
                    "protocol": "agy-5 task 170 late-only steer (PREREG work/agy-5/t170/PREREG.md)"}) + "\n")
                n += 1
print(n, "jobs ->", out)
