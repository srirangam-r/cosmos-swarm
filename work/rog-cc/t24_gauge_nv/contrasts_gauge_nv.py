#!/usr/bin/env python3
"""Secondary contrasts on the unblinded task-24 GAUGE-eval DOVER/DD scores (PREREG A2 controls: B and C are the any-LoRA
controls, base_ctlbox is the cross-box A/A null). Same paired (prompt, seed) t-interval as analyze_gauge_nv.py; no margins.
Also robustness: Wilcoxon signed-rank p and median paired d (dd_norm is heavy-tailed on base).
Usage: contrasts_gauge_nv.py gauge_nv.json key_armlabel.json [--out f.json]"""
import json, sys, numpy as np
from scipy import stats
M = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_binary", "dd_norm"]
S, K = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
arms = {}
for code, r in S.items():
    k = K[code.replace(".mp4", "")]
    arms.setdefault(k["arm"], {})[(k["prompt"], int(k["seed"]))] = {x: float(r[x]) for x in M}
def pair(a, b):
    us = sorted(set(arms[a]) & set(arms[b])); o = {"n_units": len(us)}
    for x in M:
        d = np.array([arms[a][u][x] - arms[b][u][x] for u in us]); n = len(d)
        se = d.std(ddof=1) / np.sqrt(n); t = stats.t.ppf(0.95, n - 1)
        w = stats.wilcoxon(d).pvalue if np.any(d != 0) and n >= 5 else None
        o[x] = dict(mean=float(d.mean()), se=float(se), ci90=[float(d.mean() - t * se), float(d.mean() + t * se)],
                    median=float(np.median(d)), n_pos=int((d > 0).sum()), wilcoxon_p=None if w is None else float(w))
    return o
C = [("loraA", "loraB"), ("loraA", "loraC"), ("loraB", "loraC"), ("loraC", "base_ctlbox"), ("base_ctlbox", "base"),
     ("loraA", "base"), ("loraB", "base"), ("loraC", "base")]
O = {"medians": {a: {x: float(np.median([v[x] for v in A.values()])) for x in M} for a, A in arms.items()},
     "contrasts": {f"{a}-{b}": pair(a, b) for a, b in C}}
s = json.dumps(O, indent=1)
if "--out" in sys.argv: open(sys.argv[sys.argv.index("--out") + 1], "w").write(s)
for a, m in O["medians"].items(): print("median", a, {x: round(v, 3) for x, v in m.items()})
for c, o in O["contrasts"].items():
    for x in ["dover_fused", "dover_aesthetic", "dd_norm"]:
        r = o[x]; print(f"{c:20s} {x:16s} n={o['n_units']:2d} d={r['mean']:+.4f}±{r['se']:.4f} CI90[{r['ci90'][0]:+.4f},{r['ci90'][1]:+.4f}] med={r['median']:+.3f} pos={r['n_pos']} wilc_p={r['wilcoxon_p']}")
