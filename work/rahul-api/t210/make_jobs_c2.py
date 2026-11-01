#!/usr/bin/env python3
"""Task 210 amendment 2: chunk-2 jobs. Input frame = last decoded frame of each chunk-1 clip (as tools/robot_pred/generate.py).
Usage: make_jobs_c2.py <devset_bridge> <chunk1 clips dir> <c2_inputs dir> <out jobs.jsonl>"""
import json, os, sys, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../tools/robot_pred"))
import score as S
from PIL import Image
dev, c1, inp, out = sys.argv[1:5]
os.makedirs(inp, exist_ok=True)
n = 0
with open(out, "w") as f:
    for p in sorted(glob.glob(os.path.join(c1, "t210_*.mp4"))):
        name = os.path.basename(p)[:-4]
        side = json.load(open(p[:-4] + ".json"))
        job = json.load(open(p[:-4] + ".json"))
        arm, cid = side["extra_params"]["t210_arm"], side["extra_params"]["t210_clip"]
        spec = json.load(open(os.path.join(dev, cid, "action_chunks.json")))
        last = S.read(p)[-1]
        png = os.path.abspath(os.path.join(inp, name + "_f16.png"))
        Image.fromarray(last).save(png)
        extra = {**{k: v for k, v in side["extra_params"].items() if k != "action"}, "action": spec["action_chunks"][1], "t210_chunk": 2}
        f.write(json.dumps({"name": name.replace("t210_", "t210c2_"), "prompt": side["prompt_text"], "image": png,
                            "width": 256, "height": 256, "num_frames": 17, "fps": 5, "steps": 30, "guidance": 1.0,
                            "flow_shift": 10.0, "seed": side["seed"], "negative_prompt": "", "extra_params": extra}) + "\n")
        n += 1
print(n, "jobs ->", out)
