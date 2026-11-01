#!/usr/bin/env python3
"""t226 EXPLORATORY, post hoc (Amendment 6 item 3), written before any contrast was computed.
F/H frozen dy8/dyEnd with a hop gate: a clip's value counts only if its firstfall track has no jump >35 px/frame inside the
window that feeds the statistic (dy8: f0-8; dyEnd: f0-92, since a hop anywhere can carry the track to another object).
Plus the tracker-free stay-at-start similarity ncc_end (input ball patch vs f84-92, same spot; >=0.8 = ball still there).
Same contrasts as analyze_t226.py (seed-paired, exact sign-flip). usage: explore_t226.py measures.json out.json"""
import sys, json, copy
sys.path.insert(0, __import__('os').path.dirname(__file__))
import analyze_t226 as A

def hop(cy, a, b, th=35):
    pts = [(i, cy[i]) for i in range(a, min(b, len(cy) - 1) + 1) if cy[i] is not None]
    return any(abs(z - y) / (j - i) > th for (i, y), (j, z) in zip(pts, pts[1:]))

def main(mp, op):
    M = json.load(open(mp)); G = {}
    for k, r in M.items():
        if r['scene'] == 'P': continue
        g = copy.deepcopy(r)
        if g.get('dy8_src') == 'track' and hop(r['cy'], 0, 8): g['dy8'] = None
        if g.get('dyEnd_src') == 'track' and hop(r['cy'], 0, 92): g['dyEnd'] = None
        G[k] = g
    out = {}
    for sc in 'FH':
        out[sc] = {}
        for s in ('dy8', 'dyEnd', 'ncc_end'):
            X = {}
            for r in G.values():
                if r['scene'] == sc: X.setdefault(r['seed'], {})[r['arm']] = A.value(r, s)
            arms = A.ARMS[sc]
            out[sc][s] = dict(n_valid={a: sum(X[k].get(a) is not None for k in X) for a in arms},
                              contrasts={f'{c}-{ref}': A.contrast(X, c, ref) for c in arms[2:] for ref in ('neutral', 'base')})
            out[sc][s]['contrasts']['base-neutral'] = A.contrast(X, 'base', 'neutral')
    json.dump(out, open(op, 'w'), indent=1)
    for sc in out:
        for s in out[sc]:
            print(sc, s, out[sc][s]['n_valid'], {c: (round(v['mean'], 2), v['signflip_p'], v['n']) if 'mean' in v else v['n']
                                                for c, v in out[sc][s]['contrasts'].items() if c.endswith('neutral')})

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
