#!/usr/bin/env python3
"""Task 210 scorer. Uses the shared tools/robot_pred/score.py metrics (PSNR, SSIM, LPIPS-alex) on chunk 1:
predicted frames 1..16 vs real frames 1..16 (frame 0 is the shared real conditioning frame).
Also scores the static floor (repeat real frame 0) and a 'cond echo' check (does gen frame 0 match real frame 0).
Usage: score_t210.py <devset_bridge> <clips_dir> <out.json>"""
import json, os, sys, glob, re
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../tools/robot_pred"))
import score as S
devset, clips, outp = sys.argv[1:4]
idx = json.load(open(os.path.join(devset, "index.json")))
real = {c["id"]: S.read(os.path.join(devset, c["id"], "real.mp4"))[:17] for c in idx["clips"]}
res = {"static": {}, "clips": {}}
for cid, r in real.items():
    m = S.frame_metrics(np.repeat(r[:1], 16, axis=0), r[1:17])
    res["static"][cid] = {k: float(v.mean()) for k, v in m.items()}
for p in sorted(glob.glob(os.path.join(clips, "t210_*.mp4"))):
    name = os.path.basename(p)[:-4]
    arm, cid, seed = re.match(r"t210_(base|R|N)_(bridge_\d+)_s(\d+)$", name).groups()
    g = S.read(p)
    assert g.shape[0] == 17, (name, g.shape)
    if g.shape[1:3] != real[cid].shape[1:3]:
        raise SystemExit(f"size mismatch {name} {g.shape} vs {real[cid].shape}")
    m = S.frame_metrics(g[1:17], real[cid][1:17])
    e0 = float(np.abs(g[0].astype(float) - real[cid][0].astype(float)).mean())
    # motion amount: mean |frame t - frame 0| of the prediction vs of the real clip (does the arm move?)
    mot = float(np.abs(g[1:17].astype(float) - g[:1].astype(float)).mean())
    mot_real = float(np.abs(real[cid][1:17].astype(float) - real[cid][:1].astype(float)).mean())
    res["clips"][name] = {"arm": arm, "clip": cid, "seed": int(seed), **{k: float(v.mean()) for k, v in m.items()},
                          "frame0_mad": e0, "motion_mad": mot, "motion_mad_real": mot_real}
json.dump(res, open(outp, "w"), indent=1)
for n, v in res["clips"].items():
    print(n, {k: round(v[k], 4) for k in ("psnr", "ssim", "lpips", "frame0_mad", "motion_mad", "motion_mad_real")})
st = np.array([[v["psnr"], v["ssim"], v["lpips"]] for v in res["static"].values()])
print("static floor mean psnr/ssim/lpips", st.mean(0).round(4))
