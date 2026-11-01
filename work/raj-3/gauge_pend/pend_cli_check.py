"""Run the measure_pend v1 CLI code path on the letterboxed real GAUGE pendulum clips (pseudo-Cosmos) and compare with mocap.
fps = the distinct-frame rate stored in pend_pseudo_cosmos_results.json. Writes QC images and pend_cli_results.json.
Usage: python3 -I pend_cli_check.py <pseudo_cosmos_pend dir> <repo_root>"""
import sys, json, numpy as np
d, repo = sys.argv[1:3]; sys.path.insert(0, repo + '/tools/trk_ballfall'); import trk, measure_pend as mp
B = json.load(open(f'{d}/pend_pseudo_cosmos_results.json')); out = {}
for i, b in B.items():
    F = trk.load(f'{d}/pend{i}_lb832.mp4'); r = mp.measure(F, b['fps'], nboot=200, keep_track=True)
    mp.qc(F, r, f'{d}/pend{i}_qc.png'); r.pop('track')
    r['T_mocap_zc'] = b['T_mocap_zc']; r['ratio'] = r['period_s'] / b['T_mocap_zc']; r['ratio_zc'] = r['period_zc_s'] / b['T_mocap_zc']
    r['T_pend_unchanged'] = b['T_pend_unchanged']; r['covers_mocap'] = bool(r['period_ci95'][0] <= b['T_mocap_zc'] <= r['period_ci95'][1])
    out[i] = r; print(i, r['flag'], *(f"{k}={r[k]:.4f}" for k in ('period_s', 'period_zc_s', 'T_mocap_zc', 'ratio', 'r2', 'release_t')), [round(x, 3) for x in r['period_ci95']], flush=True)
json.dump(out, open(f'{d}/pend_cli_results.json', 'w'), indent=1)
for sel, name in ((lambda r: True, 'all'), (lambda r: r['flag'] == 'ok', 'flag=ok')):
    R = [r for r in out.values() if sel(r)]
    for k in ('ratio', 'ratio_zc'):
        v = np.array([r[k] for r in R]); print(f"{name} {k}: {v.mean():.4f} ± {v.std(ddof=1)/np.sqrt(len(v)):.4f} SE, sd {v.std(ddof=1):.4f}, range {v.min():.3f}-{v.max():.3f}, n={len(v)}")
    print(name, 'CI95 covers mocap:', sum(r['covers_mocap'] for r in R), '/', len(R))
u = np.array([b['T_pend_unchanged'] / b['T_mocap_zc'] for b in B.values()]); print('trk.pend unchanged ratio: median', np.median(u), 'n within 10%:', int((abs(u - 1) < 0.1).sum()), '/', len(u), 'n at 6 s bound:', int(sum(b['T_pend_unchanged'] > 5.9 for b in B.values())))
