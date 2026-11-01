"""E7 analysis, frozen with run_e7.py before any clip exists. pend_acf (fps 24, skip 8) on every clip.
v2 (before any v2 clip): E6's tlo 'clean' reads were a flicker artifact, so a clip now counts as CLEAN only if
(a) pend_acf flag 'ok', (b) flicker = std over frames of the mean grey level / its mean < 0.08 (real GAUGE clips are far below),
and (c) tools/trk_ballfall/measure_pend.py (referee PASS) gives a period within 10% of pend_acf's.
Per arm: clean = such clips /16; within10 = ok clips with |P/P_real-1|<=0.10; median P/P_real over ok clips.
Reference rates on the same 8 targets x seeds 1,2 from E6: plain Nano (B) 1/16 ok, E6 tlo transplant 16/16 ok.
PRE-REGISTERED READINGS: an arm with clean >= 12/16 'reproduces the E6 effect'; <= 4/16 'does not'; otherwise partial.
  damp_a*: energy hypothesis (if any a reproduces it and up_fresh does not, a one-line noise fix exists).
  tlo_phrand: reproduces -> the donor's band magnitude suffices; not -> its phase matters.
  tlo_shuf: reproduces -> spatial alignment with the scene doesn't matter; not -> it does.
Clock: f = ln(P_W/P_C)/ln(0.7) per (target, seed) pair over ok periods, median over targets with a target-cluster bootstrap
95% CI (2000 resamples, rng 0), for osc (bins 3-6) and low (bins 0-6). CI low > 0.5 -> 'band carries the donor's clock';
CI high < 0.25 -> 'does not'; else partial. Writes report_e7.json / report_e7.md."""
import json, os, re, subprocess, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).parent; OUT = ROOT / "out"
E6 = Path(os.environ.get("E6_DIR", str(Path.home() / "e6"))); ACF = Path(os.environ.get("E6_ACF", str(E6 / "pend_acf.py")))
import cv2
MP = Path(os.environ.get("E7_MP", str(Path.home() / "swarm/internals/cosmos-swarm/tools/trk_ballfall/measure_pend.py")))
def flicker(p):
    cap = cv2.VideoCapture(str(p)); g = []
    while True:
        ok, f = cap.read()
        if not ok: break
        g.append(float(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).mean()))
    g = np.array(g); return float(g.std() / (g.mean() + 1e-9))
def mp_period(p):
    r = subprocess.run([sys.executable, "-I", str(MP), str(p), "--fps", "24"], capture_output=True, text=True)
    s = r.stdout; i = s.find("{")
    try: j = json.loads(s[i:]); return j["period_s"] * 24 if j.get("period_s") else None
    except Exception: return None
def period(p):
    r = subprocess.run([sys.executable, "-I", str(ACF), str(p), "--fps", "24", "--skip", "8"], capture_output=True, text=True)
    try: j = json.loads(r.stdout.strip().splitlines()[-1]); return j.get("period_frames"), j.get("flag")
    except Exception: return None, "error"
real = {t: period(E6 / "real" / f"real_{t:02}.mp4")[0] for t in range(1, 9)}
rows = []
for p in sorted(OUT.glob("*.mp4")):
    m = re.match(r"(.+)_t(\d+)_s(\d+)$", p.stem); arm, t, s = m.group(1), int(m.group(2)), int(m.group(3))
    P, fl = period(p); fk = flicker(p); Pm = mp_period(p)
    clean = fl == "ok" and fk < 0.08 and Pm is not None and abs(Pm / P - 1) <= 0.10
    rows.append(dict(arm=arm, t=t, s=s, P=P, flag_acf=fl, flicker=round(fk, 4), P_mp=Pm, flag=("ok" if clean else "not_clean"),
                     ratio=(P / real[t] if clean else None)))
res = {"real": real, "arms": {}}
for arm in sorted({r["arm"] for r in rows}):
    R = [r for r in rows if r["arm"] == arm]; ok = [r for r in R if r["flag"] == "ok"]
    res["arms"][arm] = dict(n=len(R), clean=len(ok), acf_ok=sum(1 for r in R if r["flag_acf"] == "ok"),
                           median_flicker=round(float(np.median([r["flicker"] for r in R])), 4), within10=sum(1 for r in ok if abs(r["ratio"] - 1) <= .1),
                           median_ratio=(round(float(np.median([r["ratio"] for r in ok])), 3) if ok else None),
                           reading=("reproduces" if len(ok) >= 12 else "does not" if len(ok) <= 4 else "partial"))
def fclock(a, b):
    P = {(r["arm"], r["t"], r["s"]): r for r in rows}; per = {}
    for t in range(1, 9):
        v = [np.log(P[(b, t, s)]["P"] / P[(a, t, s)]["P"]) / np.log(0.7) for s in (1, 2)
             if (a, t, s) in P and (b, t, s) in P and P[(a, t, s)]["flag"] == "ok" and P[(b, t, s)]["flag"] == "ok"]
        if v: per[t] = float(np.mean(v))
    if not per: return None
    x = np.array(list(per.values())); rng = np.random.default_rng(0)
    bs = [np.median(rng.choice(x, len(x))) for _ in range(2000)]; lo, hi = np.percentile(bs, [2.5, 97.5])
    return dict(targets=len(x), median_f=round(float(np.median(x)), 3), ci=[round(float(lo), 3), round(float(hi), 3)],
                decision=("band carries the donor's clock" if lo > .5 else "does not carry it" if hi < .25 else "partial"))
res["clock"] = {"osc(3-6)": fclock("osc_C", "osc_W"), "low(0-6)": fclock("low_C", "low_W")}
json.dump(dict(res, rows=rows), open(ROOT / "report_e7.json", "w"), indent=1, default=float)
md = ["# E7 report", "", "clean = pend_acf ok AND flicker < 0.08 AND measure_pend within 10% of pend_acf (v2). E6's tlo clips were a flicker artifact.", "",
      "| arm | clean | acf ok | median flicker | within 10% | median P/P_real | reading |", "|---|---|---|---|---|---|---|"]
for arm, a in res["arms"].items(): md.append(f"| {arm} | {a['clean']}/{a['n']} | {a['acf_ok']} | {a['median_flicker']} | {a['within10']} | {a['median_ratio']} | {a['reading']} |")
md += ["", "| clock band | targets | median f | 95% CI | decision |", "|---|---|---|---|---|"]
for k, c in res["clock"].items():
    md.append(f"| {k} | " + (f"{c['targets']} | {c['median_f']} | {c['ci']} | {c['decision']} |" if c else "- | - | - | no pairs |"))
(ROOT / "report_e7.md").write_text("\n".join(md) + "\n"); print("\n".join(md))
