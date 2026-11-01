#!/usr/bin/env python3
"""
Generate proxy videos and queue JSONL job specifications for Task 276.
Arms:
  - nphys: 6 frames x seeds 1-3 with P = P_real_s from frames.json
  - nphys_x17: 6 frames x seed 1 with P = 1.7 * P_real_s (wrong-physics control)
"""

import json
import os
from pathlib import Path
import sys

# Ensure cosmos-swarm is on PYTHONPATH
REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tools.nano_phys.proxy import generate_pendulum_proxy
from tools.nano_phys.runner import sigma_to_step

T276_DIR = Path(__file__).resolve().parent
FRAMES_FILE = T276_DIR / "frames.json"
PROXIES_DIR = T276_DIR / "proxies"
PROXIES_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = (
    "Static frontal camera view: A 318g black metal ball is fixed to the tip of a lightweight rigid rod, "
    "which rotates freely about a stationary horizontal axle mounted between two vertical posts atop a "
    "black perforated optical table. Initially, the rod angle is 10 degree, with the ball extending out to "
    "one side. Upon release, the ball follows pendulum motion: it accelerates downward past the black vertical "
    "posts, ascends on the opposite side, and continues oscillating back and forth over numerous cycles, "
    "its amplitude slowly and gradually diminishing due to friction. Maintain structural integrity and object "
    "consistency throughout: no changing shapes, no blending, and no flashing background."
)

def main():
    frames = json.load(open(FRAMES_FILE))
    
    start_step = sigma_to_step(0.90, steps=35) # step 19 (sigma = 0.89844)
    assert start_step == 19, f"Expected step 19 for sigma 0.90, got {start_step}"

    nphys_jobs = []
    nphys_x17_jobs = []

    print(f"Generating proxies and job specs for {len(frames)} frames...")

    for f_info in frames:
        fid = f_info["id"] # e.g. "real_09"
        img_rel = f_info["image"] # e.g. "inputs/f0_real_09.png"
        img_path = T276_DIR / img_rel
        pivot = tuple(f_info["pivot"])
        bob = tuple(f_info["bob"])
        p_real = float(f_info["P_real_s"])
        p_x17 = round(p_real * 1.7, 5)

        # 1. Generate nphys proxy
        proxy_nphys_path = PROXIES_DIR / f"proxy_{fid}_nphys.mp4"
        if not proxy_nphys_path.exists():
            print(f"  Generating {proxy_nphys_path.name} (P={p_real:.4f}s)...")
            generate_pendulum_proxy(
                image_path=img_path,
                out_path=proxy_nphys_path,
                pivot=pivot,
                bob=bob,
                period=p_real,
                num_frames=93,
                fps=24,
                width=832,
                height=480,
            )
        else:
            print(f"  Proxy {proxy_nphys_path.name} already exists.")

        # 2. Generate nphys_x17 control proxy
        proxy_x17_path = PROXIES_DIR / f"proxy_{fid}_nphys_x17.mp4"
        if not proxy_x17_path.exists():
            print(f"  Generating {proxy_x17_path.name} (P={p_x17:.4f}s)...")
            generate_pendulum_proxy(
                image_path=img_path,
                out_path=proxy_x17_path,
                pivot=pivot,
                bob=bob,
                period=p_x17,
                num_frames=93,
                fps=24,
                width=832,
                height=480,
            )
        else:
            print(f"  Proxy {proxy_x17_path.name} already exists.")

        # 3. Create job specs for nphys (seeds 1, 2, 3)
        for s in (1, 2, 3):
            job_name = f"t276_{fid}_nphys_s{s}"
            job = {
                "name": job_name,
                "prompt": PROMPT,
                "negative_prompt": None,
                "image": str(img_path.resolve()),
                "files": [str(proxy_nphys_path.resolve())],
                "width": 832,
                "height": 480,
                "num_frames": 93,
                "fps": 24,
                "steps": 35,
                "guidance": 6.0,
                "flow_shift": 10.0,
                "seed": s,
                "extra_params": {
                    "client": "nano_phys",
                    "noise": {"device": "cpu"},
                    "latent": {
                        "ref": proxy_nphys_path.name,
                        "start_step": start_step,
                        "init": "noised",
                    },
                },
            }
            nphys_jobs.append(job)

        # 4. Create job spec for nphys_x17 (seed 1)
        job_x17_name = f"t276_{fid}_nphys_x17_s1"
        job_x17 = {
            "name": job_x17_name,
            "prompt": PROMPT,
            "negative_prompt": None,
            "image": str(img_path.resolve()),
            "files": [str(proxy_x17_path.resolve())],
            "width": 832,
            "height": 480,
            "num_frames": 93,
            "fps": 24,
            "steps": 35,
            "guidance": 6.0,
            "flow_shift": 10.0,
            "seed": 1,
            "extra_params": {
                "client": "nano_phys",
                "noise": {"device": "cpu"},
                "latent": {
                    "ref": proxy_x17_path.name,
                    "start_step": start_step,
                    "init": "noised",
                },
            },
        }
        nphys_x17_jobs.append(job_x17)

    # Save JSONL files
    nphys_out = T276_DIR / "jobs_nphys.jsonl"
    with open(nphys_out, "w") as f:
        for j in nphys_jobs:
            f.write(json.dumps(j) + "\n")
    print(f"Wrote {len(nphys_jobs)} jobs to {nphys_out}")

    x17_out = T276_DIR / "jobs_nphys_x17.jsonl"
    with open(x17_out, "w") as f:
        for j in nphys_x17_jobs:
            f.write(json.dumps(j) + "\n")
    print(f"Wrote {len(nphys_x17_jobs)} jobs to {x17_out}")

    all_out = T276_DIR / "jobs_t276_all.jsonl"
    with open(all_out, "w") as f:
        for j in nphys_jobs + nphys_x17_jobs:
            f.write(json.dumps(j) + "\n")
    print(f"Wrote {len(nphys_jobs) + len(nphys_x17_jobs)} jobs to {all_out}")

if __name__ == "__main__":
    main()
