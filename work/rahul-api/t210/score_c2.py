#!/usr/bin/env python3
"""Task 210 amendment 2 scorer: rollout = chunk1 (17 f) + chunk2[1:] (16 f) vs real 33 f.
Writes two score files in score_t210.py's format so analyze_t210.py runs unchanged:
<out>_all.json (predicted frames 1-32) and <out>_c2.json (frames 17-32 only).
Usage: score_c2.py <devset_bridge> <chunk1 clips> <chunk2 clips> <out prefix>"""
import json, os, sys, glob, re
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../tools/robot_pred"))
import score as S
dev, c1, c2, pre = sys.argv[1:5]
idx = json.load(open(os.path.join(dev, "index.json")))
real = {c["id"]: S.read(os.path.join(dev, c["id"], "real.mp4"))[:33] for c in idx["clips"]}
outs = {w: {"static": {}, "clips": {}} for w in ("all", "c2")}
win = {"all": (1, 33), "c2": (17, 33)}
for cid, r in real.items():
    for w, (a, b) in win.items():
        m = S.frame_metrics(np.repeat(r[:1], b - a, axis=0), r[a:b])
        outs[w]["static"][cid] = {k: float(v.mean()) for k, v in m.items()}
for p in sorted(glob.glob(os.path.join(c2, "t210c2_*.mp4"))):
    name2 = os.path.basename(p)[:-4]; name1 = name2.replace("t210c2_", "t210_")
    arm, cid, seed = re.match(r"t210c2_(base|R|N)_(bridge_\d+)_s(\d+)$", name2).groups()
    g1, g2 = S.read(os.path.join(c1, name1 + ".mp4")), S.read(p)
    assert len(g1) == 17 and len(g2) == 17, name2
    roll = np.concatenate([g1, g2[1:]]); r = real[cid]
    assert len(r) == 33 and roll.shape == r.shape, (name2, roll.shape, r.shape)
    for w, (a, b) in win.items():
        m = S.frame_metrics(roll[a:b], r[a:b])
        outs[w]["clips"][name1] = {"arm": arm, "clip": cid, "seed": int(seed), **{k: float(v.mean()) for k, v in m.items()},
            "motion_mad": float(np.abs(roll[a:b].astype(float) - roll[:1].astype(float)).mean()),
            "motion_mad_real": float(np.abs(r[a:b].astype(float) - r[:1].astype(float)).mean()),
            "c2_cond_vs_c1_last_mad": float(np.abs(g2[0].astype(float) - g1[-1].astype(float)).mean())}
for w in outs:
    json.dump(outs[w], open(f"{pre}_{w}.json", "w"), indent=1)
print("scored", len(outs["all"]["clips"]), "rollouts; max |c2 f0 - c1 f16| MAD",
      round(max(v["c2_cond_vs_c1_last_mad"] for v in outs["all"]["clips"].values()), 2))
