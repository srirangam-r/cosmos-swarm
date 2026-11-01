"""Task 255 E1: noise vs action share in Nano forward dynamics (Bridge dev set, chunk 1 only).

Arms per clip i (24 clips): OWN = clip i's real chunk-0 actions; SWAP = chunk-0 actions of clip (i+12)%24.
Same first frame and same prompt in both arms; seeds 1,2,3; noise drawn on CPU (shared across arms).
Model-card FD settings: 17 frames @ 5 fps, 256x256, 30 steps, guidance 1.0, flow_shift 10 (ignored by Karras board servers).
Plus 2 determinism duplicates (OWN s1 of clips 0 and 1, different job name).
Usage: python3 make_jobs.py <devset_dir> > jobs.jsonl
"""
import json, os, sys

dev = sys.argv[1]
ids = [c["id"] for c in json.load(open(os.path.join(dev, "index.json")))["clips"]]
N = len(ids)
SEEDS = [1, 2, 3]
# Amendment (before any E1 data beyond the 2-clip pilot): the queue rejects empty prompts; 11/24 Bridge clips have none.
EMPTY = "A robot arm performs a manipulation task on a tabletop."


def job(name, cid, donor, seed):
    own = json.load(open(os.path.join(dev, cid, "action_chunks.json")))
    don = json.load(open(os.path.join(dev, donor, "action_chunks.json")))
    extra = {"action_mode": "forward_dynamics", "domain_name": own["domain_name"],
             "action_chunk_size": own["action_chunk_size"], "image_size": own["image_size"],
             "view_point": own["view_point"], "action": don["action_chunks"][0], "guardrails": True,
             "noise": {"device": "cpu"}}
    return {"name": name, "prompt": own["prompt"].strip() or EMPTY, "image": os.path.abspath(os.path.join(dev, cid, "first_frame.png")),
            "width": 256, "height": 256, "num_frames": own["action_chunk_size"] + 1, "fps": own["fps"],
            "steps": 30, "guidance": 1.0, "flow_shift": 10.0, "seed": seed, "extra_params": extra,
            "meta": {"clip": cid, "action_donor": donor}}


out = []
for s in SEEDS:
    for i, cid in enumerate(ids):
        out.append(job(f"t255_{cid}_own_s{s}", cid, cid, s))
        out.append(job(f"t255_{cid}_swap_s{s}", cid, ids[(i + N // 2) % N], s))
for i in (0, 1):
    out.append(job(f"t255_{ids[i]}_own_s1_dup", ids[i], ids[i], 1))
for j in out:
    print(json.dumps(j))
