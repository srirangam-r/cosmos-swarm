"""Single-clip ball-drop measurer (raj-3). g with free onset time, bootstrap CI, R^2; e from first rebound.
Usage:
  python3 -I measure_ball.py clip.mp4 --fps 24 --diam 0.06        # scale from ball minor side
  python3 -I measure_ball.py clip.mp4 --fps 24 --mpp 0.0027       # or metres per pixel directly
  python3 -I measure_ball.py --planted planted.json clip_dir      # planted run (writes est_v4.json)
Model up to first impact: y = y0 + 0.5 g (t-t0)^2 for t>t0, else y0 (v0=0 at release, release time free).
Static camera assumed (background from first/last frame; see trk.py)."""
import sys, json, argparse, numpy as np
from scipy.optimize import least_squares
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import trk

VERSION = 'measure_ball v4 (hinge t0 + bootstrap)'

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

def measure(F, fps, diam=None, mpp=None, nboot=300, seed=0):
    B = trk.blobs(F, mode='ball'); ok = [i for i, b in enumerate(B) if b]
    y = np.array([B[i][1] for i in ok]); t = np.array(ok) / fps
    d_px = float(np.median([B[i][4] for i in ok]))
    s = mpp if mpp else diam / d_px
    Y = y * s
    k = first_impact(Y, 0.006 if diam else 2 * s)
    n = max(k - 1, 5); tt, YY = t[:n], Y[:n]
    p = fit_hinge(tt, YY)
    res = YY - hinge(p, tt); r2 = 1 - (res ** 2).sum() / ((YY - YY.mean()) ** 2).sum()
    rng = np.random.default_rng(seed); gs = []
    for _ in range(nboot):
        Yb = hinge(p, tt) + rng.choice(res, len(res))
        gs.append(fit_hinge(tt, Yb)[1])
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
    return dict(g=float(p[1]), g_ci95=[float(np.percentile(gs, 2.5)), float(np.percentile(gs, 97.5))],
                g_sd=float(np.std(gs)), g_scale_sys_1px=float(p[1] / d_px) if diam else 0.0, r2=float(r2), t0=float(p[2]), n_fit=int(n), impact_frame=int(ok[k]),
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
            print(c['clip_id'], est[c['clip_id']], {k: r[k] for k in ('g_ci95', 'r2', 't0', 'g_poly_v3') if k in r})
        json.dump(est, open('est_v4.json', 'w')); sys.exit()
    a = argparse.ArgumentParser(); a.add_argument('clip'); a.add_argument('--fps', type=float, required=True)
    a.add_argument('--diam', type=float); a.add_argument('--mpp', type=float); a.add_argument('--nboot', type=int, default=300)
    o = a.parse_args(); assert o.diam or o.mpp, 'need --diam or --mpp'
    print(json.dumps(measure(trk.load(o.clip), o.fps, o.diam, o.mpp, o.nboot), indent=1))
