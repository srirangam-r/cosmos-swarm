#!/usr/bin/env python3
"""Summarise a corruption-validation run: per corruption, the mean paired drop
(orig - corrupted) in judge score per category, with SE over clips, plus the
judge noise (|offset 0 - offset 0.5| on the same clip)."""
import json, sys, os, collections
import numpy as np

d = json.load(open(sys.argv[1]))["results"]
by = {}
for r in d:
    base = os.path.basename(r["clip"])[:-4]
    clip, kind = base.split("__")
    by.setdefault((clip, kind), {})[r["offset"]] = r["summary"]
keys = ["overall", "Physical Laws", "Visual Integrity", "Geometric Reasoning", "Semantic Alignment"]
out = {}
# judge noise
noise = {k: [] for k in keys}
for (c, kind), offs in by.items():
    if 0.0 in offs and 0.5 in offs:
        for k in keys:
            noise[k].append(offs[0.0][k] - offs[0.5][k])
out["judge_noise_sd_offset"] = {k: float(np.std(v) / np.sqrt(2)) if v else None for k, v in noise.items()}
mean = lambda offs, k: float(np.mean([s[k] for s in offs.values()]))
clips = sorted({c for c, _ in by})
kinds = sorted({k for _, k in by} - {"orig"})
out["orig_mean"] = {k: float(np.mean([mean(by[(c, "orig")], k) for c in clips if (c, "orig") in by])) for k in keys}
out["drops"] = {}
for kind in kinds:
    row = {}
    for k in keys:
        dl = [mean(by[(c, "orig")], k) - mean(by[(c, kind)], k) for c in clips if (c, "orig") in by and (c, kind) in by]
        if dl:
            row[k] = {"mean": float(np.mean(dl)), "se": float(np.std(dl, ddof=1) / np.sqrt(len(dl))) if len(dl) > 1 else None,
                      "n": len(dl), "frac_orig_higher": float(np.mean(np.array(dl) > 0))}
    out["drops"][kind] = row
print(json.dumps(out, indent=1))
