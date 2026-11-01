"""realball (raj-2): ball free-fall g for real or Cosmos clips with a held/slow release and/or duplicated frames.
Recipe validated on GAUGE real drops (work/raj-2/gauge_realcheck_v2): (1) drop periodic duplicate frames and re-time
distinct frames uniformly (25 fps content in a 30 fps container); (2) track the ball (trk_ballfall trk.blobs, mode='ball');
(3) find the release onset t0 with a v0=0 hinge fit; (4) g = free-v0 quadratic from `skip` frames after onset up to
the frame before first impact (slow gripper release makes v0=0 fits read low, raj-3 msg 141); residual bootstrap CI.
Scale: --mpp (preferred on real footage: blob size is biased there) or --diam (median minor side of the post-onset,
pre-impact blobs). e: first-rebound apex (as trk_ballfall).
Usage:
  python3 -I realball.py clip.mp4 --fps 24 --mpp 0.0018          # GAUGE first frames at 832x480: mpp ~ 1/554 vertical
  python3 -I realball.py clip.mp4 --fps 24 --diam 0.10
  python3 -I realball.py --planted planted.json clip_dir out.json  # referee planted run (period/a from trk_ballfall v3)
"""
import sys, json, argparse, numpy as np, cv2
sys.path.insert(0, __file__.rsplit('/', 1)[0] + '/../trk_ballfall')
import trk, measure_ball as mb
VERSION = 'realball v1 (dedup + hinge onset + free-v0 quad from onset+1)'

def dedup(F, rel=0.1):
    """Indices to keep. Drops exact repeats only if they recur with a fixed period (frame-rate conversion)."""
    g = [cv2.cvtColor(f.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32) for f in F]
    d = np.array([np.abs(g[i] - g[i - 1]).mean() for i in range(1, len(g))])
    med = np.median(d)
    if med <= 0: return list(range(len(F))), 0
    dup = np.where(d < rel * med)[0] + 1
    if len(dup) < 4: return list(range(len(F))), 0
    gaps = np.diff(dup); P = int(np.bincount(gaps).argmax())
    periodic = P >= 3 and np.mean(gaps % P == 0) >= 0.9 and len(dup) >= 0.7 * len(F) / P
    if not periodic: return list(range(len(F))), 0
    s = set(dup.tolist()); return [i for i in range(len(F)) if i not in s], P

def measure(F, fps, mpp=None, diam=None, skip=1, nboot=200, seed=0, no_dedup=False):
    keep, P = (list(range(len(F))), 0) if no_dedup else dedup(F)
    fps_true = fps * len(keep) / len(F)
    B = trk.blobs(F[keep], mode='ball'); ok = np.array([i for i, b in enumerate(B) if b])
    t = ok / fps_true; y = np.array([B[i][1] for i in ok]); minor = np.array([B[i][4] for i in ok])
    s0 = mpp if mpp else diam / np.median(minor)                     # provisional scale for impact detection / fit units
    Y = y * s0
    k = mb.first_impact(Y, 0.006 if diam else 2 * s0)
    n = max(k - 1, 5); p = mb.fit_hinge(t[:n], Y[:n]); t0 = p[2]
    j0 = int(np.searchsorted(t, t0)) + skip
    if n - j0 < 4: j0 = max(n - 4, 0)
    if not mpp:                                                     # free-ball scale: post-onset, pre-impact blobs
        s = diam / np.median(minor[j0:n]); Y = y * s
    else: s = s0
    tt, YY = t[j0:n], Y[j0:n]
    c = np.polyfit(tt, YY, 2); res = YY - np.polyval(c, tt)
    r2 = 1 - (res ** 2).sum() / max(((YY - YY.mean()) ** 2).sum(), 1e-12)
    rng = np.random.default_rng(seed)
    gs = [2 * np.polyfit(tt, np.polyval(c, tt) + rng.choice(res, len(res)), 2)[0] for _ in range(nboot)]
    e = None                                                        # first-rebound e (trk_ballfall v3 method)
    if k < len(Y) - 6:
        j = k + 1
        while j < len(Y) - 1 and Y[j + 1] < Y[j] + 0.003: j += 1
        tr, yr = t[k:j + 1], Y[k:j + 1]
        if len(tr) >= 4:
            cr = np.polyfit(tr, yr, 2)
            if cr[0] > 0:
                h0 = Y[k] - p[0] * (s / s0); hr = Y[k] - np.polyval(cr, -cr[1] / (2 * cr[0]))
                if h0 > 0 and hr > 0: e = float(np.sqrt(hr / h0))
    return dict(g=float(2 * c[0]), g_ci95=[float(np.percentile(gs, 2.5)), float(np.percentile(gs, 97.5))], g_sd=float(np.std(gs)),
                r2=float(r2), rms_m=float(res.std()), t0=float(t0), fit_frames=[int(ok[j0]), int(ok[n - 1])], n_fit=int(n - j0),
                impact_frame=int(ok[k]), g_hinge_v0=float(p[1]) * (s / s0), e=e, m_per_px=float(s), dup_period=P,
                fps_true=float(fps_true), method=VERSION)

if __name__ == '__main__':
    if sys.argv[1] == '--planted':
        d = json.load(open(sys.argv[2])); est = {}
        for c in d['clips']:
            F = trk.load(f"{sys.argv[3]}/{c['clip_id']}.mp4"); p = c['params']
            if 'period_s' in p: r = trk.pend(F, c['fps'])
            elif 'a' in p: r = trk.incline(F, c['fps'])
            else: r = measure(F, c['fps'], diam=0.10, nboot=50)
            est[c['clip_id']] = {k: v for k, v in r.items() if k in p and v is not None}
            print(c['clip_id'], est[c['clip_id']], {k: r[k] for k in ('t0', 'n_fit', 'g_hinge_v0', 'dup_period', 'r2') if k in r}, flush=True)
        json.dump(est, open(sys.argv[4], 'w'), indent=1); sys.exit()
    a = argparse.ArgumentParser(); a.add_argument('clip'); a.add_argument('--fps', type=float, required=True)
    a.add_argument('--diam', type=float); a.add_argument('--mpp', type=float); a.add_argument('--skip', type=int, default=1)
    a.add_argument('--nboot', type=int, default=200); a.add_argument('--no-dedup', action='store_true')
    o = a.parse_args(); assert o.diam or o.mpp, 'need --diam or --mpp'
    print(json.dumps(measure(trk.load(o.clip), o.fps, o.mpp, o.diam, o.skip, o.nboot, no_dedup=o.no_dedup), indent=1))
