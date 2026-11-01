#!/usr/bin/env python3
"""Follow-up to #2905: |gen - real| with an INPUT-MATCHED real reference and a real-to-real noise floor.
Written before realref/judge.json existed (09:25 UTC).
gen clips: my task-113 judge re-run (midq/judge.json; 8 F/QT pairs, ball1 s1-5, ball2 s1-3), full clip only.
reals (same judge, same question file, offsets 0/0.5 averaged):
  midq run:    real_ball1_dd32_93f (ro-1's clip)
  realref run: real_ball1_dd32_93f_rogcc (same frames, my encode), real_ball1_dd33_93f, real_ball2_dd35_93f
  (dd33 / dd35 = the exact Cosmos input frames; f0 MAE 0.0 vs raj-3's input PNGs)
Reference per pair: ball1 -> mean of real_ball1 dd32 (midq) and dd33; ball2 -> real_ball2_dd35.
usage: refdist2.py midq/judge.json realref/judge.json [--out out.json]"""
import argparse, json, os, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "midq"))
from analyze_midq import load, parse, score, SETS  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("midq"); ap.add_argument("realref"); ap.add_argument("--out")
a = ap.parse_args()
G, R = load(a.midq), load(a.realref)
gen = {}
for stem, v in G.items():
    ctl, arm, key = parse(stem)
    if ctl == "" and arm in ("F", "QT"):
        gen[(arm,) + key] = v
reals = {"b1_dd32_midq": G["real_ball1_dd32_93f"], "b1_dd32_rogcc": R["real_ball1_dd32_93f_rogcc"],
         "b1_dd33": R["real_ball1_dd33_93f"], "b2_dd35": R["real_ball2_dd35_93f"]}
sets = {"gauge_overall": SETS["gauge_overall"], "gauge_physical": SETS["gauge_physical"],
        "gauge_Q125": SETS["gauge_Q125"], "q1": [1], "q6": [6], "q18": [18]}
out = {}
for s, qs in sets.items():
    rs = {k: score(v, qs) for k, v in reals.items()}
    ref = {"ball1": (rs["b1_dd32_midq"] + rs["b1_dd33"]) / 2, "ball2": rs["b2_dd35"]}
    keys = sorted((b, n) for (arm, b, n) in gen if arm == "F" and ("QT", b, n) in gen)
    F = np.array([score(gen[("F",) + k], qs) for k in keys]); Q = np.array([score(gen[("QT",) + k], qs) for k in keys])
    r = np.array([ref[b] for b, _ in keys])
    dF, dQ = np.abs(F - r), np.abs(Q - r); d = dQ - dF
    out[s] = {"reals": rs,
              "floor_rejudge_reencode": abs(rs["b1_dd32_midq"] - rs["b1_dd32_rogcc"]),
              "floor_1frame_shift": abs(rs["b1_dd32_midq"] - rs["b1_dd33"]),
              "floor_ball1_vs_ball2": abs(ref["ball1"] - ref["ball2"]),
              "n_pairs": len(keys), "absdist_F": float(dF.mean()), "absdist_QT": float(dQ.mean()),
              "QT_minus_F": float(d.mean()), "se": float(d.std(ddof=1) / np.sqrt(len(d))),
              "n_QT_closer": int((d < 0).sum()),
              "signed_F_minus_real": float((F - r).mean()), "signed_QT_minus_real": float((Q - r).mean())}
    o = out[s]
    print(f"{s:15s} reals " + " ".join(f"{k}={v:.3f}" for k, v in rs.items()) +
          f" | floors: rejudge {o['floor_rejudge_reencode']:.3f} shift {o['floor_1frame_shift']:.3f} b1-b2 {o['floor_ball1_vs_ball2']:.3f}"
          f" | n={o['n_pairs']} |F-r| {o['absdist_F']:.3f} |QT-r| {o['absdist_QT']:.3f} d {o['QT_minus_F']:+.3f}±{o['se']:.3f}"
          f" closer {o['n_QT_closer']}/{o['n_pairs']} | signed F-r {o['signed_F_minus_real']:+.3f} QT-r {o['signed_QT_minus_real']:+.3f}")
if a.out:
    json.dump(out, open(a.out, "w"), indent=1)
