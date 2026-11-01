#!/usr/bin/env python3
"""Predeclared task-24 HUE analysis (see PREREG.md). Usage: analyze_t24.py res_dir [--out summary.json]
Unit = prompt (16). Clip score = mean over offsets {0,0.5}. Prompt score = mean over seeds {1,2}.
d_p = arm(p) - base(p) (matched prompts and seeds). Mean, SE = sd/sqrt(n), t(n-1) 90% two-sided CI
(= one-sided 95% bound), and a 10k prompt-cluster bootstrap. Margins: overall 0.03, Physical Laws 0.04."""
import json, sys, re, os, numpy as np
from scipy import stats
MARGIN = {"overall": 0.03, "Physical Laws": 0.04}
CATS = ["overall", "Physical Laws", "Visual Integrity", "Geometric Reasoning", "Semantic Alignment"]
pat = re.compile(r"((?:physics|robot)_\d+)_s(\d+)\.mp4$")
def load(path):
    clips = {}
    for r in json.load(open(path))["results"]:
        m = pat.search(r["clip"]); key = (m.group(1), int(m.group(2)))
        clips.setdefault(key, []).append(r["summary"])
    return {k: {c: float(np.mean([s[c] for s in v if c in s])) for c in CATS if any(c in s for s in v)} for k, v in clips.items()}
def prompt_scores(C, seeds=(1, 2)):
    P = {}
    for (p, s), v in C.items():
        if s in seeds: P.setdefault(p, []).append(v)
    return {p: {c: float(np.mean([x[c] for x in v if c in x])) for c in CATS if any(c in x for x in v)} for p, v in P.items() if len(v) == len(seeds)}
def paired(A, B, cat, rng):
    ps = sorted(p for p in A if p in B and cat in A[p] and cat in B[p])
    d = np.array([A[p][cat] - B[p][cat] for p in ps]); n = len(d)
    if n < 3: return None
    se = d.std(ddof=1) / np.sqrt(n); t90 = stats.t.ppf(0.95, n - 1); t95 = stats.t.ppf(0.975, n - 1)
    bs = np.array([rng.choice(d, n).mean() for _ in range(10000)])
    out = {"n_prompts": n, "mean": d.mean(), "se": se, "ci90": [d.mean() - t90 * se, d.mean() + t90 * se],
           "ci95": [d.mean() - t95 * se, d.mean() + t95 * se], "boot_ci90": list(np.percentile(bs, [5, 95])),
           "n_pos": int((d > 0).sum()), "per_prompt": dict(zip(ps, d.round(4).tolist()))}
    if cat in MARGIN:
        m = MARGIN[cat]; lb, ub = out["ci90"]
        out["margin"] = m
        out["verdict"] = ("non-inferior" if lb > -m else "regression" if ub < -m else "drop (significant, within margin unclear)" if ub < 0 else "inconclusive")
    return {k: (float(v) if isinstance(v, (np.floating, float)) else v) for k, v in out.items()}
def seed_sd(C, cat):
    d = [C[(p, 1)][cat] - C[(p, 2)][cat] for (p, s) in C if s == 1 and (p, 2) in C and cat in C[(p, 1)] and cat in C[(p, 2)]]
    return {"n_pairs": len(d), "per_clip_seed_sd": float(np.std(d, ddof=1) / np.sqrt(2))} if len(d) > 2 else None
def main():
    rd = sys.argv[1]; out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else None
    rng = np.random.default_rng(0)
    arms = {x[:-5]: load(os.path.join(rd, x)) for x in sorted(os.listdir(rd)) if x.endswith(".json")}
    R = {"arms": {}, "seed_noise": {}, "paired_vs_base": {}}
    for a, C in arms.items():
        P = prompt_scores(C)
        R["arms"][a] = {"n_clips": len(C), "n_prompts_both_seeds": len(P), **{c: float(np.mean([v[c] for v in P.values() if c in v])) for c in CATS}}
        R["seed_noise"][a] = {c: seed_sd(C, c) for c in CATS}
    if "base" in arms:
        B = prompt_scores(arms["base"])
        for a in arms:
            if a == "base": continue
            A = prompt_scores(arms[a])
            R["paired_vs_base"][a] = {c: paired(A, B, c, rng) for c in CATS}
    # --ref ARM (added shift 12, before any loraA/B result exists): same paired test vs a control arm, e.g. A - loraC
    # (PREREG: "if A's Physical gain is matched by B/C, it is not physics"). Reported as a CI; margin verdicts apply only vs base.
    if "--ref" in sys.argv:
        ref = sys.argv[sys.argv.index("--ref") + 1]
        if ref in arms:
            Rf = prompt_scores(arms[ref]); R[f"paired_vs_{ref}"] = {}
            for a in arms:
                if a in (ref, "base"): continue
                R[f"paired_vs_{ref}"][a] = {c: paired(prompt_scores(arms[a]), Rf, c, rng) for c in CATS}
    s = json.dumps(R, indent=1, default=float); print(s)
    if out: open(out, "w").write(s)
if __name__ == "__main__": main()
