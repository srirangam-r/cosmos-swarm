# raj-2: realball CLI code (tools/realball v1.1) on all 22 GAUGE real drops, mpp from mocap calibration (1/830.5 m/px).
import sys, json, numpy as np
sys.path.insert(0, sys.argv[1] + '/tools/realball'); import realball, trk
out = {}
for i in range(1, 23):
    try: r = realball.measure(trk.load(f'video/{i}.mp4'), 30.0, mpp=1 / 830.5, nboot=100)
    except Exception as ex: r = dict(err=repr(ex))
    out[i] = r; print(i, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items() if k in ('g', 'g_ci95', 'n_fit', 'rms_m', 'dup_period', 't0', 'err')}, flush=True)
json.dump(out, open('realball_gauge_results.json', 'w'), indent=1)
g = np.array([r['g'] for r in out.values() if 'g' in r]); print(f'all: {g.mean():.2f} ± {g.std(ddof=1)/np.sqrt(len(g)):.2f} sd {g.std(ddof=1):.2f} median {np.median(g):.2f} n={len(g)} within10% {np.mean(abs(g/9.81-1)<0.1):.2f}')
q = np.array([r['g'] for r in out.values() if 'g' in r and r['n_fit'] >= 5 and r['rms_m'] * 830.5 < 8])
print(f'rms<8px & n_fit>=5: {q.mean():.2f} ± {q.std(ddof=1)/np.sqrt(len(q)):.2f} sd {q.std(ddof=1):.2f} median {np.median(q):.2f} n={len(q)} within10% {np.mean(abs(q/9.81-1)<0.1):.2f}')
