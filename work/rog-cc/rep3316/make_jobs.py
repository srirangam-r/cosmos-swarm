#!/usr/bin/env python3
"""rep3316: fresh-seed replication of #3316 (Rule R settles mid-fall ball) with a length-matched neutral control N.
Base F prompt and settings copied verbatim from work/raj-api-3/t138/jobs.jsonl (arm F). Writes jobs.jsonl."""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
F = [json.loads(l) for l in open(os.path.join(D, "../../raj-api-3/t138/jobs.jsonl")) if json.loads(l)["arm"] == "F"][0]["prompt"]
R = " By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy and come to rest, staying completely still for the rest of the video."
N = " The scene is lit by soft, even lighting that stays constant throughout the video, and the colours remain natural and true to life, with realistic textures and fine surface detail on every object."
out = open(os.path.join(D, "jobs.jsonl"), "w")
for img, b in (("gauge_ball1_dd33_832x480.png", "ball1"), ("gauge_ball2_dd35_832x480.png", "ball2")):
    for s in (41, 42, 43):
        for a, p in (("F", F), ("R", F + R), ("N", F + N)):
            j = dict(image=os.path.join(D, img), width=832, height=480, num_frames=93, fps=24, steps=35, guidance=6.0,
                     flow_shift=10.0, negative_prompt=None, prompt=p, seed=s, arm=a, name=f"rep3316_{a}_{b}_s{s}",
                     protocol="rep3316 (rog-cc): fresh-seed replication of #3316 + length-matched neutral N")
            out.write(json.dumps(j) + "\n")
