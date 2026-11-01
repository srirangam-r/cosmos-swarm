"""pool.py (task 162, Amendments 3+4): combine score.py outputs (seeds 21-50 on q8, seeds 51-110 on brev-p6k) and report,
for each part and pooled: seed-clustered geo-mean rho1 with the preregistered bootstrap (5000 draws, rng seed 0; labelled
'descriptive' when n_seeds < 10), a log-t 95% interval (Amd 4 sensitivity), ball1/ball2 counts, per-clip t2/ff rho1, and the
same summary after dropping clips whose two valid trackers differ by > 25% (Amd 4 item 2).
Usage: python3 -I pool.py out.json q8=score_all_s21-50.json brev=score_amd3.json"""
import sys, json, numpy as np
from scipy import stats
def seed(c): return int(c.split('_s')[-1].split('.')[0])
def divergent(r): return bool(r['rho1_t2'] is not None and r['rho1_ff'] is not None and abs(np.log(r['rho1_t2'] / r['rho1_ff'])) > np.log(1.25))
def summ(clips):
    by = {}
    for r in clips:
        if r['rho1'] and r['rho1'] > 0: by.setdefault(seed(r['clip']), []).append(np.log(r['rho1']))
    L = np.array([np.mean(v) for v in by.values()])
    used = [r for r in clips if r['rho1'] and r['rho1'] > 0]
    s = dict(n_clips_scored=len(clips), n_clips_with_rho=len(used), n_seeds=int(len(L)),
             ball1=sum('ball1' in r['clip'] for r in used), ball2=sum('ball2' in r['clip'] for r in used),
             how={h: sum(r['how'] == h for r in clips) for h in sorted({r['how'] for r in clips})})
    if len(L):
        rng = np.random.default_rng(0); bs = [rng.choice(L, len(L)).mean() for _ in range(5000)]
        s.update(geo_mean_rho1=float(np.exp(L.mean())),
                 boot_ci95=[float(np.exp(np.percentile(bs, 2.5))), float(np.exp(np.percentile(bs, 97.5)))],
                 boot_label='descriptive (n_seeds<10)' if len(L) < 10 else 'preregistered',
                 seeds_above_1=int((L > 0).sum()), seeds_below_1=int((L < 0).sum()),
                 per_seed={int(k): round(float(np.exp(np.mean(v))), 3) for k, v in sorted(by.items())})
        if len(L) >= 2:
            h = stats.t.ppf(0.975, len(L) - 1) * L.std(ddof=1) / np.sqrt(len(L))
            s['logt_ci95'] = [float(np.exp(L.mean() - h)), float(np.exp(L.mean() + h))]
    return s
out, parts = sys.argv[1], dict(a.split('=', 1) for a in sys.argv[2:])
C = {k: json.load(open(v))['clips'] for k, v in parts.items()}
allc = [r for v in C.values() for r in v]
res = {k: summ(v) for k, v in C.items()}; res['pooled'] = summ(allc)
res['pooled_drop_tracker_divergent'] = summ([r for r in allc if not divergent(r)])
res['per_clip'] = [dict(clip=r['clip'], how=r['how'], rho1=r['rho1'], rho1_t2=r['rho1_t2'], rho1_ff=r['rho1_ff'],
                        tracker_divergent=divergent(r), a_fall=r['a_fall']) for r in allc]
res['inputs'] = parts
print(json.dumps({k: v for k, v in res.items() if k != 'per_clip'}, indent=1)); json.dump(res, open(out, 'w'), indent=1)
