"""kiro-1 t185: measure_pend v1 (unchanged) on the k185 Nano clips; summarise per input vs real_ref.json."""
import sys, os, glob, json, numpy as np
repo, cdir = sys.argv[1:3]
sys.path.insert(0, repo + '/tools/trk_ballfall')
import trk, measure_pend as mp
res = {}
for p in sorted(glob.glob(cdir + '/k185_*.mp4')):
    n = os.path.basename(p)[:-4]; F = trk.load(p)
    r = mp.measure(F, 24.0, keep_track=True); mp.qc(F, r, f'qc/{n}.png'); r.pop('track'); res[n] = r
    print(n, r['flag'], round(r['period_s'], 3), 'zc', round(r['period_zc_s'], 3) if r['period_zc_s'] else None, 'R2', round(r['r2'], 3), 'nh', r['n_halfcycles'])
ref = json.load(open('real_ref.json')); summ = {}
for tag, rk in [('p10f93', 'pend10_f93'), ('p12f101', 'pend12_f101')]:
    Treal = ref[rk]['video']['period_s']
    allT = [r['period_s'] for n, r in res.items() if f'_{tag}_' in n]
    okT = [r['period_s'] for n, r in res.items() if f'_{tag}_' in n and r['r2'] > 0.8]
    a = np.array(okT); m = a.mean(); se = a.std(ddof=1) / np.sqrt(len(a)) if len(a) > 1 else float('nan')
    summ[tag] = dict(T_real=Treal, n_all=len(allT), n_r2_gt_0p8=len(a), T_nano_mean=m, T_nano_se=se, ratio=m / Treal, ratio_se=se / Treal,
                     flags={n: (r['flag'], r['r2']) for n, r in res.items() if f'_{tag}_' in n})
    print(tag, summ[tag])
json.dump(dict(clips=res, summary=summ), open('nano_periods.json', 'w'), indent=1, default=float)
