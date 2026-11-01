#!/usr/bin/env python3
"""Predeclared analysis (hue_t24/PREREG.md addendum A2) of DOVER/DD on the blinded task-24 GAUGE-ball eval clips.
Usage: analyze_gauge_nv.py gauge_nv.json real93.json KEY [--out f.json]
KEY: JSON {code: {"arm": a, "prompt": p, "seed": s}} or CSV lines code,arm,prompt,seed (code with or without .mp4).
Unit = (prompt, seed), matched across arms; paired d = arm - base; t(n-1) one-sided 95% bound (= 90% two-sided CI)
+ 10k unit bootstrap. Motion-fidelity proxy: gap = |dd_norm - R|, R = mean dd_norm of the real 93-f GAUGE balls."""
import json, sys, csv, numpy as np
from scipy import stats
M = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_binary", "dd_norm", "gap"]
def load_key(p):
    if p.endswith(".json"):
        K = json.load(open(p))
    else:
        K = {r[0]: {"arm": r[1], "prompt": r[2], "seed": int(r[3])} for r in csv.reader(open(p)) if r and not r[0].startswith("#")}
    return {k if k.endswith(".mp4") else k + ".mp4": v for k, v in K.items()}
def paired(A, B, x, rng, margin, worse_is_up=False):
    us = sorted(u for u in A if u in B)
    d = np.array([A[u][x] - B[u][x] for u in us]); n = len(d)
    if n < 3: return None
    se = d.std(ddof=1) / np.sqrt(n); t90 = stats.t.ppf(0.95, n - 1)
    lb, ub = d.mean() - t90 * se, d.mean() + t90 * se
    bs = np.array([rng.choice(d, n).mean() for _ in range(10000)])
    o = dict(n_units=n, mean=d.mean(), se=se, ci90=[lb, ub], boot_ci95=list(np.percentile(bs, [2.5, 97.5])), n_pos=int((d > 0).sum()))
    if margin is not None:
        o["margin"] = margin
        if worse_is_up:   # gap: larger = further from real
            o["verdict"] = "non-inferior" if ub < margin else "regression" if lb > margin else "rise (significant, margin unclear)" if lb > 0 else "inconclusive"
        else:
            o["verdict"] = "non-inferior" if lb > -margin else "regression" if ub < -margin else "drop (significant, margin unclear)" if ub < 0 else "inconclusive"
    return {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in o.items()}
def main():
    S, Rr, K = json.load(open(sys.argv[1])), json.load(open(sys.argv[2])), load_key(sys.argv[3])
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    R = float(np.mean([v["dd_norm"] for v in Rr.values()]))
    arms = {}
    for code, r in S.items():
        if code not in K: print("unkeyed clip", code, file=sys.stderr); continue
        k = K[code]; v = {x: float(r[x]) for x in M[:-1]}; v["gap"] = abs(v["dd_norm"] - R)
        u = (k["prompt"], int(k["seed"]))
        if u in arms.setdefault(k["arm"], {}): sys.exit(f"duplicate unit {k['arm']} {u}")
        arms[k["arm"]][u] = v
    rng = np.random.default_rng(0)
    O = {"real_ref": {"R_dd_norm": R, "n": len(Rr), **{x: float(np.mean([v[x] for v in Rr.values()])) for x in M[:-1]}},
         "arms": {a: {"n": len(C), **{x: float(np.mean([v[x] for v in C.values()])) for x in M},
                      "per_clip_sd": {x: float(np.std([v[x] for v in C.values()], ddof=1)) for x in M}} for a, C in arms.items()},
         "paired_vs_base": {}}
    if "base" in arms:
        bm = O["arms"]["base"]["dd_norm"]
        mg = {"dover_fused": 0.02, "dd_binary": 0.10, "dd_norm": 0.15 * bm, "gap": 0.15 * bm}
        for a, C in arms.items():
            if a != "base":
                O["paired_vs_base"][a] = {x: paired(C, arms["base"], x, rng, mg.get(x), worse_is_up=(x == "gap")) for x in M}
    s = json.dumps(O, indent=1); print(s)
    if out: open(out, "w").write(s)
if __name__ == "__main__": main()
