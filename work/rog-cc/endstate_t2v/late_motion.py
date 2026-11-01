#!/usr/bin/env python3
"""Task 133 EXPLORATORY addendum (PREREG_ADDENDUM.md; written before any late-motion number was computed).
Does Rule R cut late motion on unseen HUE T2V prompts, beyond the neutral suffix N?
Per clip: lateM = mean over frame pairs (60..92) of mean |d grey| (whole frame, 832x480, 0-255);
          earlyM = same over pairs (1..32); ratio = lateM / earlyM (scene-normalised).
Unit = prompt (mean of seeds 1-3, prompt kept only if all 3 seeds exist in both arms). Paired d = arm - ref,
mean, SE, t 90% CI, n_neg. Contrasts R-base, N-base, R-N; all, physics_*, robot_*.
Usage: late_motion.py <clips_dir> --out late_motion.json"""
import sys, os, re, glob, json
import numpy as np, cv2
from scipy import stats

pat = re.compile(r"es_(base|R|N)_((?:physics|robot)_\d+)_s(\d+)\.mp4$")


def motion(path):
    cap = cv2.VideoCapture(path); prev = None; d = []
    while True:
        ok, x = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(x, cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            d.append(float(np.abs(g - prev).mean()))
        prev = g
    d = np.array(d)  # d[i] = |f(i+1) - f(i)|
    if len(d) < 92:
        return None
    late, early = d[59:92].mean(), d[0:32].mean()
    return {"lateM": float(late), "earlyM": float(early), "ratio": float(late / max(early, 1e-6)), "n_pairs": int(len(d))}


def paired(P, a, b, key, subset=None):
    ps = sorted(p for p in P[a] if p in P[b] and (subset is None or p.startswith(subset)))
    d = np.array([P[a][p][key] - P[b][p][key] for p in ps]); n = len(d)
    if n < 3:
        return None
    se = d.std(ddof=1) / np.sqrt(n); t = stats.t.ppf(0.95, n - 1)
    return {"n_prompts": n, "mean": float(d.mean()), "se": float(se), "ci90": [float(d.mean() - t * se), float(d.mean() + t * se)],
            "n_neg": int((d < 0).sum()), "ref_mean": float(np.mean([P[b][p][key] for p in ps])),
            "per_prompt": dict(zip(ps, d.round(4).tolist()))}


def main():
    cd = sys.argv[1]; out = sys.argv[sys.argv.index("--out") + 1]
    C = {}
    for f in sorted(glob.glob(os.path.join(cd, "es_*.mp4"))):
        m = pat.search(f)
        if m:
            r = motion(f)
            if r:
                C[(m.group(1), m.group(2), int(m.group(3)))] = r
    P = {a: {} for a in ("base", "R", "N")}
    for a in P:
        for p in {k[1] for k in C if k[0] == a}:
            L = [C[(a, p, s)] for s in (1, 2, 3) if (a, p, s) in C]
            if len(L) == 3:
                P[a][p] = {k: float(np.mean([x[k] for x in L])) for k in ("lateM", "earlyM", "ratio")}
    res = {"n_clips": len(C), "n_prompts": {a: len(P[a]) for a in P}, "contrasts": {}}
    for a, b in (("R", "base"), ("N", "base"), ("R", "N")):
        for key in ("lateM", "ratio", "earlyM"):
            for sub in (None, "physics", "robot"):
                res["contrasts"][f"{a}-{b}:{key}:{sub or 'all'}"] = paired(P, a, b, key, sub)
    res["clips"] = {"|".join(map(str, k)): v for k, v in C.items()}
    json.dump(res, open(out, "w"), indent=1)
    for k, v in res["contrasts"].items():
        if v:
            print(f"{k:28s} n={v['n_prompts']:2d} d={v['mean']:+.3f}±{v['se']:.3f} CI90[{v['ci90'][0]:+.3f},{v['ci90'][1]:+.3f}] "
                  f"neg={v['n_neg']}/{v['n_prompts']} ref={v['ref_mean']:.3f}")


if __name__ == "__main__":
    main()
