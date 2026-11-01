#!/usr/bin/env python3
"""Predeclared task-24 NVIDIA-scoreboard analysis (PREREG.md addendum A1). Usage: analyze_nv.py res_nv_dir [--out f.json]
Same unit/aggregation as analyze_t24.py: clip value (DOVER = mean of 3 fragment draws) -> mean over seeds {1,2} per prompt
-> paired d_p = arm - base over the 16 prompts; t(15) one-sided 95% lower bound (= 90% two-sided CI) + 10k prompt bootstrap."""
import json, sys, re, os, numpy as np
from scipy import stats
METRICS = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_binary", "dd_norm"]
MARGIN_ABS = {"dover_fused": 0.02, "dd_binary": 0.10}   # PROPOSED (not human-approved)
MARGIN_REL = {"dd_norm": 0.15}                          # 15% of the base arm's mean, PROPOSED
pat = re.compile(r"((?:physics|robot)_\d+)_s(\d+)\.mp4$")
def load(path):
    C = {}
    for k, r in json.load(open(path)).items():
        m = pat.search(k)
        if m and isinstance(r, dict): C[(m.group(1), int(m.group(2)))] = {x: float(r[x]) for x in METRICS if x in r}
    return C
def prompt_scores(C, seeds=(1, 2)):
    P = {}
    for (p, s), v in C.items():
        if s in seeds: P.setdefault(p, []).append(v)
    return {p: {x: float(np.mean([v[x] for v in L])) for x in METRICS if all(x in v for v in L)} for p, L in P.items() if len(L) == len(seeds)}
def paired(A, B, x, rng, margin=None):
    ps = sorted(p for p in A if p in B and x in A[p] and x in B[p])
    d = np.array([A[p][x] - B[p][x] for p in ps]); n = len(d)
    if n < 3: return None
    se = d.std(ddof=1) / np.sqrt(n); t90 = stats.t.ppf(0.95, n - 1); t95 = stats.t.ppf(0.975, n - 1)
    bs = np.array([rng.choice(d, n).mean() for _ in range(10000)])
    o = {"n_prompts": n, "mean": d.mean(), "se": se, "ci90": [d.mean() - t90 * se, d.mean() + t90 * se],
         "ci95": [d.mean() - t95 * se, d.mean() + t95 * se], "boot_ci95": list(np.percentile(bs, [2.5, 97.5])),
         "n_pos": int((d > 0).sum()), "per_prompt": dict(zip(ps, d.round(4).tolist()))}
    if margin is not None:
        lb, ub = o["ci90"]; o["margin"] = margin
        o["verdict"] = ("non-inferior" if lb > -margin else "regression" if ub < -margin else "drop (significant, within margin unclear)" if ub < 0 else "inconclusive")
    return {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in o.items()}
def main():
    rd = sys.argv[1]; out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    rng = np.random.default_rng(0)
    arms = {f[:-5]: load(os.path.join(rd, f)) for f in sorted(os.listdir(rd)) if f.endswith(".json")}
    R = {"arms": {}, "seed_noise": {}, "paired_vs_base": {}}
    for a, C in arms.items():
        P = prompt_scores(C)
        R["arms"][a] = {"n_clips": len(C), "n_prompts_both_seeds": len(P), **{x: float(np.mean([v[x] for v in P.values() if x in v])) for x in METRICS}}
        sd = {}
        for x in METRICS:
            d = [C[(p, 1)][x] - C[(p, 2)][x] for (p, s) in C if s == 1 and (p, 2) in C and x in C[(p, 1)] and x in C[(p, 2)]]
            sd[x] = {"n_pairs": len(d), "per_clip_seed_sd": float(np.std(d, ddof=1) / np.sqrt(2))} if len(d) > 2 else None
        R["seed_noise"][a] = sd
    if "base" in arms:
        B = prompt_scores(arms["base"])
        for a in arms:
            if a == "base": continue
            A = prompt_scores(arms[a])
            R["paired_vs_base"][a] = {x: paired(A, B, x, rng, MARGIN_ABS.get(x, MARGIN_REL[x] * R["arms"]["base"][x] if x in MARGIN_REL else None)) for x in METRICS}
    s = json.dumps(R, indent=1, default=float); print(s)
    if out: open(out, "w").write(s)
if __name__ == "__main__": main()
