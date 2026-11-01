#!/usr/bin/env python3
"""Pair HUE (tools/hue_judge, gauge_ball questions, CPU, offsets 0/0.5 averaged) QT vs F and QS vs F by (input, seed)."""
import json, os, re, sys
import numpy as np
R = json.load(open(os.path.join(os.path.dirname(__file__), "res.json")))["results"]
by = {}
for r in R:
    s = os.path.basename(r["clip"])[:-4]
    v = dict(r["summary"]); v.update({f"Q{x['id']}": x["p_yes"] for x in r["rows"]})
    by.setdefault(s, []).append(v)
M = {s: {k: float(np.mean([x[k] for x in v])) for k in v[0]} for s, v in by.items()}
def key(s):
    m = re.search(r"_(F|QT|QS)_(ball\d)_fps24_93f_s(\d)", s)
    return (m.group(1), m.group(2), int(m.group(3))) if m else None
arms = {}
for s in M:
    k = key(s)
    if k: arms[k] = s
KEYS = ["overall", "Physical Laws", "Visual Integrity", "Geometric Reasoning", "Semantic Alignment", "Q4", "Q6", "Q12"]
out = {}
for arm in ("QT", "QS"):
    pairs = [(arms[("F", b, sd)], arms[(a, b, sd)]) for (a, b, sd) in arms if a == arm and ("F", b, sd) in arms]
    res = {"n": len(pairs), "pairs": pairs}
    for k in KEYS:
        d = np.array([M[t][k] - M[f][k] for f, t in pairs])
        res[k] = {"F": float(np.mean([M[f][k] for f, _ in pairs])), arm: float(np.mean([M[t][k] for _, t in pairs])),
                  "diff": float(d.mean()), "se": float(d.std(ddof=1) / np.sqrt(len(d))) if len(d) > 1 else None,
                  "n_pos": int((d > 0).sum())}
    out[f"{arm}-F"] = res
out["real_ref"] = {k: M["real_ball1_dd32_93f"][k] for k in KEYS}
json.dump(out, open(os.path.join(os.path.dirname(__file__), "pair.json"), "w"), indent=1)
for c, res in out.items():
    if c == "real_ref":
        print("real_ref", {k: round(v, 3) for k, v in res.items()}); continue
    print(f"{c} n={res['n']}")
    for k in KEYS:
        x = res[k]; a = [z for z in x if z not in ('F','diff','se','n_pos')][0]
        print(f"  {k:20s} F {x['F']:.3f}  {a} {x[a]:.3f}  diff {x['diff']:+.3f} ± {x['se']:.3f}  ({x['n_pos']}/{res['n']} up)")
