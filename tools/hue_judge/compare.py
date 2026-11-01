#!/usr/bin/env python3
"""Paired before/after comparison of two hue_judge result files.

Clips are matched by file stem (e.g. physics_017_s1.mp4 in both runs), so generate
before and after clips with the same names, prompts, seeds and settings.
Scores are averaged over frame offsets first. Reports per category:
  before mean, after mean, paired diff (after - before) +- SE over clips, n.
Optional --seednoise: a result file of the BEFORE model at two seeds, named
<stem>_s1 / <stem>_s2; reports the SD of a single-clip score across seeds and the
SE of a mean over n clips, so you can tell whether the diff exceeds seed noise.

usage: python3 compare.py before.json after.json [--seednoise base.json]
"""
import argparse, json, os, re
import numpy as np

KEYS = ["overall", "Physical Laws", "Visual Integrity", "Geometric Reasoning", "Semantic Alignment"]


def load(path):
    by = {}
    for r in json.load(open(path))["results"]:
        stem = os.path.basename(r["clip"])[:-4]
        by.setdefault(stem, []).append(r["summary"])
    return {s: {k: float(np.mean([x[k] for x in v if x.get(k) is not None]))
                for k in KEYS if any(x.get(k) is not None for x in v)} for s, v in by.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("before"); ap.add_argument("after"); ap.add_argument("--seednoise")
    a = ap.parse_args()
    b, f = load(a.before), load(a.after)
    common = sorted(set(b) & set(f))
    out = {"n_clips": len(common), "missing_after": sorted(set(b) - set(f)), "categories": {}}
    for k in KEYS:
        d = [f[s][k] - b[s][k] for s in common if k in b[s] and k in f[s]]
        if not d:
            continue
        out["categories"][k] = {"before": float(np.mean([b[s][k] for s in common if k in b[s]])),
                                "after": float(np.mean([f[s][k] for s in common if k in f[s]])),
                                "diff": float(np.mean(d)),
                                "se": float(np.std(d, ddof=1) / np.sqrt(len(d))) if len(d) > 1 else None,
                                "n": len(d)}
    if a.seednoise:
        s = load(a.seednoise)
        pairs = {}
        for stem in s:
            m = re.match(r"(.*)_s(\d+)$", stem)
            if m:
                pairs.setdefault(m.group(1), {})[m.group(2)] = s[stem]
        pairs = {p: v for p, v in pairs.items() if len(v) >= 2}
        sn = {}
        for k in KEYS:
            dd = [v["1"][k] - v["2"][k] for v in pairs.values() if "1" in v and "2" in v and k in v["1"] and k in v["2"]]
            if len(dd) > 1:
                sd1 = float(np.sqrt(np.mean(np.square(dd)) / 2))  # per-clip seed SD
                sn[k] = {"per_clip_seed_sd": sd1, "n_pairs": len(dd),
                         "se_of_paired_diff_over_n_clips": float(sd1 * np.sqrt(2) / np.sqrt(max(len(common), 1)))}
        out["seed_noise"] = sn
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
