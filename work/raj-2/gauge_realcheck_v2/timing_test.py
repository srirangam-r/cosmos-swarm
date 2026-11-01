# raj-2 (run from the gauge data dir: python3 timing_test.py <repo_root>; needs real_ball_results.json): which timestamp model fits real GAUGE ball falls best? A: drop dups, uniform t=k/fps_src; B: keep dups t=i/30;
# C: drop dups, keep t=i/30. Same frames (release-6 .. impact-1), same hinge fit, scale = mocap-calibrated ppm.
import sys, json, numpy as np, cv2
sys.path.insert(0, sys.argv[1] + '/tools/trk_ballfall'); import measure_ball as mb
exec(open(__file__.rsplit('/', 1)[0] + '/real_ball.py').read().split('rows = {}')[0].split('import measure_ball as mb')[1])
RB = json.load(open('real_ball_results.json')); out = {}
for i in range(1, 23):
    r0 = RB[str(i)]
    if not r0 or r0['n_fit'] < 10: continue
    B = json.load(open(f'tracks/{i}.json')); dup, n = dups(f'video/{i}.mp4')
    keep = [k for k in range(len(B)) if k not in dup]; fsrc = FPS * len(keep) / len(B)
    cy = np.array([B[k][1] if B[k] else np.nan for k in keep])
    hold = np.nanmedian(cy[:8]); r = int(np.argmax(cy > hold + 4)); a = max(r - 6, 0)
    k = next(j for j in range(r + 1, min(r + 30, len(cy) - 1)) if cy[j + 1] < cy[j] - 3)
    lo, hi = keep[a], keep[k]; ppm = r0['ppm_cal']; res = {}
    for name, fr, tt in [('A', [kk for kk in keep if lo <= kk < hi], None), ('B', list(range(lo, hi)), None), ('C', [kk for kk in keep if lo <= kk < hi], None)]:
        fr = [kk for kk in fr if B[kk]]
        t = (np.array([keep.index(kk) for kk in fr]) / fsrc) if name == 'A' else np.array(fr) / FPS
        Y = np.array([B[kk][1] for kk in fr]) / ppm
        p = mb.fit_hinge(t, Y); m = t > p[2]
        rms = np.sqrt(np.mean((Y - mb.hinge(p, t))[m] ** 2)) * ppm
        res[name] = dict(g=float(p[1]), ratio=float(p[1] / r0['mocap_g_hinge']), rms_px=float(rms), n=int(m.sum()))
    out[i] = res; print(i, {kk: (round(v['ratio'], 3), round(v['rms_px'], 2)) for kk, v in res.items()})
for kk in 'ABC':
    v = np.array([o[kk]['ratio'] for o in out.values()]); e = np.array([o[kk]['rms_px'] for o in out.values()])
    print(kk, f'g/mocap {v.mean():.3f} ± {v.std(ddof=1)/np.sqrt(len(v)):.3f} (sd {v.std(ddof=1):.3f}, med {np.median(v):.3f}); median fit rms {np.median(e):.2f} px; n={len(v)}')
json.dump(out, open('timing_test_results.json', 'w'), indent=1)
