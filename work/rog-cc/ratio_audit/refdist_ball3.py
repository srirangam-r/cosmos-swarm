#!/usr/bin/env python3
"""Per-pair |gen - real| for the t108 ball3 F/QT clips vs the input-matched real ball3 dd34 continuation (same as refdist2, ball3).
Usage: refdist_ball3.py t108_judge.json [--out f.json]"""
import sys, json, importlib.util, numpy as np
spec = importlib.util.spec_from_file_location("am", __file__.rsplit("/", 2)[0] + "/midq/analyze_midq.py")
am = importlib.util.module_from_spec(spec); spec.loader.exec_module(am)
pq = am.load(sys.argv[1]); out = {}
for ctl, rname in [("", "real_ball3_dd34_93f"), ("trunc36", "trunc36_real_ball3_dd34_93f")]:
    real = pq[rname]; R = {}
    for s in ["gauge_overall", "gauge_physical", "gauge_Q125"]:
        r = am.score(real, am.SETS[s]); rows = []
        for k in (1, 2, 3):
            f = pq[f"{ctl + '_' if ctl else ''}cause_F_ball3_fps24_93f_s{k}"]; q = pq[f"{ctl + '_' if ctl else ''}cause_QT_ball3_fps24_93f_s{k}"]
            fs, qs = am.score(f, am.SETS[s]), am.score(q, am.SETS[s]); rows.append((fs - r, qs - r, abs(qs - r) - abs(fs - r)))
        a = np.array(rows); d = a[:, 2]
        R[s] = {"real": r, "signed_F_minus_real": float(a[:, 0].mean()), "signed_QT_minus_real": float(a[:, 1].mean()),
                "absF": float(np.abs(a[:, 0]).mean()), "absQT": float(np.abs(a[:, 1]).mean()),
                "d_mean": float(d.mean()), "d_se": float(d.std(ddof=1) / np.sqrt(3)), "QT_closer": int((d < 0).sum()), "per_seed_d": d.round(4).tolist()}
    out[ctl or "full"] = R
s = json.dumps(out, indent=1); print(s)
if "--out" in sys.argv: open(sys.argv[sys.argv.index("--out") + 1], "w").write(s)
