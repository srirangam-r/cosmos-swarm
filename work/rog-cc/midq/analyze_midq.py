#!/usr/bin/env python3
"""Predeclared analysis for PREREG.md (midq). Written before any clip was judged.
usage: analyze_midq.py judge.json [--out summary.json]
Clip names: {ball|cause5}_{F|QT|QS}_{ball1|ball2}_fps24_93f_s{N}.mp4, real_*.mp4,
controls trunc36_<stem>.mp4 and static_<stem>.mp4."""
import argparse, json, os, re
import numpy as np
from scipy import stats

POL = {i: 1 for i in range(1, 23)}
POL.update({17: -1, 19: -1, 20: -1})          # negated twins: score = 1 - P(Yes)
GAUGE = list(range(1, 14))
GAUGE_PHYS = [2, 3, 4, 5, 6, 13]
REL = [1, 2, 5]                                  # release-scene questions (#2577)
MF_PHYS = [3, 4, 13, 15, 16, 17, 18, 19, 20, 21]
MF_ALL = MF_PHYS + [7, 8, 9, 10, 11, 12, 14, 22]
SETS = {"gauge_overall": GAUGE, "gauge_physical": GAUGE_PHYS, "gauge_Q125": REL,
        "mf_overall": MF_ALL, "mf_physical": MF_PHYS}
MARGIN = {"gauge_overall": 0.03, "gauge_physical": 0.04, "mf_overall": 0.03, "mf_physical": 0.04}


def load(path):
    acc = {}
    for r in json.load(open(path))["results"]:
        stem = os.path.basename(r["clip"])[:-4]
        for row in r["rows"]:
            acc.setdefault(stem, {}).setdefault(row["id"], []).append(row["p_yes"])
    return {s: {q: float(np.mean(v)) for q, v in d.items()} for s, d in acc.items()}


def score(pq, qs):
    return float(np.mean([pq[q] if POL[q] > 0 else 1 - pq[q] for q in qs]))


def parse(stem):
    pre = ""
    for p in ("trunc36_", "static_"):
        if stem.startswith(p):
            pre, stem = p[:-1], stem[len(p):]
    m = re.match(r"(?:ball|cause5)_(F|QT|QS)_(ball\d)_fps24_93f_s(\d+)$", stem)
    if m:
        return pre, m.group(1), (m.group(2), int(m.group(3)))
    return pre, ("real" if stem.startswith("real") else None), None


def paired(clips, set_, ctl, a="QT", b="F"):
    A = {k: v for (c, arm, k), v in clips.items() if c == ctl and arm == a}
    B = {k: v for (c, arm, k), v in clips.items() if c == ctl and arm == b}
    keys = sorted(set(A) & set(B))
    if not keys:
        return None
    d = np.array([score(A[k], SETS[set_]) - score(B[k], SETS[set_]) for k in keys])
    n = len(d); m = float(d.mean())
    se = float(d.std(ddof=1) / np.sqrt(n)) if n > 1 else float("nan")
    t = stats.t.ppf(0.95, n - 1) if n > 1 else float("nan")
    out = {"n": n, "mean": m, "se": se, "ci90": [m - t * se, m + t * se], "n_up": int((d > 0).sum()),
           f"mean_{a}": float(np.mean([score(A[k], SETS[set_]) for k in keys])),
           f"mean_{b}": float(np.mean([score(B[k], SETS[set_]) for k in keys]))}
    if set_ in MARGIN:
        out["margin"] = MARGIN[set_]
        out["verdict"] = ("NI" if out["ci90"][0] > -MARGIN[set_] else "NI not shown") + \
                         (", sig drop" if out["ci90"][1] < 0 else (", sig gain" if out["ci90"][0] > 0 else ""))
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("judge"); ap.add_argument("--out")
    a = ap.parse_args()
    pq = load(a.judge)
    clips, reals, statics = {}, {}, {}
    for stem, v in pq.items():
        ctl, arm, key = parse(stem)
        if ctl == "static":
            statics[stem] = v
        elif arm == "real":
            reals[(ctl, stem)] = v
        elif arm:
            clips[(ctl, arm, key)] = v
    res = {"n_clips_judged": len(pq), "contrasts": {}, "arm_means": {}, "real": {}, "static": {}, "validity": {}}
    for ctl in ("", "trunc36"):
        for s in SETS:
            for b in ("F",):
                for x in ("QT", "QS"):
                    r = paired(clips, s, ctl, x, b)
                    if r:
                        res["contrasts"][f"{ctl or 'full'}:{x}-{b}:{s}"] = r
        for arm in ("F", "QT", "QS"):
            vs = [v for (c, ar, k), v in clips.items() if c == ctl and ar == arm]
            if vs:
                res["arm_means"][f"{ctl or 'full'}:{arm}"] = {s: float(np.mean([score(v, q) for v in vs]))
                                                             for s, q in SETS.items()} | {"n": len(vs)}
    for (ctl, stem), v in reals.items():
        res["real"][f"{ctl or 'full'}:{stem}"] = {s: score(v, q) for s, q in SETS.items()}
    for stem, v in statics.items():
        res["static"][stem] = {s: score(v, q) for s, q in SETS.items()}
    # V1: real (full) minus mean static on mf_physical must be >= 0.10
    rf = [v for (c, s), v in reals.items() if c == ""]
    if rf and statics:
        for s in ("mf_physical", "gauge_physical"):
            gap = float(np.mean([score(v, SETS[s]) for v in rf]) - np.mean([score(v, SETS[s]) for v in statics.values()]))
            res["validity"][f"V1_real_minus_static_{s}"] = gap
        res["validity"]["V1_pass"] = res["validity"]["V1_real_minus_static_mf_physical"] >= 0.10
    # V2: twin sums P(Yes)+P(Yes twin): ~1 reads, ~2 yes-bias
    allv = list(pq.values())
    res["validity"]["V2_twin_sum_bounce_lower(16+17)"] = float(np.mean([v[16] + v[17] for v in allv]))
    res["validity"]["V2_twin_sum_rest(18+19)"] = float(np.mean([v[18] + v[19] for v in allv]))
    # per-question means by arm (full), raw P(Yes)
    res["perq_raw_full"] = {arm: {q: float(np.mean([v[q] for (c, ar, k), v in clips.items() if c == "" and ar == arm]))
                                  for q in range(1, 23)} for arm in ("F", "QT", "QS")
                            if any(c == "" and ar == arm for (c, ar, k) in clips)}
    res["perq_raw_real"] = {stem: {q: v[q] for q in range(1, 23)} for (c, stem), v in reals.items()}
    # J-S test: QT-F on Q1/2/5, full vs trunc36
    f, t = res["contrasts"].get("full:QT-F:gauge_Q125"), res["contrasts"].get("trunc36:QT-F:gauge_Q125")
    if f and t:
        res["JS_test"] = {"full": f["mean"], "full_se": f["se"], "trunc36": t["mean"], "trunc36_se": t["se"]}
    js = json.dumps(res, indent=1)
    if a.out:
        open(a.out, "w").write(js)
    for k, v in res["contrasts"].items():
        print(f"{k:38s} {v['mean']:+.3f} ± {v['se']:.3f}  CI90 [{v['ci90'][0]:+.3f},{v['ci90'][1]:+.3f}] n={v['n']} up={v['n_up']} {v.get('verdict','')}")
    print("validity", json.dumps(res["validity"]))
    print("real", json.dumps(res["real"]))


if __name__ == "__main__":
    main()
