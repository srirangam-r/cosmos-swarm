"""raj-2: independent check that rahul-3 sim_drop v1 real-g clips encode g=9.81, with planted-passing tools
(firstfall v1 auto-seed, realball v1.1), scale = meta px_per_m only (no ground-truth tracks used)."""
import sys, json, glob, os, numpy as np
repo = sys.argv[1]; d = sys.argv[2]
sys.path.insert(0, repo + '/tools/realball'); sys.path.insert(0, repo + '/tools/trk_ballfall')
import trk, realball, firstfall as ff
res = {}
for m in sorted(glob.glob(d + '/meta/*.json')):
    M = json.load(open(m)); n = M['name']; F = trk.load(f'{d}/videos/{n}.mp4'); r = {'g_true': M['g'], 'px_per_m': M['px_per_m'], 'holder': M['holder'], 'h_m': M['h_m']}
    try:
        a, tr = ff.measure(F, M['fps'], ppm=M['px_per_m'], nboot=100); r.update(ff_g=a['g'], ff_ci=a['g_ci95'], ff_flag=a['flag'], ff_n=a['n_fit'], ff_T=a['fall_time_s'], ff_h=a['fall_m'])
        ff.qc_png(f'{d}/{n}_ffqc.png', F, tr, a)
    except Exception as e: r['ff_err'] = repr(e)
    try:
        b = realball.measure(F, M['fps'], mpp=1 / M['px_per_m'], nboot=100, no_dedup=True); r.update(rb_g=b['g'], rb_ci=b['g_ci95'], rb_n=b['n_fit'], rb_r2=b['r2'])
    except Exception as e: r['rb_err'] = repr(e)
    res[n] = r; print(n, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k in ('ff_g', 'ff_flag', 'rb_g', 'rb_r2', 'holder', 'ff_err', 'rb_err')}, flush=True)
for key, flt in (('ff_g', lambda r: r.get('ff_flag') == 'ok'), ('rb_g', lambda r: 'rb_g' in r)):
    v = np.array([r[key] / r['g_true'] for r in res.values() if key in r and flt(r)])
    if len(v): print(key, f'ratio mean {v.mean():.3f} ± {v.std(ddof=1)/np.sqrt(len(v)):.3f} SE, sd {v.std(ddof=1):.3f}, median {np.median(v):.3f}, n={len(v)}, within10 {int((abs(v-1)<0.1).sum())}')
json.dump(res, open(d + '/simdrop_check_results.json', 'w'), indent=1, default=float)
