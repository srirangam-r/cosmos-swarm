"""measure_pend v1 (raj-3): pendulum period from one clip, release-aware.
Why: trk.pend fits from frame 0. On real GAUGE pendulum video the robot holds the pendulum for ~2.6 s before release,
and trk.pend then returns its 6 s bound (true 1.18 s). Cosmos clips made from GAUGE first frames can hold too.
Method:
  track  trk.blobs (temporal-median background diff, largest blob centroid); project the centroid onto the
         principal axis of its post-release motion -> s(t) in px (period needs no metric scale)
  release first frame of a sustained (4-frame) departure > tol px from the initial position; frames before are dropped
  fit    damped sinusoid s = c + e^{-beta t}(A cos wt + B sin wt), beta free sign (as GAUGE eq. 43), T = 2 pi / w,
         global over a T grid; plus the median full period from successive same-direction zero crossings (T_zc)
  CI     residual moving-block bootstrap of the damped fit (block = 1/4 of the fitted period)
  flag   ok if >= 3 half-cycles seen, R2 > 0.8, |T_fit - T_zc| / T_fit < 0.05, >= 90% frames tracked
Usage: python3 -I measure_pend.py clip.mp4 --fps 24 [--dedup] [--tol 3] [--qc out.png]"""
import sys, os, json, argparse, numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import trk

def release(s, tol):
    s0 = np.median(s[:3]); m = np.abs(s - s0) > tol
    for k in range(len(m) - 3):
        if m[k:k + 4].all(): return k
    return 0

def zc_period(t, s):
    x = s - np.median(s); sg = np.sign(x); out = []
    for up in (True, False):
        i = np.where((sg[:-1] < 0) & (sg[1:] >= 0))[0] if up else np.where((sg[:-1] > 0) & (sg[1:] <= 0))[0]
        tc = t[i] - x[i] * (t[i + 1] - t[i]) / (x[i + 1] - x[i])
        out += list(np.diff(tc))
    n_half = int(np.sum(sg[:-1] * sg[1:] < 0))
    return (float(np.median(out)) if out else float('nan')), n_half, out

def _fit(t, s, Tgrid):
    best = None
    for T in Tgrid:
        def r(p):
            w = 2 * np.pi / p[0]; e = np.exp(-p[1] * t)
            return p[2] + e * (p[3] * np.cos(w * t) + p[4] * np.sin(w * t)) - s
        try:
            z = least_squares(r, [T, 0.0, np.median(s), s[0] - np.median(s), 0.0],
                              bounds=([0.15, -3, -1e5, -1e5, -1e5], [60, 3, 1e5, 1e5, 1e5]))
        except Exception: continue
        if best is None or z.cost < best.cost: best = z
    return best

def measure(F, fps, tol=3.0, nboot=200, seed=0, keep_track=False):
    B = trk.blobs(F); ok = [k for k, b in enumerate(B) if b]
    P = np.array([[B[k][0], B[k][1]] for k in ok], float); t_all = np.array(ok) / fps
    k0 = release(P[:, 0], tol) if np.ptp(P[:, 0]) >= np.ptp(P[:, 1]) else release(P[:, 1], tol)
    Q = P[k0:] - P[k0:].mean(0); _, _, Vt = np.linalg.svd(Q, full_matrices=False)
    s = Q @ Vt[0]; t = t_all[k0:] - t_all[k0]
    Tzc, n_half, per = zc_period(t, s)
    dur = t[-1]; Tgrid = np.unique(np.concatenate([np.linspace(0.3, max(1.0, 2 * dur), 40), [Tzc] if np.isfinite(Tzc) else []]))
    z = _fit(t, s, Tgrid); T, beta = float(z.x[0]), float(z.x[1]); res = z.fun; fit = s + res
    r2 = float(1 - np.sum(res ** 2) / np.sum((s - s.mean()) ** 2))
    rng = np.random.default_rng(seed); L = max(2, int(round(T * fps / 4))); n = len(s); Tb = []
    for _ in range(nboot):
        idx = np.concatenate([np.arange(st, st + L) % n for st in rng.integers(0, n, n // L + 1)])[:n]
        zb = _fit(t, fit + res[idx], [T]); Tb.append(zb.x[0])
    ci = [float(np.percentile(Tb, 2.5)), float(np.percentile(Tb, 97.5))]
    frac = len(ok) / len(F)
    flag = 'ok' if (n_half >= 3 and r2 > 0.8 and np.isfinite(Tzc) and abs(T - Tzc) / T < 0.05 and frac >= 0.9) else 'check'
    r = dict(method='measure_pend v1', period_s=T, period_ci95=ci, period_zc_s=Tzc, zc_periods=[float(p) for p in per],
             beta=beta, r2=r2, n_halfcycles=n_half, release_frame=int(ok[k0]), release_t=float(t_all[k0]),
             fit_window_s=float(dur), frac_tracked=float(frac), amp_px=float(np.ptp(s) / 2), fps=fps, flag=flag)
    if keep_track: r['track'] = [[int(ok[k0 + i]), float(t[i]), float(s[i]), float(fit[i])] for i in range(len(s))]
    return r

def qc(F, r, path):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, cv2
    tr = np.array(r['track']); fig = plt.figure(figsize=(14, 5)); ax = fig.add_subplot(1, 2, 1)
    ax.plot(tr[:, 1], tr[:, 2], '.', ms=4, label='tracked s (px, principal axis)'); ax.plot(tr[:, 1], tr[:, 3], '-', label='damped fit')
    ax.set_xlabel('t since release (s)'); ax.legend(fontsize=8)
    ax.set_title(f"[{r['flag']}] T={r['period_s']:.3f} s CI95 {r['period_ci95'][0]:.3f}-{r['period_ci95'][1]:.3f}  T_zc={r['period_zc_s']:.3f}  R2={r['r2']:.3f}  release t={r['release_t']:.2f}s", fontsize=9)
    idx = np.linspace(r['release_frame'], len(F) - 1, 6).astype(int); tiles = []
    for i in idx:
        im = F[i].clip(0, 255).astype(np.uint8).copy(); cv2.putText(im, f'f{i}', (8, 28), 0, 0.9, (0, 255, 255), 2); tiles.append(cv2.resize(im, None, fx=0.4, fy=0.4))
    ax2 = fig.add_subplot(1, 2, 2); g = np.concatenate([np.concatenate(tiles[:3], 1), np.concatenate(tiles[3:6], 1)], 0)
    ax2.imshow(g[:, :, ::-1]); ax2.axis('off'); fig.tight_layout(); fig.savefig(path, dpi=80); plt.close(fig)

if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('clip'); a.add_argument('--fps', type=float, required=True)
    a.add_argument('--dedup', action='store_true'); a.add_argument('--tol', type=float, default=3.0)
    a.add_argument('--nboot', type=int, default=200); a.add_argument('--qc')
    o = a.parse_args(); F = trk.load(o.clip); fps = o.fps
    if o.dedup:
        import measure_ball as mb; F, fac = mb.dedup(F); fps = o.fps * fac
    r = measure(F, fps, o.tol, o.nboot, keep_track=bool(o.qc))
    if o.qc: qc(F, r, o.qc)
    r.pop('track', None); print(json.dumps(r, indent=1))
