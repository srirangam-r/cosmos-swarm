#!/usr/bin/env python3
"""EXPLORATORY (not in PREREG; written ~08:56 UTC before the midq judge finished), after scout-1 #2679:
score each generated clip by its distance from the real clip's judge profile in the same window,
|score(gen) - score(real)|, and compare QT vs F paired by (input, seed).
Only ball1 has a real clip, so this uses the 5 ball1 pairs (s1-5). Window: full clip and trunc36.
usage: refdist_midq.py judge.json [--out refdist.json]"""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_midq import load, parse, score, SETS  # noqa: E402

ap = argparse.ArgumentParser(); ap.add_argument("judge"); ap.add_argument("--out")
a = ap.parse_args()
pq = load(a.judge)
clips, real = {}, {}
for stem, v in pq.items():
    ctl, arm, key = parse(stem)
    if ctl == "static":
        continue
    if arm == "real":
        real[ctl] = v
    elif arm and key[0] == "ball1":
        clips[(ctl, arm, key)] = v
out = {}
for ctl in ("", "trunc36"):
    if ctl not in real:
        continue
    for s, qs in list(SETS.items()) + [(f"q{q}", [q]) for q in (1, 2, 5, 6, 18, 19)]:
        r = score(real[ctl], qs)
        keys = sorted(k for (c, arm, k) in clips if c == ctl and arm == "F" and (c, "QT", k) in clips)
        dF = np.array([abs(score(clips[(ctl, "F", k)], qs) - r) for k in keys])
        dQ = np.array([abs(score(clips[(ctl, "QT", k)], qs) - r) for k in keys])
        d = dQ - dF
        out[f"{ctl or 'full'}:{s}"] = {"n": len(keys), "real": r, "absdist_F": float(dF.mean()),
                                       "absdist_QT": float(dQ.mean()), "QT_minus_F": float(d.mean()),
                                       "se": float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else None,
                                       "n_QT_closer": int((d < 0).sum())}
for k, v in out.items():
    print(f"{k:24s} real {v['real']:.3f}  |F-real| {v['absdist_F']:.3f}  |QT-real| {v['absdist_QT']:.3f}  "
          f"d {v['QT_minus_F']:+.3f}±{(v['se'] or float('nan')):.3f}  QT closer {v['n_QT_closer']}/{v['n']}")
if a.out:
    json.dump(out, open(a.out, "w"), indent=1)
