#!/usr/bin/env python3
"""Task 210: Bridge forward-dynamics jobs, chunk 1 only, arms base / R / N, for the shared Cosmos queue.
Usage: make_jobs.py <devset_bridge dir> <out jobs.jsonl> [--seeds 0 1 2] [--arms base R N] [--only id ...]
Each job: real first_frame.png + action chunk 0 (16x10), 17 frames @ 5 fps, 30 steps, CFG 1.0, flow_shift 10 (requested;
board servers use Karras sigmas, #2870), no negative prompt. R and N are the exact task-133 suffixes (rog-cc make_jobs.py)."""
import argparse, json, os
R = (" By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy "
     "and come to rest, staying completely still for the rest of the video.")
N = (" The scene is lit by soft, even lighting that stays constant throughout the video, and the colours remain "
     "natural and true to life, with realistic textures and fine surface detail on every object.")
SUFFIX = {"base": None, "R": R, "N": N}

DEFAULT = "A robot manipulates an object."  # NVIDIA notebook build_action_prompt default (as in DROID gen_vllm.py)

def arm_prompt(p, arm):
    p = p.strip() or DEFAULT  # 10/24 Bridge clips have no instruction; the server rejects an empty prompt
    if SUFFIX[arm] is None:
        return p  # devset prompt verbatim (what a user sends)
    if not p.endswith((".", "!", "?")):
        p += "."
    return p + SUFFIX[arm]

ap = argparse.ArgumentParser()
ap.add_argument("devset"); ap.add_argument("out")
ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2])
ap.add_argument("--arms", nargs="+", default=["base", "R", "N"])
ap.add_argument("--only", nargs="*")
a = ap.parse_args()
idx = json.load(open(os.path.join(a.devset, "index.json")))
n = 0
with open(a.out, "w") as f:
    for s in a.seeds:
        for arm in a.arms:
            for c in idx["clips"]:
                if a.only and c["id"] not in a.only:
                    continue
                d = os.path.join(a.devset, c["id"])
                spec = json.load(open(os.path.join(d, "action_chunks.json")))
                extra = {"action_mode": "forward_dynamics", "domain_name": spec["domain_name"],
                         "action_chunk_size": spec["action_chunk_size"], "image_size": spec["image_size"],
                         "view_point": spec["view_point"], "action": spec["action_chunks"][0], "guardrails": False,
                         "t210_arm": arm, "t210_clip": c["id"]}
                f.write(json.dumps({"name": f"t210_{arm}_{c['id']}_s{s}", "prompt": arm_prompt(spec["prompt"], arm),
                                    "image": os.path.abspath(os.path.join(d, "first_frame.png")),
                                    "width": 256, "height": 256, "num_frames": spec["action_chunk_size"] + 1,
                                    "fps": spec["fps"], "steps": 30, "guidance": 1.0, "flow_shift": 10.0, "seed": s,
                                    "negative_prompt": "", "extra_params": extra}) + "\n")
                n += 1
print(n, "jobs ->", a.out)
