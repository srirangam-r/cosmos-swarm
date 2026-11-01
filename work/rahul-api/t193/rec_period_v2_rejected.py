"""rec_period v2 (rahul-api): tracker-free pendulum period from frame self-similarity recurrence.

Independent of tools/trk_ballfall/measure_pend.py: no bob detection, no tracking, no sinusoid fit.
  1. Grayscale, downsample x2, light blur.
  2. Motion mask = pixels whose temporal std > max(0.25 * p99.9(std), 4 gray levels), dilated.
  3. D(tau) = mean_i mean_mask (F_i - F_{i+tau})^2 for every lag tau with >= MIN_OVERLAP pairs.
  4. Period = lag of the FIRST local minimum of D in [TMIN, TMAX] s whose depth >= DEPTH_MIN (else the deepest
     minimum, flagged), parabolic sub-frame refinement. (v1 rule revised from 'global minimum' after the planted
     runs and before any task-193 Nano clip was fetched: global min can pick 2T when damping is low.)
  5. Uncertainty: moving-block bootstrap over the start index i (block 6 frames, 300 draws).
Readability rule (fixed before any Nano clip of task 193 came back):
  depth = 1 - D(tau*) / max_{tau < tau*} D(tau) >= 0.40, and tau* is not at the last searchable lag.
v2 changes (made on planted + real GAUGE only, before any task-193 Nano clip was fetched): mask 0.5*p99.9, D box-smoothed over 5 lags.
Usage: python -I rec_period.py clip.mp4 [--fps F] [--start K] [--n N] [--dedup]
"""
import sys, json, argparse
import numpy as np
import cv2

TMIN, TMAX, MIN_OVERLAP, DEPTH_MIN = 0.6, 3.2, 15, 0.40
MASK_FRAC, SMOOTH = 0.5, 5  # v2: mask thr = 0.5*p99.9(std); D smoothed by a 5-lag box filter


def load(path, dedup=False, max_frames=100000):
    c = cv2.VideoCapture(path)
    fps = c.get(cv2.CAP_PROP_FPS)
    G = []
    while len(G) < max_frames:
        ok, f = c.read()
        if not ok:
            break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        G.append(g)
    G = np.array(G)
    if dedup:  # drop exact/near-exact repeated frames (GAUGE 25 fps content in 30 fps container)
        d = np.abs(np.diff(G, axis=0)).mean(axis=(1, 2))
        keep = np.r_[True, d > 0.05 * np.median(d)]
        fps = fps * keep.mean()
        G = G[keep]
    return G, fps


def prep(G):
    out = []
    for g in G:
        g = cv2.resize(g, (g.shape[1] // 2, g.shape[0] // 2), interpolation=cv2.INTER_AREA)
        out.append(cv2.GaussianBlur(g, (0, 0), 1.0))
    return np.array(out)


def motion_mask(P):
    sd = P.std(0)
    thr = max(MASK_FRAC * np.percentile(sd, 99.9), 4.0)
    m = (sd > thr).astype(np.uint8)
    m = cv2.dilate(m, np.ones((5, 5), np.uint8))
    return m.astype(bool), float(thr)


def dcurve(X, idx_sets=None):
    N = len(X)
    taus = np.arange(1, N - MIN_OVERLAP + 1)
    D = np.empty(len(taus))
    for k, t in enumerate(taus):
        d = ((X[:-t] - X[t:]) ** 2).mean(1)  # per start frame i, length N - t
        if idx_sets is None:
            D[k] = d.mean()
        else:
            ii = idx_sets[idx_sets < len(d)]
            D[k] = d[ii].mean() if len(ii) else d.mean()
    return taus, D


def pick(taus, D, fps):
    if SMOOTH > 1:
        D = np.convolve(np.pad(D, SMOOTH // 2, mode='edge'), np.ones(SMOOTH) / SMOOTH, mode='valid')
    lo, hi = TMIN * fps, TMAX * fps
    sel = np.where((taus >= lo) & (taus <= hi))[0]
    if len(sel) < 3:
        return None
    def depth_at(k):
        peak = D[:k].max() if k > 0 else D[k]
        return 1.0 - D[k] / peak if peak > 0 else 0.0
    # first local minimum inside the window that is a deep dip (avoids locking onto 2T when damping is low)
    k = None
    for j in sel:
        if 0 < j < len(D) - 1 and D[j] < D[j - 1] and D[j] <= D[j + 1] and depth_at(j) >= DEPTH_MIN:
            k = j
            break
    if k is None:
        k = sel[np.argmin(D[sel])]
    at_edge = (k == sel[-1]) or (k == len(taus) - 1)
    depth = depth_at(k)
    t = float(taus[k])
    if 0 < k < len(taus) - 1:
        y0, y1, y2 = D[k - 1], D[k], D[k + 1]
        den = y0 - 2 * y1 + y2
        if den > 0:
            t += 0.5 * (y0 - y2) / den
    return dict(tau_frames=t, period_s=t / fps, depth=float(depth), at_edge=bool(at_edge), k=int(k))


def measure(G, fps, nboot=300, seed=0):
    P = prep(G)
    m, thr = motion_mask(P)
    X = P[:, m]
    X = X - X.mean(1, keepdims=True)  # remove global brightness flicker per frame
    taus, D = dcurve(X)
    r = pick(taus, D, fps)
    if r is None:
        return dict(flag='too_short', fps=fps, n=len(G))
    rng = np.random.default_rng(seed)
    N = len(X)
    B = 6
    Ts = []
    for _ in range(nboot):
        starts = rng.integers(0, N - B + 1, size=int(np.ceil(N / B)))
        idx = np.concatenate([np.arange(s, s + B) for s in starts])
        _, Db = dcurve(X, idx)
        rb = pick(taus, Db, fps)
        if rb is not None:
            Ts.append(rb['period_s'])
    Ts = np.array(Ts)
    readable = (r['depth'] >= DEPTH_MIN) and not r['at_edge']
    return dict(method='rec_period v2', period_s=r['period_s'], depth=r['depth'], at_edge=r['at_edge'],
                boot_se=float(Ts.std()) if len(Ts) else None,
                boot_ci68=[float(np.percentile(Ts, 16)), float(np.percentile(Ts, 84))] if len(Ts) else None,
                flag='ok' if readable else ('edge' if r['at_edge'] else 'shallow'),
                fps=float(fps), n=int(N), mask_frac=float(m.mean()), mask_thr=thr,
                D=[float(x) for x in D], taus=[int(t) for t in taus])


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--fps', type=float, default=None)
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--n', type=int, default=None)
    ap.add_argument('--dedup', action='store_true')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    G, fps = load(a.clip, dedup=a.dedup)
    if a.fps:
        fps = a.fps
    G = G[a.start: (a.start + a.n) if a.n else None]
    r = measure(G, fps)
    r['clip'] = a.clip; r['start'] = a.start
    print(json.dumps({k: v for k, v in r.items() if k not in ('D', 'taus')}))
    if a.out:
        json.dump(r, open(a.out, 'w'))
