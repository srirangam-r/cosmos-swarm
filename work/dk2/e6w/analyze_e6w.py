"""E6-W analysis (dk2), frozen together with run_e6w.py BEFORE any W clip exists.
Period = tools/pend_acf unchanged (fps 24, skip 8), exactly as analyze_e6.py. Only 'ok'-flagged periods are used.
Per matched pair (same target, donor recording, fill seed, arm): r = P(W clip, warped donor) / P(C clip, E6 unwarped donor).
Frequency-carry fraction  f = ln(r) / ln(7/10): 1 = the clip takes the donor's clock (period scales with the donor),
0 = the donor's speed doesn't matter. Per target, average f over its pairs; report the median over targets with a
target-cluster bootstrap 95% CI (2000 resamples, rng seed 0).
PRE-REGISTERED DECISIONS (per arm, tlo is primary, 'all' is the positive copy control):
  CI low  > 0.5   -> "band carries the donor's clock"
  CI high < 0.25  -> "donor speed does not set the clock"
  otherwise       -> "partial / inconclusive"
Also reported: WA reconstruction (P(WA_recXX) / P(realw_XX)), and P(W)/P(target real) descriptively.
Run on the box: python -I analyze_e6w.py  -> report_e6w.json / report_e6w.md
"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent; OUT = ROOT / "out"
CS = Path.home() / "swarm/internals/cosmos-swarm"
E6OUT = CS / "work/raj-noise/e6/out"; REAL = CS / "work/codex-api-4/t8/output/clips"
ACF = CS / "tools/pend_acf/pend_acf.py"; PY = sys.executable
cache = {}


def period(mp4):
    if mp4 not in cache:
        r = subprocess.run([PY, "-I", str(ACF), str(mp4), "--fps", "24", "--skip", "8"], capture_output=True, text=True)
        try:
            j = json.loads(r.stdout.strip().splitlines()[-1]); cache[mp4] = (j.get("period_frames"), j.get("flag"))
        except Exception:
            cache[mp4] = (None, "error")
    return cache[mp4]


def okP(mp4):
    P, fl = period(mp4) if mp4.exists() else (None, "missing")
    return (P if fl == "ok" and P else None), fl


res = {"recon": [], "pairs": []}
for p in sorted(OUT.glob("WA_rec*.mp4")):
    d = p.stem[6:]; Pw, fw = okP(p); Pr, fr = okP(ROOT / "clips" / f"realw_{d}.mp4")
    res["recon"].append(dict(donor=int(d), P=Pw, flag=fw, P_realw=Pr, ratio=(Pw / Pr if Pw and Pr else None)))
for p in sorted(OUT.glob("W_t*_d*_*.mp4")):
    m = re.match(r"W_t(\d+)_d(\d+)_(\w+?)_s(\d+)$", p.stem); t, d, arm, s = m.groups()
    Pw, fw = okP(p); Pc, fc = okP(E6OUT / f"C_t{t}_d{d}_{arm}_s{s}.mp4"); Pt, _ = okP(REAL / f"real_{t}.mp4")
    r = Pw / Pc if Pw and Pc else None
    res["pairs"].append(dict(target=int(t), donor=int(d), arm=arm, seed=int(s), P_W=Pw, flag_W=fw, P_C=Pc, flag_C=fc,
                             P_target_real=Pt, ratio=r, f=(np.log(r) / np.log(0.7) if r else None),
                             W_over_real=(Pw / Pt if Pw and Pt else None), C_over_real=(Pc / Pt if Pc and Pt else None)))
rng = np.random.default_rng(0); summ = {}
for arm in ("tlo", "all"):
    R = [r for r in res["pairs"] if r["arm"] == arm]
    byt = {}
    for r in R:
        if r["f"] is not None: byt.setdefault(r["target"], []).append(r["f"])
    ft = np.array([np.mean(v) for v in byt.values()])
    a = dict(n_pairs=len(R), n_pairs_read=sum(r["f"] is not None for r in R), n_targets=len(ft))
    if len(ft) >= 3:
        boots = [np.median(rng.choice(ft, len(ft))) for _ in range(2000)]
        lo, hi = np.percentile(boots, [2.5, 97.5]); a.update(median_f=float(np.median(ft)), ci=[float(lo), float(hi)])
        a["decision"] = ("band carries the donor's clock" if lo > 0.5 else
                         "donor speed does not set the clock" if hi < 0.25 else "partial / inconclusive")
        a["median_W_over_real"] = float(np.median([r["W_over_real"] for r in R if r["W_over_real"]] or [np.nan]))
        a["median_C_over_real"] = float(np.median([r["C_over_real"] for r in R if r["C_over_real"]] or [np.nan]))
    else:
        a["decision"] = "too few readable pairs (<3 targets)"
    summ[arm] = a
res["summary"] = summ
json.dump(res, open(ROOT / "report_e6w.json", "w"), indent=1, default=float)
md = ["# E6-W (wrong-period donor control)", "", "| arm | pairs read | targets | median f | 95% CI | decision | P_W/P_real | P_C/P_real |",
      "|---|---|---|---|---|---|---|---|"]
for arm, a in summ.items():
    md.append(f"| {arm} | {a['n_pairs_read']}/{a['n_pairs']} | {a['n_targets']} | {a.get('median_f')} | {a.get('ci')} | "
              f"{a['decision']} | {a.get('median_W_over_real')} | {a.get('median_C_over_real')} |")
md += ["", "recon (WA): " + ", ".join(f"d{r['donor']}: {r['ratio'] and round(r['ratio'], 3)} ({r['flag']})" for r in res["recon"])]
(ROOT / "report_e6w.md").write_text("\n".join(md) + "\n"); print("\n".join(md))
