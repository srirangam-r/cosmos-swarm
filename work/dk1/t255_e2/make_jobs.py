"""Task 255 E2: zero-action drift (CoCo https://arxiv.org/abs/2608.04653 'drift energy', ported to Nano FD on Bridge).

Arms per clip (24 Bridge dev clips, chunk 1 only, same first frame + prompt as E1):
  OWN  = clip's real chunk-0 actions (identical request to E1's OWN, re-generated on ONE stack with ZERO)
  ZERO = "stay still": physical zero translation, identity rotation (rot6d [1,0,0,0,1,0]),
         gripper held at the clip's own chunk-0 t0 value (all 24 are open), then quantile-normalised
         with tools/robot_pred/bridge_orig_lerobot_stats.json exactly as build_devset.normalize.
Seeds 1,2,3; extra_params.noise={"device":"cpu"} so seeds pair across arms and with E1's q8 clips.
Model-card FD settings as E1: 17 f @ 5 fps, 256x256, 30 steps, guidance 1.0, flow_shift 10.
Plus 2 determinism duplicates (OWN s1, ZERO s1 of clip 0).
Usage: python3 make_jobs.py <devset_dir> <stats.json> > jobs.jsonl
"""
import json, os, sys
import numpy as np

dev, statsp = sys.argv[1:3]
ids = [c["id"] for c in json.load(open(os.path.join(dev, "index.json")))["clips"]]
S = json.load(open(statsp))
Q01, Q99 = np.array(S["q01"], np.float32), np.array(S["q99"], np.float32)
SEEDS = [1, 2, 3]
EMPTY = "A robot arm performs a manipulation task on a tabletop."  # same amendment as E1 (queue rejects empty prompts)


def normalize(a):
    return 2.0 * (a - Q01) / np.clip(Q99 - Q01, 1e-8, None) - 1.0


def zero_chunk(own_chunk):
    T = len(own_chunk)
    raw = np.zeros((T, 10), np.float32)
    raw[:, 3] = 1.0  # rot6d col0 = (1,0,0)
    raw[:, 7] = 1.0  # rot6d col1 = (0,1,0)
    z = normalize(raw)
    z[:, 9] = own_chunk[0][9]  # hold gripper state (already normalised, +1 = open)
    return z.tolist()


def job(name, cid, arm, seed):
    own = json.load(open(os.path.join(dev, cid, "action_chunks.json")))
    act = own["action_chunks"][0] if arm == "own" else zero_chunk(own["action_chunks"][0])
    extra = {"action_mode": "forward_dynamics", "domain_name": own["domain_name"],
             "action_chunk_size": own["action_chunk_size"], "image_size": own["image_size"],
             "view_point": own["view_point"], "action": act, "guardrails": True,
             "noise": {"device": "cpu"}}
    return {"name": name, "prompt": own["prompt"].strip() or EMPTY,
            "image": os.path.abspath(os.path.join(dev, cid, "first_frame.png")),
            "width": 256, "height": 256, "num_frames": own["action_chunk_size"] + 1, "fps": own["fps"],
            "steps": 30, "guidance": 1.0, "flow_shift": 10.0, "seed": seed, "extra_params": extra,
            "meta": {"clip": cid, "arm": arm, "task": 255, "exp": "E2"}}


out = []
for s in SEEDS:
    for cid in ids:
        for arm in ("own", "zero"):
            out.append(job(f"t255e2_{cid}_{arm}_s{s}", cid, arm, s))
for arm in ("own", "zero"):
    out.append(job(f"t255e2_{ids[0]}_{arm}_s1_dup", ids[0], arm, 1))
for j in out:
    print(json.dumps(j))
