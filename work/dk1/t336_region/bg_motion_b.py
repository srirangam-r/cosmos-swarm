#!/usr/bin/env python3
"""t336b secondary readout (written 21:06 UTC 2026-11-01, BEFORE any t336b clip exists; after dk-scout #6966).
Outside-box motion = mean frame-to-frame |grey diff| outside the t336 pendulum box (same box and code as rev6767
bg_motion.py, 9739ea5: plain 1.50, nphys 0.63 grey/frame over 6 scenes). Per arm (plain, nphys, inj19, inj27; 4 scenes x
seeds 1-3) mean and per-scene means. Prediction contrast (dk-scout #6966):
  FI (static-still account): inj19/inj27 ~ plain >> nphys   -> report ratio (inj - nphys)/(plain - nphys) near 1
  A  (box/attention coupling): inj19/inj27 ~ nphys          -> ratio near 0
Descriptive (no decision rule); motion does not track DOVER per clip (#6932 r=.09).
usage: bg_motion_b.py <t336b clips dir> <refs dir (t276 plain/nphys mp4)> <out.json>"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "rev6767"))
from swap_box import read
meta = json.load(open(HERE.parent / "rev6767/out/swap_meta.json"))["clips"]
clips, refs, outp = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
SC = ("12", "17", "18", "19"); ARMS = ("plain", "nphys", "inj19", "inj27")
rows = {}
for sc in SC:
    for s in (1, 2, 3):
        x0, y0, x1, y1 = meta[f"{sc}_s{s}"]["box"]; out = np.ones((480, 832), bool); out[y0:y1, x0:x1] = False
        for arm in ARMS:
            p = (refs / f"t276_real_{sc}_{arm}_s{s}.mp4") if arm in ("plain", "nphys") else (clips / f"t336b_real_{sc}_{arm}_s{s}.mp4")
            if not p.exists(): continue
            g = read(p).astype(np.float32).mean(-1)
            rows[f"{sc}_s{s}_{arm}"] = float(np.abs(np.diff(g, axis=0)).mean(0)[out].mean())
res = {"rows": rows, "arms": {}}
for arm in ARMS:
    v = [rows[k] for k in rows if k.endswith("_" + arm)]
    if v: res["arms"][arm] = {"n": len(v), "mean": round(float(np.mean(v)), 4),
                              "per_scene": {sc: round(float(np.mean([rows[k] for k in rows if k.startswith(sc) and k.endswith("_" + arm)])), 4) for sc in SC if any(k.startswith(sc) and k.endswith("_" + arm) for k in rows)}}
A = res["arms"]
for arm in ("inj19", "inj27"):
    if arm in A and "plain" in A and "nphys" in A:
        A[arm]["ratio_FI_vs_A"] = round((A[arm]["mean"] - A["nphys"]["mean"]) / (A["plain"]["mean"] - A["nphys"]["mean"]), 3)
json.dump(res, open(outp, "w"), indent=1)
print(json.dumps(res["arms"], indent=1))
