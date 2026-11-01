"""raj-3: end-to-end check of the Cosmos-clip pipeline on REAL GAUGE ball drops.
Each real clip is deduplicated (25-in-30 fps), letterboxed 1280x720 -> 832x480 (scale 0.65, 6 px pad, as for Cosmos I2V inputs),
written as mp4 at its distinct-frame rate, then measured with the measure_ball v5 CLI code path (trk.blobs tracker, fixed px/m).
Scale: 830.5 px/m at 1280x720 (raj-2 mocap calibration, msg 146) x 0.65 = 539.8 px/m. Reference: mocap g, v5 estimator (skip=1).
Usage: python3 -I pseudo_cosmos.py <gauge_real_dir> <repo_root> <outdir>"""
import sys, json, numpy as np, cv2
root, repo, outd = sys.argv[1:4]
sys.path.insert(0, repo + '/tools/trk_ballfall'); import trk, measure_ball as mb
PPM = 830.5 * 0.65; res = {}
for i in range(1, 23):
    F = trk.load(f'{root}/video/{i}.mp4'); F, fac = mb.dedup(F); fps = 30.0 * fac
    L = np.zeros((len(F), 480, 832, 3), np.uint8)
    for k, f in enumerate(F): L[k, 6:474] = cv2.resize(f.clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA)
    p = f'{outd}/gauge{i}_lb832.mp4'; w = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(*'mp4v'), fps, (832, 480))
    for f in L: w.write(f)
    w.release()
    try:
        r = mb.measure(trk.load(p), fps, mpp=1 / PPM, nboot=100)
    except Exception as e:
        res[i] = dict(err=repr(e)); print(i, 'ERR', e); continue
    d = json.load(open(f'{root}/json/{i}.json')); z = np.array(d['ball']['z']) / 1000; t = np.arange(len(z)) / d['FPS']
    i0 = int(np.argmax(z)); j = i0 + 1
    while j < len(z) - 1 and not (z[j] <= z[j - 1] and z[j] < z[j + 1]): j += 1
    a = max(i0 - 8, 0); c, s, _ = mb.fit_onset(t[a:j], z[a] - z[a:j], d['FPS'], 1)
    r['g_mocap_v5'] = float(2 * c[0]); r['ratio'] = r['g'] / r['g_mocap_v5']
    res[i] = {k: v for k, v in r.items() if k not in ('method',)}
    print(i, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res[i].items() if k in ('g', 'g_ci95', 'r2', 'n_fit', 'onset_frame', 'impact_frame', 'g_hinge_v4', 'g_mocap_v5', 'ratio', 'fps')}, flush=True)
ok = [r for r in res.values() if 'err' not in r]
for key in ('g', 'ratio', 'g_hinge_v4'):
    v = np.array([r[key] for r in ok]); print(key, f'mean {v.mean():.3f} ± {v.std(ddof=1)/np.sqrt(len(v)):.3f} SE, sd {v.std(ddof=1):.3f}, median {np.median(v):.3f}, n={len(v)}')
rat = np.array([r['ratio'] for r in ok]); print('within 10%:', int((abs(rat - 1) < 0.1).sum()), '/', len(rat))
json.dump(dict(ppm=PPM, per_clip=res), open(f'{outd}/pseudo_cosmos_results.json', 'w'), indent=1, default=float)
