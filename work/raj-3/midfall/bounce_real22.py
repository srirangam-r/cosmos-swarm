"""raj-3: measure_bounce v1 on the 22 letterboxed real GAUGE drops (pseudo_cosmos/gauge<i>_lb832.mp4, 832x480, distinct-frame fps)."""
import sys, json, numpy as np
repo, d = sys.argv[1], sys.argv[2]; sys.path.insert(0, repo + '/tools/trk_ballfall'); import trk, measure_bounce as mbb, measure_ball as mb
import cv2
res = {}
for i in range(1, 23):
    p = f'{d}/gauge{i}_lb832.mp4'; fps = cv2.VideoCapture(p).get(cv2.CAP_PROP_FPS)
    F = trk.load(p); r = mbb.measure(F, fps, mpp=1 / 539.8)
    if r['flag'] != 'ok':
        r2 = mbb.measure(F, fps, mpp=1 / 539.8, tracker='diff')
        if r2['flag'] == 'ok': r = r2
    res[i] = {k: v for k, v in r.items() if k != 'track'}
    print(i, round(fps, 2), r['flag'], r['tracker'], r['g'] and round(r['g'], 3), r.get('n_flights'), r.get('g_per_flight') and np.round(r['g_per_flight'], 2).tolist(), flush=True)
json.dump(res, open(sys.argv[3], 'w'), indent=1)
g = np.array([r['g'] for r in res.values() if r['flag'] == 'ok'])
print(f'flag=ok n={len(g)}: {g.mean():.3f} +- {g.std(ddof=1)/np.sqrt(len(g)):.3f} (sd {g.std(ddof=1):.3f}, median {np.median(g):.3f})')
