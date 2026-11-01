"""Bounce-flight gravity (raj-3, v1). g from the curvature of the ballistic flights BETWEEN bounces, not from the first drop.
Why: on Cosmos clips the first drop is often unusable (the held ball is never released, the ball starts mid-air, or the first
fall lasts only ~4 frames). Each rebound flight is a clean parabola with free v0; its curvature is g regardless of release.
Track: trk.blobs (mode 'ball', i.e. bg from first/last frame; or 'diff', temporal-median bg). Impacts = local maxima of image y
(lowest points) where the ball turns from moving down to moving up by more than --tol px. Flight i = frames strictly between impact i
and impact i+1. A flight is used if it has >= 5 frames and rises by >= 6 px above its endpoints. Pooled fit: one shared curvature
with a free offset and slope per flight (linear least squares); g = 2 * curvature * m_per_px. Residual bootstrap CI.
Primary g = FIRST usable rebound flight (largest, best conditioned); g_pooled = all flights (later short flights read ~15% low on real
GAUGE drops, so it is reported only). flag = ok (first-flight R^2 > 0.98 and >= 6 frames) | weak | no_bounce.
Usage: python3 -I measure_bounce.py clip.mp4 --fps 24 --ppm 539.8 [--tracker ball|diff] [--qc qc.png]
       python3 -I measure_bounce.py clip.mp4 --fps 24 --ppm 539.8 --track_json samball_track.json [--start N]   (external track, e.g. SAM)
       python3 -I measure_bounce.py --planted planted.json clip_dir     (planted run, diam 0.10 m scale like v5)"""
import sys, json, argparse, numpy as np
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import trk

VERSION = 'measure_bounce v1 (curvature of the first rebound flight, residual bootstrap; pooled all-flight value as g_pooled)'


def impacts(y, tol):
    """Indices k with y[k] a local max (lowest point) and the ball moving up by > tol within 2 frames after it."""
    out = []
    for k in range(1, len(y) - 2):
        if y[k] >= y[k - 1] and y[k] >= y[k + 1] and y[k] - min(y[k + 1], y[k + 2]) > tol and y[k] - y[max(k - 2, 0)] > tol:
            if out and k - out[-1] < 3:
                if y[k] > y[out[-1]]: out[-1] = k
                continue
            out.append(k)
    return out


def flights(t, y, tol, min_n=5, min_rise=6.0):
    K = impacts(y, tol); seg = []
    for a, b in zip(K[:-1], K[1:]):
        idx = np.arange(a + 1, b)
        if len(idx) >= min_n and min(y[a], y[b]) - y[idx].min() >= min_rise: seg.append(idx)
    return K, seg


def pooled(t, y, seg):
    rows, Y = [], []
    for i, idx in enumerate(seg):
        for j in idx:
            r = np.zeros(1 + 2 * len(seg)); r[0] = t[j] ** 2; r[1 + 2 * i] = 1; r[2 + 2 * i] = t[j]; rows.append(r); Y.append(y[j])
    A, Y = np.array(rows), np.array(Y); c, *_ = np.linalg.lstsq(A, Y, rcond=None)
    return c, A, Y


def measure(F, fps, diam=None, mpp=None, tracker='ball', tol=2.0, nboot=300, seed=0):
    B = trk.blobs(F, mode=tracker); ok = [i for i, b in enumerate(B) if b]
    fr = np.array(ok); y = np.array([B[i][1] for i in ok]); d_px = float(np.median([B[i][4] for i in ok]))
    s = mpp if mpp else diam / d_px
    return fit_track(fr, y, fps, s, d_px=d_px, tracker=tracker, tol=tol, nboot=nboot, seed=seed,
                     track=[[int(i), float(B[i][0]), float(B[i][1])] for i in ok])


def fit_track(fr, y, fps, s, d_px=None, tracker='external', tol=2.0, nboot=300, seed=0, track=None):
    """Bounce-flight g from any per-frame track: fr = frame indices, y = image y (px, down), s = m per px."""
    fr = np.asarray(fr); y = np.asarray(y, float); t = fr / fps
    K, seg = flights(t, y, tol)
    base = dict(method=VERSION, tracker=tracker, fps=fps, m_per_px=float(s), d_px=d_px, impact_frames=[int(fr[k]) for k in K],
                track=track if track is not None else [[int(i), float('nan'), float(v)] for i, v in zip(fr, y)])
    if not seg: return dict(base, g=None, flag='no_bounce', n_flights=0)
    cp, _, _ = pooled(t, y, seg); g_pooled = float(2 * cp[0] * s); allseg = seg
    seg = seg[:1]   # v1 primary: first rebound flight only (later, shorter flights read ~15% low on real GAUGE drops)
    c, A, Y = pooled(t, y, seg); fit = A @ c; res = Y - fit
    # R^2 against per-flight means (how much of the within-flight motion the parabolas explain)
    sst = sum(((y[idx] - y[idx].mean()) ** 2).sum() for idx in seg); r2 = 1 - (res ** 2).sum() / sst
    rng = np.random.default_rng(seed); gs = [2 * np.linalg.lstsq(A, fit + rng.choice(res, len(res)), rcond=None)[0][0] * s for _ in range(nboot)]
    per = [float(2 * np.polyfit(t[idx], y[idx], 2)[0] * s) for idx in allseg]
    n = int(sum(len(i) for i in seg)); g = float(2 * c[0] * s)
    flag = 'ok' if (r2 > 0.98 and n >= 6) else 'weak'
    return dict(base, g=g, g_ci95=[float(np.percentile(gs, 2.5)), float(np.percentile(gs, 97.5))], g_sd=float(np.std(gs)), r2=float(r2),
                n_flights=len(allseg), n_frames=n, g_pooled=g_pooled, g_per_flight=per, flight_frames=[[int(fr[i[0]]), int(fr[i[-1]])] for i in allseg],
                flight_rise_px=[float(min(y[i[0] - 1], y[i[-1] + 1]) - y[i].min()) for i in allseg], flag=flag)


def qc(r, path):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    tr = np.array(r['track']); fps = r['fps']
    plt.figure(figsize=(9, 5)); plt.plot(tr[:, 0] / fps, tr[:, 2], '.', ms=4, color='0.4', label='track y')
    for k in r['impact_frames']: plt.axvline(k / fps, color='r', lw=0.6)
    for a, b in r.get('flight_frames', []):
        m = (tr[:, 0] >= a) & (tr[:, 0] <= b); plt.plot(tr[m, 0] / fps, tr[m, 2], 'o', ms=4)
    plt.gca().invert_yaxis(); plt.xlabel('t (s)'); plt.ylabel('y (px, down)')
    g = r['g']; plt.title(f"[{r['flag']}] bounce-flight g={g if g is None else round(g, 3)} m/s2 flights={r['n_flights']} " +
                          (f"CI95 {r['g_ci95'][0]:.2f}-{r['g_ci95'][1]:.2f} R2={r['r2']:.3f}" if g is not None else ''), fontsize=9)
    plt.savefig(path, dpi=80, bbox_inches='tight'); plt.close()


if __name__ == '__main__':
    if sys.argv[1] == '--planted':
        d = json.load(open(sys.argv[2])); est = {}
        for c in d['clips']:
            if 'g' not in c['params']: continue
            r = measure(trk.load(f"{sys.argv[3]}/{c['clip_id']}.mp4"), c['fps'], diam=0.10, nboot=50)
            print(c['clip_id'], r['flag'], r['g'], r.get('n_flights'), r.get('g_per_flight'), r.get('r2'))
            if r['g'] is not None: est[c['clip_id']] = {'g': r['g']}
        json.dump(est, open('est_bounce_v1.json', 'w')); sys.exit()
    a = argparse.ArgumentParser(); a.add_argument('clip'); a.add_argument('--fps', type=float, required=True)
    a.add_argument('--ppm', type=float); a.add_argument('--mpp', type=float); a.add_argument('--diam', type=float)
    a.add_argument('--tracker', default='ball'); a.add_argument('--tol', type=float, default=2.0); a.add_argument('--qc')
    a.add_argument('--track_json', help="use an external track instead of trk.blobs: JSON with 'cy' (one value per frame, null/NaN = missing), e.g. tools/samball --track_out")
    a.add_argument('--start', type=int, default=0, help='ignore track frames before this index (e.g. before a spawned ball appears)')
    o = a.parse_args(); mpp = o.mpp or (1 / o.ppm if o.ppm else None)
    if o.track_json:
        cy = np.array([np.nan if v is None else v for v in json.load(open(o.track_json))['cy']], float)
        fr = np.where(np.isfinite(cy) & (np.arange(len(cy)) >= o.start))[0]
        r = fit_track(fr, cy[fr], o.fps, mpp, tracker='external:' + o.track_json.rsplit('/', 1)[-1], tol=o.tol)
    else:
        r = measure(trk.load(o.clip), o.fps, diam=o.diam, mpp=mpp, tracker=o.tracker, tol=o.tol)
    if o.qc: qc(r, o.qc)
    print(json.dumps({k: v for k, v in r.items() if k != 'track'}))
