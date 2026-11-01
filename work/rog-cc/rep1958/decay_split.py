"""Follow-up to #2079/#2081, prompted by scout-1 #2070 (test 2) and #2094 (region split).
(1) Does motion DECAY over the continuation?  E(k) = mean |G[cut+k+1]-G[cut+k]|; early = k in [0,32), late = k in [48,80);
    ratio R = late/early.  Hypothesis (A) "no rest state": Nano R ~ 1 while real R << 1.
(2) Region split (fixed camera, so no motion compensation): BALL-PATH ROI = largest connected blob of pixels the REAL
    continuation changes (|diff| > 10 gray in >= 3 of the 32 steps k in [0,32)), dilated 9 px; identical ROI for every mode of that cut.  STATIC = rest of
    the active frame.  Late motion is reported per region, so arm/background drift and ball-region motion are separated.
Inputs as rep1958.py (416x240 gray transcodes, ctx meta, real GAUGE videos).  Usage: decay_split.py CLIPDIR CTXDIR REALDIR OUT.json
"""
import json, sys, glob, os
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rep1958 import read_gray, letterbox, real_dedup, TOP, BOT

E0, E1, L0, L1 = 0, 32, 48, 80


def energies(fr, cut, mask):
    a = [f[TOP:BOT] for f in fr[cut:cut + L1 + 1]]
    if len(a) <= L1: return None
    d = [np.abs(a[k + 1] - a[k]) for k in range(L1)]
    out = {}
    for name, m in (('full', np.ones_like(mask)), ('ball', mask), ('static', ~mask)):
        e = np.array([x[m].mean() for x in d])
        out[name] = dict(early=float(e[E0:E1].mean()), late=float(e[L0:L1].mean()),
                         ratio=float(e[L0:L1].mean() / max(e[E0:E1].mean(), 1e-6)))
    return out


def main(clipdir, ctxdir, realdir, out):
    meta = json.load(open(os.path.join(ctxdir, 'meta.json')))
    res = {'real': {}, 'clips': {}, 'mask_frac': {}}
    masks = {}
    for cut, m in meta.items():
        vid = m['video'].split('/')[-1].replace('.mp4', '')
        raw, keep = real_dedup(os.path.join(realdir, f'ball{vid}.mp4'))
        r_last = m['raw_frames'][-1]
        d_last = min(range(len(keep)), key=lambda j: abs(keep[j] - r_last))
        lb = [letterbox(raw[i]) for i in keep]
        a = [f[TOP:BOT] for f in lb[d_last:d_last + E1 + 1]]
        cnt = sum((np.abs(a[k + 1] - a[k]) > 10).astype(np.uint8) for k in range(E1))
        n, lab, st, _ = cv2.connectedComponentsWithStats((cnt >= 3).astype(np.uint8), connectivity=8)
        big = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))  # largest moving blob in the real clip = the ball's path
        mv = cv2.dilate((lab == big).astype(np.uint8), np.ones((9, 9), np.uint8)) > 0
        res.setdefault('mask_bbox', {})[cut] = [int(v) for v in st[big, :4]]
        masks[cut] = mv; res['mask_frac'][cut] = float(mv.mean())
        res['real'][cut] = energies(lb, d_last, mv)
    for p in sorted(glob.glob(os.path.join(clipdir, '*.mp4'))):
        sc = json.load(open(p[:-4] + '.json'))
        cut = sc.get('last_real_frame_index_in_output', 0) or 0
        res['clips'][os.path.basename(p)[:-4]] = dict(cut=sc['cut'], mode=sc['mode'], seed=sc['seed'],
                                                      **(energies(read_gray(p), cut, masks[sc['cut']]) or {}))
    # summary: per cut type (pre/post), b1/b3 averaged within seed (as #1958/#2079), mean +- SE over seeds
    S = {}
    for typ in ('pre', 'post'):
        cuts = [c for c in masks if c.endswith(typ)]
        S[typ] = {'real': {r: {q: float(np.mean([res['real'][c][r][q] for c in cuts])) for q in ('early', 'late', 'ratio')}
                           for r in ('full', 'ball', 'static')}}
        for mode in sorted({v['mode'] for v in res['clips'].values()}):
            per_seed = {}
            for v in res['clips'].values():
                if v['mode'] == mode and v['cut'] in cuts and 'full' in v: per_seed.setdefault(v['seed'], []).append(v)
            S[typ][mode] = {}
            for r in ('full', 'ball', 'static'):
                S[typ][mode][r] = {}
                for q in ('early', 'late', 'ratio'):
                    x = np.array([np.mean([v[r][q] for v in vs]) for vs in per_seed.values()])
                    S[typ][mode][r][q] = [float(x.mean()), float(x.std(ddof=1) / np.sqrt(len(x))), len(x)]
    res['summary'] = S
    json.dump(res, open(out, 'w'), indent=1)
    for typ in S:
        print(f'== {typ} cut   (late = k48-80, early = k0-32; values mean +- SE over seeds)')
        for mode, v in S[typ].items():
            row = []
            for r in ('full', 'ball', 'static'):
                q = v[r]
                if mode == 'real': row.append(f"{r}: E {q['early']:.2f} L {q['late']:.2f} R {q['ratio']:.2f}")
                else: row.append(f"{r}: E {q['early'][0]:.2f} L {q['late'][0]:.2f}±{q['late'][1]:.2f} R {q['ratio'][0]:.2f}±{q['ratio'][1]:.2f}")
            print(f'{mode:6s} ' + ' | '.join(row))


if __name__ == '__main__':
    main(*sys.argv[1:5])
