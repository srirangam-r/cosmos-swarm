#!/usr/bin/env python3
"""Build queue jobs for task 133: 16 task-24 HUE T2V prompts x {base, R, N} x seeds 1-3 (T2V, no image).
Usage: make_jobs.py <dir with task-24 base args.json> jobs.jsonl"""
import json, sys, glob, os
R = (" By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy "
     "and come to rest, staying completely still for the rest of the video.")
N = (" The scene is lit by soft, even lighting that stays constant throughout the video, and the colours remain "
     "natural and true to life, with realistic textures and fine surface detail on every object.")
SUFFIX = {"base": "", "R": R, "N": N}
src, out = sys.argv[1], sys.argv[2]
prompts = {}
for p in sorted(glob.glob(os.path.join(src, "*_s1.args.json"))):
    a = json.load(open(p)); prompts[os.path.basename(p)[:-len("_s1.args.json")]] = a["prompt"].strip()
assert len(prompts) == 16, len(prompts)
with open(out, "w") as f:
    for arm in ["base", "R", "N"]:
        for s in (1, 2, 3):
            for k, pr in prompts.items():
                f.write(json.dumps({"name": f"es_{arm}_{k}_s{s}", "arm": arm, "hue_sample": k,
                    "prompt": pr + SUFFIX[arm], "negative_prompt": "", "image": None, "width": 832, "height": 480,
                    "num_frames": 93, "fps": 24, "steps": 35, "guidance": 6.0, "flow_shift": 10.0, "seed": s,
                    "protocol": "task133 end-state rule on unseen HUE T2V prompts (rog-cc PREREG)"}) + "\n")
print(len(prompts) * 9, "jobs ->", out)
print("words R", len(R.split()), "N", len(N.split()))
