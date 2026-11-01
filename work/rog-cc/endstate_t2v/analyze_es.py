#!/usr/bin/env python3
"""Task 133 predeclared analysis (PREREG.md). Usage: analyze_es.py ROOT [--out summary.json]
ROOT/res/<arm>.json = hue_judge output; ROOT/res_nv/<arm>.json = nv_scoreboard score.py output. Arms base, R, N.
Clip HUE score = mean over offsets {0,0.5}. Prompt value = mean over seeds {1,2,3} (prompt kept only if all 3 seeds exist
in BOTH arms). d_p = arm(p) - ref(p) over the 16 prompts; mean, SE, t(n-1) 90% CI (= one-sided 95% bound), 10k prompt bootstrap.
Margins (vs base only): HUE overall 0.03, Physical Laws 0.04 (human-approved #1306); DOVER fused 0.02, dd_norm 15% of base
mean (PROPOSED). Subsets physics_* / robot_* reported as CIs only."""
import json, sys, re, os, numpy as np
from scipy import stats
HUE = ["overall", "Physical Laws", "Visual Integrity", "Geometric Reasoning", "Semantic Alignment"]
NV = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_binary", "dd_norm"]
MARGIN = {"overall": 0.03, "Physical Laws": 0.04, "dover_fused": 0.02}
SEEDS = (1, 2, 3)
pat = re.compile(r"((?:physics|robot)_\d+)_s(\d+)\.mp4$")
def load_hue(path):
    C = {}
    for r in json.load(open(path))["results"]:
        m = pat.search(r["clip"]); C.setdefault((m.group(1), int(m.group(2))), []).append(r["summary"])
    return {k: {c: float(np.mean([s[c] for s in v if c in s])) for c in HUE if any(c in s for s in v)} for k, v in C.items()}
def load_nv(path):
    C = {}
    for k, r in json.load(open(path)).items():
        m = pat.search(k)
        if m and isinstance(r, dict): C[(m.group(1), int(m.group(2)))] = {x: float(r[x]) for x in NV if x in r and r[x] is not None}
    return C
def pscores(C, cats):
    P = {}
    for (p, s), v in C.items():
        if s in SEEDS: P.setdefault(p, []).append(v)
    return {p: {c: float(np.mean([x[c] for x in L])) for c in cats if all(c in x for x in L)} for p, L in P.items() if len(L) == len(SEEDS)}
def paired(A, B, c, rng, subset=None, margin=None):
    ps = sorted(p for p in A if p in B and c in A[p] and c in B[p] and (subset is None or p.startswith(subset)))
    d = np.array([A[p][c] - B[p][c] for p in ps]); n = len(d)
    if n < 3: return None
    se = d.std(ddof=1) / np.sqrt(n); t90 = stats.t.ppf(0.95, n - 1)
    bs = np.array([rng.choice(d, n).mean() for _ in range(10000)])
    o = {"n_prompts": n, "mean": float(d.mean()), "se": float(se), "ci90": [float(d.mean() - t90 * se), float(d.mean() + t90 * se)],
         "boot_ci90": [float(x) for x in np.percentile(bs, [5, 95])], "n_pos": int((d > 0).sum()),
         "ref_mean": float(np.mean([B[p][c] for p in ps])), "per_prompt": dict(zip(ps, d.round(4).tolist()))}
    if margin is not None:
        lb, ub = o["ci90"]; o["margin"] = margin
        o["verdict"] = ("non-inferior" if lb > -margin else "regression" if ub < -margin else
                        "drop (significant, margin unclear)" if ub < 0 else "inconclusive")
    return o
def seed_sd(C, c):
    sds = []
    for p in {k[0] for k in C}:
        v = [C[(p, s)][c] for s in SEEDS if (p, s) in C and c in C[(p, s)]]
        if len(v) == 3: sds.append(np.std(v, ddof=1))
    return {"n_prompts": len(sds), "per_clip_seed_sd_rms": float(np.sqrt(np.mean(np.square(sds))))} if sds else None
def main():
    root = sys.argv[1]; out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    rng = np.random.default_rng(0); S = {}
    for kind, cats, loader in [("hue", HUE, load_hue), ("nv", NV, load_nv)]:
        d = os.path.join(root, "res" if kind == "hue" else "res_nv")
        arms = {a: loader(os.path.join(d, a + ".json")) for a in ["base", "R", "N"] if os.path.exists(os.path.join(d, a + ".json.done"))}
        P = {a: pscores(C, cats) for a, C in arms.items()}
        K = S[kind] = {"arms": {a: {"n_clips": len(arms[a]), "n_prompts_all_seeds": len(P[a]),
                       **{c: float(np.mean([v[c] for v in P[a].values() if c in v])) for c in cats}} for a in arms},
                       "seed_sd": {a: {c: seed_sd(arms[a], c) for c in cats} for a in arms}, "contrasts": {}}
        for a, b in [("R", "base"), ("N", "base"), ("R", "N")]:
            if a in P and b in P:
                K["contrasts"][f"{a}-{b}"] = {c: paired(P[a], P[b], c, rng, margin=(MARGIN.get(c) if b == "base" else None)
                    if c != "dd_norm" else None) for c in cats}
                if b == "base" and "dd_norm" in cats:
                    o = K["contrasts"][f"{a}-{b}"]["dd_norm"]
                    if o: m = 0.15 * o["ref_mean"]; lb, ub = o["ci90"]; o["margin"] = m; o["verdict"] = (
                        "non-inferior" if lb > -m else "regression" if ub < -m else "drop (significant, margin unclear)" if ub < 0 else "inconclusive")
                for sub in ["physics", "robot"]:
                    K["contrasts"][f"{a}-{b}:{sub}"] = {c: paired(P[a], P[b], c, rng, subset=sub) for c in cats}
    s = json.dumps(S, indent=1); print(s)
    if out: open(out, "w").write(s)
    for kind in S:
        for k, v in S[kind]["contrasts"].items():
            for c, o in v.items():
                if o: print(f"{kind} {k:16s} {c:20s} {o['mean']:+.4f} ± {o['se']:.4f} CI90 [{o['ci90'][0]:+.4f},{o['ci90'][1]:+.4f}] n={o['n_prompts']} up={o['n_pos']} {o.get('verdict','')}", file=sys.stderr)
if __name__ == "__main__": main()
