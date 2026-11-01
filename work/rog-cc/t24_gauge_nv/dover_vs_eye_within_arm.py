#!/usr/bin/env python3
"""#2249 confound check: re-run DOVER/DD vs ro-1 eye codes WITHIN arm (key now released, #2999).
Arm-demeaned metric (subtract each arm's mean), then artifact vs clean; also the per-arm artifact rate.
Usage: dover_vs_eye_within_arm.py dover_vs_eye.json key_armlabel.json [--out f.json]"""
import json, sys, numpy as np
D, K = json.load(open(sys.argv[1])), json.load(open(sys.argv[2]))
rows = D["rows"]
for r in rows: r["arm"] = K[r["code"]]["arm"]
arms = sorted({r["arm"] for r in rows}); O = {"artifact_rate": {}, "within_arm": {}}
isart = lambda r: str(r["artifact"]).strip().lower() not in ("", "none", "no", "0", "clean")
for a in arms:
    R = [r for r in rows if r["arm"] == a]; O["artifact_rate"][a] = [sum(isart(r) for r in R), len(R)]
rng = np.random.default_rng(0)
for m in ["fused", "aes", "tech", "dd_norm"]:
    mu = {a: np.mean([r[m] for r in rows if r["arm"] == a]) for a in arms}
    x = np.array([r[m] - mu[r["arm"]] for r in rows]); y = np.array([isart(r) for r in rows])
    a, c = x[y], x[~y]; d = a.mean() - c.mean()
    bs = [rng.choice(a, len(a)).mean() - rng.choice(c, len(c)).mean() for _ in range(4000)]
    auc = float((a[:, None] > c[None, :]).mean() + 0.5 * (a[:, None] == c[None, :]).mean())
    O["within_arm"][m] = dict(n_art=int(y.sum()), n_clean=int((~y).sum()), d_art_minus_clean=float(d),
                              ci95=[float(v) for v in np.percentile(bs, [2.5, 97.5])], auc=auc)
s = json.dumps(O, indent=1); print(s)
if "--out" in sys.argv: open(sys.argv[sys.argv.index("--out") + 1], "w").write(s)
