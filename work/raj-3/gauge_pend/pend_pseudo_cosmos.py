"""raj-3 task 8: does a planted-passing period tool recover the real pendulum period at Cosmos resolution?
Per GAUGE real pendulum clip: read the first ~8 s, dedup (25-in-30 fps), keep 7.875 s (= 189 frames @24 fps window),
letterbox 1280x720 -> 832x468 + 6 px pad (the Cosmos I2V input transform), write mp4 at the distinct-frame fps,
then measure the period with
  (A) trk.pend unchanged (planted PASS, 4/4 period <5%),
  (B) release-aware: trk.blobs x-centroid, leading hold removed, damped sinusoid (beta free sign, like GAUGE eq. 43) + zero-crossings.
Reference: mocap x-swing zero-crossing period over the matched window after mocap release.
Usage: python3 -I pend_pseudo_cosmos.py <pend_dir with video/ json/> <repo_root> <outdir> [clip ids...]"""
import sys, json, os, numpy as np, cv2
from scipy.optimize import least_squares
root, repo, outd = sys.argv[1:4]; os.makedirs(outd, exist_ok=True)
ids = [int(a) for a in sys.argv[4:]] or list(range(1, 21))
sys.path.insert(0, repo + '/tools/trk_ballfall'); import trk, measure_ball as mb
WIN = 189 / 24.0
def read(p, n):
    c = cv2.VideoCapture(p); F = []
    while len(F) < n:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    return np.array(F)
def zc(t, x):
    xx = x - np.median(x); s = np.sign(xx); i = np.where((s[:-1] < 0) & (s[1:] >= 0))[0]
    j = np.where((s[:-1] > 0) & (s[1:] <= 0))[0]
    tc = lambda k: t[k] - xx[k] * (t[k + 1] - t[k]) / (xx[k + 1] - xx[k])
    d = np.concatenate([np.diff(tc(i)), np.diff(tc(j))]) if len(i) > 1 or len(j) > 1 else np.array([])
    return (float(np.median(d)) if len(d) else float('nan')), len(d)
def damped(t, x):
    best = None
    for T in np.linspace(0.6, 4.0, 35):
        def r(p):
            w = 2 * np.pi / p[0]; e = np.exp(-p[1] * t)
            return p[2] + e * (p[3] * np.cos(w * t) + p[4] * np.sin(w * t)) - x
        s = least_squares(r, [T, 0.0, np.median(x), x[0] - np.median(x), 0], bounds=([0.2, -3, -1e4, -1e4, -1e4], [20, 3, 1e4, 1e4, 1e4]))
        if best is None or s.cost < best.cost: best = s
    res = best.fun; r2 = 1 - np.sum(res ** 2) / np.sum((x - x.mean()) ** 2)
    return float(best.x[0]), float(best.x[1]), float(r2)
def release(x, tol):
    x0 = np.median(x[:3]); m = np.abs(x - x0) > tol
    for k in range(len(m) - 3):
        if m[k:k + 4].all(): return k
    return 0
out = {}
for i in ids:
    vp = f'{root}/video/{i}.mp4'
    if not os.path.exists(vp): continue
    R = read(vp, 250).astype(np.float32); Fd, fac = mb.dedup(R); fps = 30.0 * fac
    Fd = Fd[: int(np.floor(WIN * fps)) + 1]
    p = f'{outd}/pend{i}_lb832.mp4'; w = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(*'mp4v'), fps, (832, 480))
    for f in Fd:
        L = np.zeros((480, 832, 3), np.uint8); L[6:474] = cv2.resize(f.clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA); w.write(L)
    w.release()
    F = trk.load(p)
    rA = trk.pend(F, fps)['period_s']
    B = trk.blobs(F); ok = [k for k, b in enumerate(B) if b]
    x = np.array([B[k][0] for k in ok]); y = np.array([B[k][1] for k in ok]); t = np.array(ok) / fps
    k0 = release(x, 3.0); tv = t[k0:] - t[k0]; xv = x[k0:]
    TB, betaB, r2B = damped(tv, xv); TZ, nZ = zc(tv, xv)
    # mocap reference, matched window length after release
    d = json.load(open(f'{root}/json/{i}.json')); P = np.array([d['ball'][c] for c in 'xyz']).T / 1000; tm = np.arange(len(P)) / d['FPS']
    mu = P[:300].mean(0); _, _, Vt = np.linalg.svd(P[:300] - mu, full_matrices=False); a = (P - mu) @ Vt[0]
    km = release(a, 0.005); span = tv[-1]
    m = (tm >= tm[km]) & (tm <= tm[km] + span); Tm, nm = zc(tm[m] - tm[km], a[m]); Tmd, _, r2m = damped(tm[m] - tm[km], a[m])
    out[i] = dict(fps=fps, n_frames=len(F), n_tracked=len(ok), release_t_video=float(t[k0]), window_after_release_s=float(span),
                  T_pend_unchanged=rA, T_damped=TB, beta=betaB, r2=r2B, T_zc=TZ, n_halfcycles=nZ,
                  T_mocap_zc=Tm, T_mocap_damped=Tmd, ratio_unchanged=rA / Tm, ratio_damped=TB / Tm, ratio_zc=TZ / Tm)
    print(i, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in out[i].items()}, flush=True)
json.dump(out, open(f'{outd}/pend_pseudo_cosmos_results.json', 'w'), indent=1)
for key in ('T_mocap_zc', 'T_pend_unchanged', 'T_damped', 'T_zc', 'ratio_unchanged', 'ratio_damped', 'ratio_zc'):
    v = np.array([o[key] for o in out.values()]); print(f'{key}: mean {v.mean():.4f} ± {v.std(ddof=1)/np.sqrt(len(v)):.4f} SE, sd {v.std(ddof=1):.4f}, median {np.median(v):.4f}, n={len(v)}')
