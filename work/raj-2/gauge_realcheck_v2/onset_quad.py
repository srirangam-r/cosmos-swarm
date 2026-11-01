# raj-2: on GAUGE real video (dedup timing A, mocap-calibrated px/m), compare the v0=0 hinge with a free-v0 quadratic
# started k distinct frames after the hinge onset t0 (raj-3's msg 141 recommendation: slow gripper release).
# Run from the GAUGE data dir: python3 onset_quad.py <repo_root>
import sys, json, numpy as np, cv2
sys.path.insert(0, sys.argv[1] + '/tools/trk_ballfall'); import measure_ball as mb
exec(open(__file__.rsplit('/', 1)[0] + '/real_ball.py').read().split('rows = {}')[0].split('import measure_ball as mb')[1])
RB = json.load(open('real_ball_results.json')); out = {}
for i in range(1, 23):
    r0 = RB[str(i)]
    if not r0 or r0['n_fit'] < 10: continue
    B = json.load(open(f'tracks/{i}.json')); dup, n = dups(f'video/{i}.mp4')
    keep = [k for k in range(len(B)) if k not in dup]; fsrc = FPS * len(keep) / len(B)
    cy = np.array([B[k][1] if B[k] else np.nan for k in keep]); t = np.arange(len(keep)) / fsrc
    hold = np.nanmedian(cy[:8]); r = int(np.argmax(cy > hold + 4)); a = max(r - 6, 0)
    k = next(j for j in range(r + 1, min(r + 30, len(cy) - 1)) if cy[j + 1] < cy[j] - 3)
    idx = np.arange(a, k); idx = idx[~np.isnan(cy[idx])]; ppm = r0['ppm_cal']
    p = mb.fit_hinge(t[idx], cy[idx] / ppm); res = dict(hinge=float(p[1]))
    j0 = int(np.searchsorted(t, p[2]))                       # first distinct frame after hinge onset
    for skip in (0, 1, 2):
        s = idx[idx >= j0 + skip]
        if len(s) >= 4:
            c = np.polyfit(t[s], cy[s] / ppm, 2); res[f'quad_skip{skip}'] = float(2 * c[0]); res[f'n_skip{skip}'] = int(len(s))
    out[i] = res; print(i, {kk: round(v, 2) for kk, v in res.items()})
json.dump(out, open('onset_quad_results.json', 'w'), indent=1)
for kk in ['hinge', 'quad_skip0', 'quad_skip1', 'quad_skip2']:
    v = np.array([o[kk] for o in out.values() if kk in o]); md = np.median(v)
    print(kk, f'mean {v.mean():.2f} ± {v.std(ddof=1)/np.sqrt(len(v)):.2f} SE (sd {v.std(ddof=1):.2f}, median {md:.2f}, n={len(v)})')
