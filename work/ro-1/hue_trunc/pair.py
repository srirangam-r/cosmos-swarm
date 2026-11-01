#!/usr/bin/env python3
"""ro-1: QT-F paired HUE deltas per window (early f0-35 / late f46-92), vs the full-clip deltas in hue_qt/pair.json (#2577)."""
import json, os, re
import numpy as np
D = os.path.dirname(os.path.abspath(__file__))
R = json.load(open(os.path.join(D, 'res.json')))['results']
by = {}
for r in R:
    s = os.path.basename(r['clip'])[:-4]
    v = dict(r['summary']); v.update({f"Q{x['id']}": x['p_yes'] for x in r['rows']})
    by.setdefault(s, []).append(v)
M = {s: {k: float(np.mean([x[k] for x in v])) for k in v[0]} for s, v in by.items()}
KEYS = ['overall', 'Physical Laws', 'Q1', 'Q2', 'Q5', 'Q6']
out = {}
for w in ('early', 'late'):
    arms = {}
    for s in M:
        m = re.search(rf'^{w}__.*_(F|QT)_(ball\d)_fps24_93f_s(\d)', s)
        if m: arms[(m.group(1), m.group(2), int(m.group(3)))] = s
    pairs = [(arms[('F', b, sd)], arms[(a, b, sd)]) for (a, b, sd) in arms if a == 'QT' and ('F', b, sd) in arms]
    res = {'n': len(pairs)}
    for k in KEYS:
        d = np.array([M[t][k] - M[f][k] for f, t in pairs])
        res[k] = dict(F=float(np.mean([M[f][k] for f, _ in pairs])), QT=float(np.mean([M[t][k] for _, t in pairs])),
                      real=M[f'{w}__real_ball1_dd32_93f'][k], diff=float(d.mean()), se=float(d.std(ddof=1) / np.sqrt(len(d))), n_pos=int((d > 0).sum()))
    out[w] = res
    print(f'{w} n={len(pairs)}')
    for k in KEYS:
        x = res[k]; print(f"  {k:14s} F {x['F']:.3f} QT {x['QT']:.3f} real {x['real']:.3f}  QT-F {x['diff']:+.3f} ± {x['se']:.3f} ({x['n_pos']}/{len(pairs)} up)")
json.dump(out, open(os.path.join(D, 'pair.json'), 'w'), indent=1)
