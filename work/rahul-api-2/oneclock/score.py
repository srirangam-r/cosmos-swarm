"""score.py (task 162, PREREG Amendment 2): rho1 per included clip from BOTH trackers, then a seed-clustered summary.
Usage: python3 -I score.py qc_codes.csv clip_dir out.json [--real real1.mp4 ...]
- segment valid for a tracker: a > 0, rms < 5 px, n >= 5
- both valid and median |y_t2 - y_ff| over the union of fall+flight1 frames < 4 px -> rho1 = mean of the two ('both')
- one valid -> that tracker ('single_tracker'); neither -> 'untracked'
Seed clustering: clips sharing a seed (ball1/ball2) are averaged in log rho1 first; 95% CI = bootstrap over seeds."""
import sys, os, csv, json, argparse, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oneclock

def valid(seg):
    return bool(seg) and seg['a'] > 0 and seg['rms'] < 5 and seg['n'] >= 5

def per_tracker(path, tr, fps):
    r = oneclock.run(path, fps, 539.8, (280.0, 116.0), tr)
    fl1 = r['flights'][0] if r.get('flights') else None
    ok = valid(r.get('fall')) and valid(fl1)
    return r, (r['flights'][0]['a'] / r['fall']['a'] if ok else None)

def score_clip(path, fps=24.0):
    (rt, xt), (rf, xf) = per_tracker(path, 't2', fps), per_tracker(path, 'ff', fps)
    yt = np.array([np.nan if v is None else v for v in rt['track_y']]); yf = np.array([np.nan if v is None else v for v in rf['track_y']])
    segs = [s for s in [rt.get('fall'), (rt.get('flights') or [None])[0], rf.get('fall'), (rf.get('flights') or [None])[0]] if s]
    fr = sorted({t for s in segs for t in range(s['t'][0], s['t'][1] + 1)})
    dy = np.abs(yt[fr] - yf[fr]) if fr else np.array([np.nan]); med = float(np.nanmedian(dy)) if np.isfinite(dy).any() else None
    if xt is not None and xf is not None and med is not None and med < 4: rho, how = float(np.exp((np.log(xt) + np.log(xf)) / 2)), 'both'
    elif xt is not None and xf is not None: rho, how = None, 'trackers_disagree'
    elif xt is not None: rho, how = xt, 'single_tracker_t2'
    elif xf is not None: rho, how = xf, 'single_tracker_ff'
    else: rho, how = None, 'untracked'
    pick = rt if how in ('both', 'single_tracker_t2') else rf
    return dict(clip=os.path.basename(path), rho1=rho, how=how, rho1_t2=xt, rho1_ff=xf, median_dy_px=med,
                a_fall=pick.get('fall', {}).get('a') if pick.get('fall') else None,
                a_flights=[f['a'] if f else None for f in pick.get('flights', [])], impacts=pick.get('impacts'))

def seed_of(name):
    return int(name.split('_s')[-1].split('.')[0])

if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('qc'); ap.add_argument('clips'); ap.add_argument('out')
    ap.add_argument('--real', nargs='*', default=[])
    a = ap.parse_args()
    inc = [row['clip'] for row in csv.DictReader(open(a.qc)) if row['include'].strip() == '1']
    res = [score_clip(os.path.join(a.clips, c + '.mp4')) for c in inc]
    for r in res: print(r['clip'], r['how'], 'rho1', None if r['rho1'] is None else round(r['rho1'], 3), 't2', r['rho1_t2'] and round(r['rho1_t2'], 3), 'ff', r['rho1_ff'] and round(r['rho1_ff'], 3), 'dy', r['median_dy_px'] and round(r['median_dy_px'], 1))
    by = {}
    for r in res:
        if r['rho1'] and r['rho1'] > 0: by.setdefault(seed_of(r['clip']), []).append(np.log(r['rho1']))
    L = np.array([np.mean(v) for v in by.values()]); summ = dict(n_clips=len(res), n_seeds=int(len(L)))
    if len(L):
        rng = np.random.default_rng(0); bs = [rng.choice(L, len(L)).mean() for _ in range(5000)]
        summ.update(geo_mean_rho1=float(np.exp(L.mean())), ci95=[float(np.exp(np.percentile(bs, 2.5))), float(np.exp(np.percentile(bs, 97.5)))],
                    seeds_above_1=int((L > 0).sum()), seeds_below_1=int((L < 0).sum()), per_seed={int(k): float(np.exp(np.mean(v))) for k, v in by.items()})
    real = [score_clip(p, 25.0) for p in a.real]
    for r in real: print('REAL', r['clip'], r['how'], r['rho1'] and round(r['rho1'], 3))
    print(json.dumps(summ))
    json.dump(dict(summary=summ, clips=res, real=real), open(a.out, 'w'), indent=1)
