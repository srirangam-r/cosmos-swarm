"""Task 255 E3: action-contrast guidance (FreeAction https://arxiv.org/abs/2509.24241) for Nano FD on Bridge.
Design FROZEN in this file + analyze.py before any E3 clip exists. Prior-work note: board #5420. Hook: action_cfg.py.

v = v(a) + s * (v(a) - v(a'))   (extra_params.action_cfg; request guidance_scale stays 1, the hook sets 1+s)

Arms per clip (24 Bridge dev clips, chunk 1, same first frame + prompt + settings as E1/E2):
  plain      own action, no action_cfg                         (= E2 OWN request; regenerated on the E3 stack)
  neg1       own action, a' = physical negation of a, s = 1
  neg3       own action, a' = physical negation of a, s = 3
  zero1      own action, a' = physical zero (E2's ZERO chunk), s = 1
  swap       donor action (rog1 E1 donor = clip (i + N/2) mod N), no action_cfg
  swap_neg3  donor action, a' = physical negation of the donor action, s = 3
  ctrl       own action, a' = a (explicit), s = 3, seed 1 only  -> must reproduce plain (hook wiring control)
Physical negation: de-normalise (bridge_orig_lerobot quantile stats), translation -> -translation, rotation R -> R^T
(rot6d re-encoded with the same convention, so it is convention-independent), gripper held at the clip's own value,
re-normalise. (FreeAction negates its action vector; Bridge actions here are quantile-normalised, where token
negation is not the opposite motion, so the opposite motion is built in physical space.)
Seeds 1,2,3; noise.device=cpu. 17 f @ 5 fps, 256x256, 30 steps, guidance 1.0 (flow_shift 10 sent; ignored by the
board's Karras/UniPC server, #2870). Order: all seed-1 jobs first, then seed 2, then seed 3 (partial runs stay usable).
Usage: python3 make_jobs.py <devset_dir> <stats.json> > jobs.jsonl
"""
import json, os, sys
import numpy as np

dev, statsp = sys.argv[1:3]
ids = [c["id"] for c in json.load(open(os.path.join(dev, "index.json")))["clips"]]
N = len(ids)
S = json.load(open(statsp))
Q01, Q99 = np.array(S["q01"], np.float64), np.array(S["q99"], np.float64)
SEEDS = [1, 2, 3]
EMPTY = "A robot arm performs a manipulation task on a tabletop."
ARMS = ["plain", "neg1", "neg3", "zero1", "swap", "swap_neg3"]


def normalize(a):
    return 2.0 * (a - Q01) / np.clip(Q99 - Q01, 1e-8, None) - 1.0


def denormalize(z):
    return (np.asarray(z, np.float64) + 1.0) / 2.0 * np.clip(Q99 - Q01, 1e-8, None) + Q01


def r6_to_R(r6):
    c0, c1 = r6[:3], r6[3:6]
    b0 = c0 / np.linalg.norm(c0)
    c1 = c1 - (b0 @ c1) * b0
    b1 = c1 / np.linalg.norm(c1)
    return np.stack([b0, b1, np.cross(b0, b1)], axis=1)  # columns


def R_to_r6(R):
    return np.concatenate([R[:, 0], R[:, 1]])


def phys_neg(chunk):
    raw = denormalize(chunk)
    out = raw.copy()
    out[:, :3] = -raw[:, :3]
    for t in range(len(raw)):
        out[t, 3:9] = R_to_r6(r6_to_R(raw[t, 3:9]).T)
    z = normalize(out)
    z[:, 9] = np.asarray(chunk)[:, 9]  # gripper is a state, not a delta: keep it
    return z.astype(np.float32).tolist()


def phys_zero(chunk):
    T = len(chunk)
    raw = np.zeros((T, 10), np.float64)
    raw[:, 3] = 1.0
    raw[:, 7] = 1.0
    z = normalize(raw)
    z[:, 9] = chunk[0][9]  # identical to E2's ZERO chunk
    return z.astype(np.float32).tolist()


def chunk_of(cid):
    a = json.load(open(os.path.join(dev, cid, "action_chunks.json")))
    return a, a["action_chunks"][0]


def job(cid, arm, seed, i):
    meta, own = chunk_of(cid)
    donor = ids[(i + N // 2) % N]
    act = chunk_of(donor)[1] if arm.startswith("swap") else own
    extra = {"action_mode": "forward_dynamics", "domain_name": meta["domain_name"],
             "action_chunk_size": meta["action_chunk_size"], "image_size": meta["image_size"],
             "view_point": meta["view_point"], "action": act, "guardrails": True, "noise": {"device": "cpu"}}
    if arm in ("neg1", "neg3", "swap_neg3"):
        extra["action_cfg"] = {"scale": 1.0 if arm == "neg1" else 3.0, "alt": phys_neg(act)}
    elif arm == "zero1":
        extra["action_cfg"] = {"scale": 1.0, "alt": phys_zero(own)}
    elif arm == "ctrl":
        extra["action_cfg"] = {"scale": 3.0, "alt": own}
    return {"name": f"t255e3_{cid}_{arm}_s{seed}", "prompt": meta["prompt"].strip() or EMPTY,
            "image": os.path.abspath(os.path.join(dev, cid, "first_frame.png")),
            "width": 256, "height": 256, "num_frames": meta["action_chunk_size"] + 1, "fps": meta["fps"],
            "steps": 30, "guidance": 1.0, "flow_shift": 10.0, "seed": seed, "extra_params": extra,
            "meta": {"clip": cid, "arm": arm, "task": 255, "exp": "E3",
                     "action_donor": donor if arm.startswith("swap") else cid}}


out = []
for s in SEEDS:
    for i, cid in enumerate(ids):
        for arm in ARMS + (["ctrl"] if s == 1 else []):
            out.append(job(cid, arm, s, i))
for j in out:
    print(json.dumps(j))
