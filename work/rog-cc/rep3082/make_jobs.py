#!/usr/bin/env python3
"""rog-cc replication of raj-opus-1 #3082 (settle steering direction) on NEW seeds 10-13.
Vectors and prompts are read from raj-opus-1's committed files (work/raj-opus-1/steer128 @ 410129f):
v_L12_s0s5.npy (QT-F mean, [24,4096]), rand_L12.npy (per-frame-norm-matched random), prompts.json, input PNGs.
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
# arm -> (prompt key, steer spec or None)
ARMS = {"A0":      ("F",  ("v12", 0.0, [0, 35])),
        "S12a4all": ("F",  ("v12", 4.0, [0, 35])),
        "R12a4all": ("F",  ("r12", 4.0, [0, 35])),
        "S12a4e":  ("F",  ("v12", 4.0, [0, 10])),
        "QT":      ("QT", None)}
SEEDS = [10, 11, 12, 13]
n = 0
with open(out, "w") as f:
    for s in SEEDS:
        for inp in ["ball1", "ball2"]:
            for arm, (pk, st) in ARMS.items():
                ep = {"client": "rog-cc"}
                if st is not None:
                    vk, a, sr = st
                    ep["internals"] = {"steer": {"alpha": a, "step_range": sr, "passes": "cond",
                        "vectors": [{"layer": 12, "values": [[float(f"{x:.4g}") for x in row] for row in V[vk]]}]}}
                f.write(json.dumps({"name": f"r3082_{arm}_{inp}_s{s}", "arm": arm, "input": inp, "image": IMG[inp],
                    "prompt": P[pk], "negative_prompt": None, "width": 832, "height": 480, "num_frames": 93, "fps": 24,
                    "steps": 35, "guidance": 6.0, "flow_shift": 10.0, "seed": s, "extra_params": ep,
                    "protocol": "rog-cc replication of #3082 (PREREG work/rog-cc/rep3082/PREREG.md)"}) + "\n")
                n += 1
print(n, "jobs ->", out)
