#!/usr/bin/env python3
import json
from pathlib import Path

WORK_DIR = Path(__file__).resolve().parent
REPO_ROOT = WORK_DIR.parents[2]
IMAGE_PATH = REPO_ROOT / "work/raj-1/gauge_ball/gauge_ball1_f0_832x480.png"
PROMPT = (
    "Static frontal camera view: A 121g black ball is suspended high above a wooden plank, "
    "which is fixed on a black perforated optical table. Coefficient of friction is 0.81; "
    "coefficient of restitution is 0.58. When released, the ball undergoes free fall, "
    "followed by a sequence of successive bounces with diminishing peak heights, "
    "before finally coming to rest on the plank. Maintain structural integrity and "
    "object consistency throughout: no changing shapes, no blending, and no flashing background."
)

factors = [1.0, 0.5, 0.2, 0.05]
step_ranges = [[0, 10], [0, 20]]
seeds = [1, 2, 3]

jobs = []
for factor in factors:
    f_str = str(factor).replace(".", "p")
    for s_range in step_ranges:
        s_str = f"step{s_range[1]}"
        for seed in seeds:
            name = f"b1_att{f_str}_{s_str}_s{seed}"
            job = {
                "name": name,
                "prompt": PROMPT,
                "image": str(IMAGE_PATH),
                "width": 832,
                "height": 480,
                "num_frames": 93,
                "fps": 24,
                "steps": 35,
                "guidance": 6.0,
                "flow_shift": 10.0,
                "seed": seed,
                "negative_prompt": None,
                "extra_params": {
                    "internals": {
                        "conditioning": {
                            "attention_scale": {
                                "factor": factor,
                                "step_range": s_range
                            }
                        }
                    }
                }
            }
            jobs.append(job)

out_file = WORK_DIR / "jobs.jsonl"
with open(out_file, "w") as f:
    for j in jobs:
        f.write(json.dumps(j) + "\n")

print(f"Wrote {len(jobs)} jobs to {out_file}")
