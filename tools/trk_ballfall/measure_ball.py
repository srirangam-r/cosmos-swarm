"""Single-clip ball-drop measurer (raj-3). g with free onset time, bootstrap CI, R^2; e from first rebound.
Usage:
  python3 -I measure_ball.py clip.mp4 --fps 24 --diam 0.06        # scale from ball minor side
  python3 -I measure_ball.py clip.mp4 --fps 24 --mpp 0.0027       # or metres per pixel directly
  python3 -I measure_ball.py --planted planted.json clip_dir      # planted run (writes est_v5.json)
  add --dedup for real footage with duplicated frames (e.g. GAUGE 25-in-30 fps); --ppm px/m instead of --mpp
v5 model up to first impact: hinge y0 + 0.5 g (t-t0)^2 [t>t0] locates release t0; g = free-v0 quadratic on frames >= t0 + 1 frame
(slow gripper releases leave the ball already moving at free-fall onset; v4's v0=0 hinge read GAUGE mocap 9.36 vs 9.82 for v5).
Also reports g_by_skip (0-3 frames after t0: stability), r2_lin and dAIC (quadratic vs constant velocity).
Static camera assumed (background from first/last frame; see trk.py)."""
import sys, json, argparse, numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import trk

VERSION = 'measure_ball v5 (hinge onset, free-v0 quadratic from onset+1 frame, bootstrap)'

def hinge(p, t): return p[0] + 0.5 * p[1] * np.clip(t - p[2], 0, None) ** 2

def fit_hinge(t, Y):
    best = None
    for t0 in np.linspace(t[0] - 0.2, t[max(len(t) - 4, 1)], 12):
        try:
            s = least_squares(lambda p: hinge(p, t) - Y, [Y[0], 2.0, t0],
                              bounds=([-np.inf, 0, t[0] - 1.0], [np.inf, 200, t[-1]]))
        except Exception: continue
        if best is None or s.cost < best.cost: best = s
    return best.x

def first_impact(Y, tol):
    k = int(np.argmax(Y >= Y.max() - tol))
    rev = np.where(Y[1:] < Y[:-1] - tol)[0]
    if len(rev): k = min(k, int(rev[0]))
    return k


def fit_onset(t, Y, fps, skip=1):
    """v5: hinge fit locates the release t0; then a free-v0 quadratic from the first frame >= t0 + skip/fps.
    Handles slow releases (ball already moving at free-fall onset). On GAUGE real mocap (n=22) skip=1 gives 9.815 +- 0.009."""
    p = fit_hinge(t, Y)
    s = int(np.searchsorted(t, p[2] + skip / fps - 1e-9)); s = max(0, min(s, len(t) - 5))
    c = np.polyfit(t[s:], Y[s:], 2)
    return c, s, p

def dedup(F, rel=0.1):
    """Drop exact-duplicate frames (e.g. 25 fps footage in a 30 fps container). Returns kept frames and the distinct-frame fps factor."""
    d = np.array([np.abs(F[k] - F[k - 1]).mean() for k in range(1, len(F))])
    keep = [0] + [k for k in range(1, len(F)) if d[k - 1] >= rel * np.median(d)]
    return F[keep], len(keep) / len(F)

def measure(F, fps, diam=None, mpp=None, nboot=300, seed=0, skip=1):
    B = trk.blobs(F, mode='ball'); ok = [i for i, b in enumerate(B) if b]
    y = np.array([B[i][1] for i in ok]); t = np.array(ok) / fps
    d_px = float(np.median([B[i][4] for i in ok]))
    s = mpp if mpp else diam / d_px
    Y = y * s
    k = first_impact(Y, 0.006 if diam else 2 * s)
    n = max(k - 1, 5); tt, YY = t[:n], Y[:n]
    c, s0, p = fit_onset(tt, YY, fps, skip)
    g = float(2 * c[0]); ts, Ys = tt[s0:], YY[s0:]; fit = np.polyval(c, ts); res = Ys - fit
    sst = ((Ys - Ys.mean()) ** 2).sum(); r2 = 1 - (res ** 2).sum() / sst
    rl = Ys - np.polyval(np.polyfit(ts, Ys, 1), ts); r2_lin = 1 - (rl ** 2).sum() / sst   # constant-velocity alternative
    m = len(ts); daic = m * np.log((rl ** 2).sum() / m) - m * np.log(max((res ** 2).sum(), 1e-30) / m) - 2  # >0 favours quadratic
    rng = np.random.default_rng(seed); gs = []
    for _ in range(nboot):
        gs.append(2 * np.polyfit(ts, fit + rng.choice(res, m), 2)[0])
    g_skip = {}
    for sk in range(4):
        cc, ss, _ = fit_onset(tt, YY, fps, sk); g_skip[sk] = float(2 * cc[0])
    poly = np.polyfit(tt, YY, 2)  # trk.py v3 estimator, for comparison
    e = None
    if k < len(Y) - 6:
        j = k + 1
        while j < len(Y) - 1 and Y[j + 1] < Y[j] + 0.003: j += 1
        tr, yr = t[k:j + 1], Y[k:j + 1]
        if len(tr) >= 4:
            c = np.polyfit(tr, yr, 2)
            if c[0] > 0:
                h0 = Y[k] - p[0]; hr = Y[k] - np.polyval(c, -c[1] / (2 * c[0]))
                if h0 > 0 and hr > 0: e = float(np.sqrt(hr / h0))
    return dict(g=g, g_hinge_v4=float(p[1]), g_by_skip=g_skip, r2_lin=float(r2_lin), dAIC_quad_vs_lin=float(daic), onset_frame=int(ok[s0]), g_ci95=[float(np.percentile(gs, 2.5)), float(np.percentile(gs, 97.5))],
                g_sd=float(np.std(gs)), g_scale_sys_1px=float(g / d_px) if diam else 0.0, r2=float(r2), t0=float(p[2]), n_fit=int(n), impact_frame=int(ok[k]),
                g_poly_v3=float(2 * poly[0]), e=e, d_px=d_px, m_per_px=float(s), fps=fps, method=VERSION)

if __name__ == '__main__':
    if sys.argv[1] == '--planted':
        d = json.load(open(sys.argv[2])); est = {}
        for c in d['clips']:
            F = trk.load(f"{sys.argv[3]}/{c['clip_id']}.mp4"); p = c['params']
            if 'period_s' in p: r = trk.pend(F, c['fps'])
            elif 'a' in p: r = trk.incline(F, c['fps'])
            else: r = measure(F, c['fps'], diam=0.10, nboot=50)
            est[c['clip_id']] = {k: v for k, v in r.items() if k in p and v is not None}
            print(c['clip_id'], est[c['clip_id']], {k: r[k] for k in ('g_ci95', 'r2', 't0', 'g_hinge_v4', 'g_by_skip') if k in r})
        json.dump(est, open('est_v5.json', 'w')); sys.exit()
    a = argparse.ArgumentParser(); a.add_argument('clip'); a.add_argument('--fps', type=float, required=True)
    a.add_argument('--diam', type=float); a.add_argument('--mpp', type=float); a.add_argument('--nboot', type=int, default=300)
    a.add_argument('--ppm', type=float); a.add_argument('--skip', type=int, default=1); a.add_argument('--dedup', action='store_true')
    o = a.parse_args(); mpp = o.mpp or (1 / o.ppm if o.ppm else None); assert o.diam or mpp, 'need --diam, --mpp or --ppm'
    F = trk.load(o.clip); fps = o.fps; nd = None
    if o.dedup: F, fac = dedup(F); fps = o.fps * fac; nd = len(F)
    r = measure(F, fps, o.diam, mpp, o.nboot, skip=o.skip); r['n_distinct'] = nd; r['clip'] = o.clip
    print(json.dumps(r, indent=1))
