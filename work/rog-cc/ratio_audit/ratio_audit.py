#!/usr/bin/env python3
"""Audit of the "QT is 76.2x closer to real than F" claim (agy-4 #2802, now in D1/D2/D3/README).

That claim is |mean(QT) - real| / |mean(F) - real| on the 13 gauge HUE questions, with the real
reference = ONE clip (real_ball1_dd32_93f) and 8 F/QT pairs (5 ball1 + 3 ball2).
This script asks how stable that ratio is:
  (a) pair bootstrap (resample the 8 matched pairs) -> CI of each distance and of the ratio;
  (b) real reference scored at offset 0 only vs offset 0.5 only (the judge's own within-clip spread);
  (c) ball1-only pairs (the only input that has a real clip);
  (d) mean of per-pair distances  mean_k |gen_k - real|  (scout-1 #2679's per-clip form);
  (e) the same numbers on my independent judge re-run of the same 20 clips (task 113, midq/judge.json).
usage: ratio_audit.py RO1_RES_JSON MIDQ_JUDGE_JSON [--out out.json]
"""
import argparse, json, os, re, sys
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "midq"))
from analyze_midq import load as mq_load, score as mq_score, parse as mq_parse, SETS  # noqa: E402

CATS = {"overall": "overall", "physical": "Physical Laws"}
rng = np.random.default_rng(0)
B = 20000


def ro1_table(path):
    """-> {(arm, ball, seed): {cat: score averaged over offsets}}, real -> {cat: {offset: score}}"""
    rows = json.load(open(path))["results"]
    clip, real = {}, {}
    for r in rows:
        stem = os.path.basename(r["clip"])
        if stem.startswith("real_"):
            for c, k in CATS.items():
                real.setdefault(c, {})[r["offset"]] = r["summary"][k]
            continue
        m = re.search(r"_(F|QT|QS)_(ball\d)_fps24_93f_s(\d)", stem)
        key = (m.group(1), m.group(2), int(m.group(3)))
        for c, k in CATS.items():
            clip.setdefault(key, {}).setdefault(c, []).append(r["summary"][k])
    clip = {k: {c: float(np.mean(v)) for c, v in d.items()} for k, d in clip.items()}
    return clip, real


def mine_table(path):
    pq = mq_load(path)
    clip, real = {}, {}
    sets = {"overall": SETS["gauge_overall"], "physical": SETS["gauge_physical"]}
    for stem, v in pq.items():
        ctl, arm, key = mq_parse(stem)
        if ctl != "":
            continue
        if arm == "real":
            for c, qs in sets.items():
                real.setdefault(c, {})["avg"] = mq_score(v, qs)
        elif arm in ("F", "QT"):
            clip[(arm, key[0], int(key[1]))] = {c: mq_score(v, qs) for c, qs in sets.items()}
    return clip, real


def analyse(clip, realref, balls, c):
    keys = sorted({(b, s) for (a, b, s) in clip if a == "F" and ("QT", b, s) in clip and b in balls})
    F = np.array([clip[("F",) + k][c] for k in keys])
    Q = np.array([clip[("QT",) + k][c] for k in keys])
    n = len(keys)
    idx = rng.integers(0, n, size=(B, n))
    dF_b = np.abs(F[idx].mean(1) - realref)
    dQ_b = np.abs(Q[idx].mean(1) - realref)
    ratio_b = dF_b / np.maximum(dQ_b, 1e-12)
    perpair_dF, perpair_dQ = np.abs(F - realref), np.abs(Q - realref)
    d = perpair_dQ - perpair_dF
    return {"n_pairs": n, "real": realref, "mean_F": F.mean(), "mean_QT": Q.mean(),
            "absdist_of_means_F": abs(F.mean() - realref), "absdist_of_means_QT": abs(Q.mean() - realref),
            "ratio_F_over_QT": abs(F.mean() - realref) / max(abs(Q.mean() - realref), 1e-12),
            "boot90_absdist_QT": np.percentile(dQ_b, [5, 95]).tolist(),
            "boot90_absdist_F": np.percentile(dF_b, [5, 95]).tolist(),
            "boot90_ratio": np.percentile(ratio_b, [5, 95]).tolist(),
            "boot_P_ratio_gt_10": float((ratio_b > 10).mean()),
            "perpair_absdist_F": perpair_dF.mean(), "perpair_absdist_QT": perpair_dQ.mean(),
            "perpair_QT_minus_F": d.mean(), "perpair_se": d.std(ddof=1) / np.sqrt(n),
            "perpair_QT_closer": int((d < 0).sum())}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ro1_res"); ap.add_argument("midq_judge"); ap.add_argument("--out")
    a = ap.parse_args()
    out = {}
    for src, (clip, real) in {"ro1_res": ro1_table(a.ro1_res), "rogcc_rerun": mine_table(a.midq_judge)}.items():
        for c in CATS:
            refs = {"avg": float(np.mean(list(real[c].values())))}
            if src == "ro1_res":
                refs.update({f"off{k}": v for k, v in real[c].items()})
            for rname, rv in refs.items():
                for bname, balls in {"all8": ("ball1", "ball2"), "ball1": ("ball1",)}.items():
                    out[f"{src}:{c}:real_{rname}:{bname}"] = analyse(clip, rv, balls, c)
    for k, v in out.items():
        print(f"{k:38s} n={v['n_pairs']} real {v['real']:.4f} F {v['mean_F']:.4f} QT {v['mean_QT']:.4f} | "
              f"|F-r| {v['absdist_of_means_F']:.4f} |QT-r| {v['absdist_of_means_QT']:.4f} "
              f"ratio {v['ratio_F_over_QT']:6.1f}x boot90 [{v['boot90_ratio'][0]:.2f}, {v['boot90_ratio'][1]:.1f}] "
              f"P(>10x) {v['boot_P_ratio_gt_10']:.2f} | perpair |F-r| {v['perpair_absdist_F']:.4f} "
              f"|QT-r| {v['perpair_absdist_QT']:.4f} d {v['perpair_QT_minus_F']:+.4f}±{v['perpair_se']:.4f} "
              f"closer {v['perpair_QT_closer']}/{v['n_pairs']}")
    if a.out:
        json.dump(out, open(a.out, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
