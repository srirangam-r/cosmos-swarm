"""Task 226 pendulum readout (rahul-api-2). Frozen before the task-226 pendulum clips exist.

Per clip (pend10_mid_f93 input, 832x480):
  me_all   tracker-free motion: mean |gray(F_t) - gray(F_t-1)| inside a fixed disk around the pivot (r = 165 px,
           pivot (322,127), L ~132 px), averaged over frames 1..N-1. Exists for every clip, including a stopped one.
  me_late  the same over frames 46..N-1 (second half of a 93 f clip).
  curve    the per-frame motion values (for the seed-carryover test).
  pend     measure_pend v1 (tools/trk_ballfall, planted PASS): period_s, flag (ok/check), r2, n_halfcycles, amp_px,
           and rms_px = RMS of the principal-axis track s(t). NaN if the tracker finds no motion.
Contrasts (arm labels from the sidecar, see --arm-key): for each (A, B) the seed-paired differences of
  log(me_all), log(me_late) and, on seeds where BOTH clips are flag 'ok', log(T_A / T_B);
  mean diff, d = mean diff / SD across seeds of arm B (the seed spread), exact whole-seed sign-flip p (two-sided).
Seed carryover: mean Pearson r between motion curves of arm A and arm B at the SAME seed vs the permutation null
  (seed labels of B permuted; exact over all permutations up to 8 seeds).
Usage: python -I readout.py measure CLIPDIR OUT.json [--glob '*.mp4']
       python -I readout.py analyze OUT.json RESULT.json --arms base,N,STOP,FAST --contrasts STOP:base,FAST:base,N:base,STOP:N,FAST:N
"""
import sys, os, json, glob, re, argparse, itertools
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.normpath(os.path.join(HERE, '..', '..', '..', 'tools', 'trk_ballfall'))
sys.path.insert(0, TOOLS)
import trk, measure_pend as mp  # noqa: E402

PIVOT = (322.0, 127.0); R_ROI = 165.0; LATE0 = 46


def roi_mask(h, w):
    yy, xx = np.mgrid[0:h, 0:w]
    return ((xx - PIVOT[0]) ** 2 + (yy - PIVOT[1]) ** 2) <= R_ROI ** 2


def motion(F):
    G = F.mean(3) if F.ndim == 4 else F
    m = roi_mask(*G.shape[1:3])
    d = np.abs(np.diff(G, axis=0))[:, m].mean(1)  # d[k] = motion between frame k and k+1
    return d


def measure_clip(path, fps=24.0):
    F = trk.load(path)
    d = motion(F)
    r = dict(clip=os.path.basename(path), n_frames=int(len(F)), fps=fps,
             me_all=float(d.mean()), me_late=float(d[LATE0 - 1:].mean()) if len(d) >= LATE0 else float('nan'),
             curve=[float(x) for x in d])
    try:
        p = mp.measure(F, fps, nboot=100, keep_track=True)
        s = np.array([x[2] for x in p.pop('track')])
        p['rms_px'] = float(np.sqrt(np.mean((s - s.mean()) ** 2)))
        r['pend'] = p
    except Exception as e:  # stopped clip: no blob, or too few points
        r['pend'] = dict(flag='fail', error=repr(e)[:200], period_s=float('nan'), rms_px=float('nan'))
    side = os.path.splitext(path)[0] + '.json'
    if os.path.exists(side):
        try:
            sc = json.load(open(side))
            r['sidecar'] = {k: sc.get(k) for k in ('name', 'seed', 'prompt', 'num_frames', 'fps', 'endpoint')}
            r['sidecar']['extra_params'] = sc.get('extra_params') or (sc.get('request') or {}).get('extra_params')
        except Exception:
            pass
    return r


def signflip_p(x):
    x = np.asarray(x, float); n = len(x)
    if n == 0:
        return float('nan')
    obs = abs(x.mean()); cnt = 0; tot = 0
    for sg in itertools.product((1, -1), repeat=n):
        tot += 1; cnt += abs((x * np.array(sg)).mean()) >= obs - 1e-12
    return cnt / tot


def paired(rows, A, B, key):
    """rows: {(arm, seed): value}. Returns paired stats of A - B over seeds having finite values in both."""
    seeds = sorted({s for (a, s) in rows if a == A} & {s for (a, s) in rows if a == B})
    pairs = [(s, rows[(A, s)], rows[(B, s)]) for s in seeds
             if np.isfinite(rows[(A, s)]) and np.isfinite(rows[(B, s)])]
    if not pairs:
        return dict(key=key, n=0)
    dif = np.array([a - b for _, a, b in pairs]); bvals = np.array([rows[(B, s)] for s in seeds if np.isfinite(rows[(B, s)])])
    sdB = float(np.std(bvals, ddof=1)) if len(bvals) > 1 else float('nan')
    se = float(np.std(dif, ddof=1) / np.sqrt(len(dif))) if len(dif) > 1 else float('nan')
    return dict(key=key, n=len(dif), seeds=[s for s, _, _ in pairs], diffs=[float(x) for x in dif],
                mean_diff=float(dif.mean()), se=se, sd_seed_B=sdB,
                d_vs_seed_spread=float(dif.mean() / sdB) if sdB and np.isfinite(sdB) and sdB > 0 else float('nan'),
                ratio_geo=float(np.exp(dif.mean())), signflip_p=signflip_p(dif),
                n_same_sign=int(max((dif > 0).sum(), (dif < 0).sum())))


def carryover(curves, A, B, max_exact=8, nperm=20000, seed=0):
    seeds = sorted({s for (a, s) in curves if a == A} & {s for (a, s) in curves if a == B})
    if len(seeds) < 3:
        return dict(n=len(seeds))
    L = min(min(len(curves[(A, s)]), len(curves[(B, s)])) for s in seeds)
    XA = np.array([curves[(A, s)][:L] for s in seeds]); XB = np.array([curves[(B, s)][:L] for s in seeds])
    C = np.corrcoef(XA, XB)[:len(seeds), len(seeds):]
    same = float(np.mean(np.diag(C))); off = float((C.sum() - np.trace(C)) / (C.size - len(seeds)))
    n = len(seeds); vals = []
    if n <= max_exact:
        for pmt in itertools.permutations(range(n)):
            vals.append(np.mean(C[np.arange(n), list(pmt)]))
    else:
        rng = np.random.default_rng(seed)
        for _ in range(nperm):
            vals.append(np.mean(C[np.arange(n), rng.permutation(n)]))
    vals = np.array(vals)
    return dict(n=n, seeds=seeds, r_same_seed=same, r_diff_seed=off, r_same_each=[float(x) for x in np.diag(C)],
                perm_p=float(np.mean(vals >= same - 1e-12)))


def analyze(meas, arms, contrasts, arm_key='arm'):
    tab = {}; curves = {}
    for r in meas:
        ep = (r.get('sidecar') or {}).get('extra_params') or {}
        arm = r.get('arm') or ep.get(arm_key); seed = r.get('seed') or (r.get('sidecar') or {}).get('seed') or ep.get('seed')
        if arm is None or seed is None:
            continue
        tab[(arm, int(seed))] = r; curves[(arm, int(seed))] = np.array(r['curve'])
    out = dict(arms={}, contrasts={}, carryover={})
    for a in arms:
        rs = [v for (aa, s), v in tab.items() if aa == a]
        T = [v['pend'].get('period_s') for v in rs if v['pend'].get('flag') == 'ok']
        out['arms'][a] = dict(n=len(rs), n_ok=len(T), n_fail=sum(v['pend'].get('flag') == 'fail' for v in rs),
                              me_all_geo=float(np.exp(np.mean([np.log(v['me_all']) for v in rs]))) if rs else None,
                              me_late_geo=float(np.exp(np.mean([np.log(v['me_late']) for v in rs]))) if rs else None,
                              T_ok_geo=float(np.exp(np.mean(np.log(T)))) if T else None, T_ok=T)
    for c in contrasts:
        A, B = c.split(':')
        res = {}
        for key, f in (('log_me_all', lambda v: np.log(v['me_all'])), ('log_me_late', lambda v: np.log(v['me_late'])),
                       ('log_rms_px', lambda v: np.log(v['pend'].get('rms_px', np.nan)) if v['pend'].get('rms_px', 0) > 0 else np.nan),
                       ('log_T_ok', lambda v: np.log(v['pend']['period_s']) if v['pend'].get('flag') == 'ok' else np.nan),
                       ('log_T_any', lambda v: np.log(v['pend']['period_s']) if np.isfinite(v['pend'].get('period_s', np.nan)) else np.nan)):
            rows = {k: float(f(v)) for k, v in tab.items() if k[0] in (A, B)}
            res[key] = paired(rows, A, B, key)
        out['contrasts'][c] = res
        out['carryover'][c] = carryover(curves, A, B)
    return out


def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('measure'); m.add_argument('clipdir'); m.add_argument('out'); m.add_argument('--glob', default='*.mp4')
    m.add_argument('--fps', type=float, default=24.0)
    z = sub.add_parser('analyze'); z.add_argument('meas'); z.add_argument('out')
    z.add_argument('--arms', required=True); z.add_argument('--contrasts', required=True); z.add_argument('--arm-key', default='arm')
    o = ap.parse_args()
    if o.cmd == 'measure':
        res = []
        for p in sorted(glob.glob(os.path.join(o.clipdir, o.glob))):
            r = measure_clip(p, o.fps); res.append(r)
            pe = r['pend']; print(f"{r['clip']}: me_all {r['me_all']:.3f} me_late {r['me_late']:.3f} T {pe.get('period_s', float('nan')):.3f} {pe.get('flag')}", flush=True)
        json.dump(res, open(o.out, 'w'))
    else:
        meas = json.load(open(o.meas))
        out = analyze(meas, o.arms.split(','), o.contrasts.split(','), o.arm_key)
        json.dump(out, open(o.out, 'w'), indent=1)
        for c, res in out['contrasts'].items():
            for k, v in res.items():
                if v.get('n'):
                    print(f"{c:10s} {k:12s} n={v['n']} ratio {v['ratio_geo']:.3f} d={v['d_vs_seed_spread']:.2f} p={v['signflip_p']:.3f}")
            co = out['carryover'][c]
            if co.get('n', 0) >= 3:
                print(f"{c:10s} carryover r_same {co['r_same_seed']:.3f} r_diff {co['r_diff_seed']:.3f} perm p {co['perm_p']:.4f}")


if __name__ == '__main__':
    main()
