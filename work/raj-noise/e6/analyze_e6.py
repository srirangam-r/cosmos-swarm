"""E6 analysis, fixed before the clips exist. Period: tools/pend_acf (ro-3; within 1% of mocap on 20/20 real recordings),
unchanged, skip 8 frames, on every generated clip and on each real continuation. All periods in FRAMES (generation at
24 fps; the real continuations are 25 fps distinct frames), so 'ratio' compares frame periods; seconds are also given.
Trajectory-copy index: correlation of a clip's motion-energy course with the DONOR's real clip minus with the TARGET's.
"""
import glob, json, re, subprocess, sys
from pathlib import Path
import numpy as np, cv2

ROOT = Path(__file__).parent; OUT = ROOT / "out"
REAL = Path.home() / "swarm/internals/cosmos-swarm/work/codex-api-4/t8/output/clips"
ACF = Path.home() / "swarm/internals/cosmos-swarm/tools/pend_acf/pend_acf.py"
PY = sys.executable


def period(mp4):
    r = subprocess.run([PY, "-I", str(ACF), str(mp4), "--fps", "24", "--skip", "8"], capture_output=True, text=True)
    try:
        j = json.loads(r.stdout.strip().splitlines()[-1])
        return j.get("period_frames"), j.get("flag")
    except Exception:
        return None, "error"


def course(mp4):
    cap = cv2.VideoCapture(str(mp4)); G = []
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        G.append(cv2.resize(g, (g.shape[1] // 8, g.shape[0] // 8), interpolation=cv2.INTER_AREA))
    G = np.array(G); return np.abs(np.diff(G, axis=0)).mean(axis=(1, 2))


def corr(a, b):
    n = min(len(a), len(b)); a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-12))


def med(v):
    v = [x for x in v if x is not None]; return round(float(np.median(v)), 3) if v else None


real = {}
for p in sorted(REAL.glob("real_*.mp4")):
    i = int(p.stem.split("_")[1]); P, flag = period(p); real[i] = dict(P=P, flag=flag, course=course(p))
rows = []
for mp4 in sorted(OUT.glob("*.mp4")):
    n = mp4.stem; P, flag = period(mp4); c = course(mp4)
    m = re.match(r"A_rec(\d+)$", n) or re.match(r"B_rec(\d+)_s(\d+)$", n) or re.match(r"C_t(\d+)_d(\d+)_(\w+?)_s(\d+)$", n)
    if not m: continue
    if n.startswith("A_"):
        t = int(m.group(1)); arm, d = "recon", t
    elif n.startswith("B_"):
        t = int(m.group(1)); arm, d = "base", None
    else:
        t, d, arm = int(m.group(1)), int(m.group(2)), m.group(3)
    r = dict(name=n, target=t, donor=d, arm=arm, P=P, flag=flag)
    if real.get(t, {}).get("P") and P:
        r["ratio"] = P / real[t]["P"]
    r["copy_index"] = (corr(c, real[d]["course"]) - corr(c, real[t]["course"])) if d and d != t and d in real else None
    r["corr_target_real"] = corr(c, real[t]["course"]) if t in real else None
    rows.append(r)
res = {"real_periods_frames": {i: v["P"] for i, v in real.items()}, "n_clips": len(rows)}
for arm in ("recon", "base", "tlo", "slo", "all"):
    R = [r for r in rows if r["arm"] == arm]
    ok = [r for r in R if r.get("ratio")]
    res[arm] = dict(n=len(R), n_period_read=len(ok), median_ratio=med([r["ratio"] for r in ok]),
                    within_10pct=sum(1 for r in ok if abs(r["ratio"] - 1) <= 0.10),
                    median_copy_index=med([r["copy_index"] for r in R]),
                    median_corr_with_target_real=med([r["corr_target_real"] for r in R]))
json.dump(dict(res, rows=rows), open(ROOT / "report.json", "w"), indent=1, default=float)
md = ["# E6 report (task 250)", "", "| arm | clips | period read | median P/P_real | within 10% | copy index | corr w/ target real |",
      "|---|---|---|---|---|---|---|"]
for arm in ("recon", "base", "tlo", "slo", "all"):
    a = res[arm]
    md.append(f"| {arm} | {a['n']} | {a['n_period_read']} | {a['median_ratio']} | {a['within_10pct']} | {a['median_copy_index']} | {a['median_corr_with_target_real']} |")
md += ["", "recon = inverted real clip regenerated; base = plain Nano from the same frame; tlo/slo = donor's coarse band + fresh fill;",
       "all = donor's full noise (copy control). copy index > 0: the clip moves like the DONOR recording rather than the target's real continuation."]
(ROOT / "report.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
