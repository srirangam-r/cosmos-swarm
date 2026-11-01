"""pend_acf (ro-3): tracker-free pendulum period from image self-similarity.

Idea: a pendulum's frame at t and at t+P look the same (same bob/rod position, same direction of motion is not needed
since the pose repeats); at t+P/2 the bob is on the other side. So the mean frame difference
    D(lag) = mean_t mean_px |I_t - I_{t+lag}|   (grayscale, blurred, downsampled, motion pixels only)
has its first deep minimum at lag = P. No bob detection, no pivot, no scale: robust to occlusion by the post, to the bob
leaving the plane and to big non-sinusoidal swings, which break centroid trackers on Nano clips.

Pipeline: frames -> drop the first --skip frames (Nano reframes / outpaints in ~0-11) -> optional release detection
(motion energy onset; for real clips that start with a hold) -> 1/8-scale gray + blur -> mask = pixels whose temporal
std is in the top 10% (the moving rod/bob) -> D(lag) for lag in [lag_min, n/1.3] -> first local minimum whose depth is
>= 35% of the D range and which is lower than D(lag/2) (rejects the half-period, which can also dip on symmetric swings)
-> parabolic sub-frame refinement.
Uncertainty: the period is re-estimated on sliding half-length windows (each must hold >= 1.3 periods);
CI = 2.5-97.5 percentile of those plus +-0.5 frame / sqrt(k) quantisation, k = number of periods spanned.
Also reports P from the 2nd minimum (2P/2) as a consistency check; flag 'ok' if |P2/2 - P| < 5% (when 2P fits) and
the window spread < 10%, else 'check'.

Usage: python -I pend_acf.py clip.mp4 --fps 24 [--skip 12] [--release] [--qc out.png]  -> JSON on stdout
"""
import sys, json, argparse, numpy as np, cv2


def load(p, skip=0):
    c = cv2.VideoCapture(p); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    return F[skip:]


def prep(F, scale=8):
    G = []
    for f in F:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        g = cv2.resize(g, (g.shape[1] // scale, g.shape[0] // scale), interpolation=cv2.INTER_AREA)
        G.append(cv2.GaussianBlur(g, (3, 3), 0))
    return np.array(G)


def release_idx(G, frac=0.15):
    """first frame where frame-to-frame motion energy exceeds frac of its 90th percentile for 4 frames in a row"""
    e = np.abs(np.diff(G, axis=0)).mean(axis=(1, 2)); thr = frac * np.percentile(e, 90)
    m = e > thr
    for k in range(len(m) - 3):
        if m[k:k + 4].all(): return k
    return 0


def dcurve(G, lags, mask):
    X = G[:, mask]
    return np.array([np.abs(X[:-L] - X[L:]).mean() for L in lags])


def first_min(lags, D, depth=0.35):
    rng = D.max() - D.min()
    if rng <= 0: return None
    for i in range(1, len(D) - 1):
        if D[i] <= D[i - 1] and D[i] <= D[i + 1]:
            # prominence: rise on the left side since the previous max
            left_max = D[:i].max()
            j = i + 1
            while j < len(D) and D[j] >= D[j - 1]: j += 1
            right_max = D[i:j].max() if j > i + 1 else D[i]
            prom = min(left_max, right_max if j < len(D) else left_max) - D[i]
            if prom < depth * rng: continue
            L = lags[i]
            # reject half-period dips: D at L/2 must not be lower than D at L
            h = np.argmin(np.abs(lags - L / 2))
            if lags[h] >= lags[0] + 1 and D[h] < D[i]: continue
            # parabolic refinement
            a, b, c = D[i - 1], D[i], D[i + 1]; den = a - 2 * b + c
            off = 0.5 * (a - c) / den if den > 0 else 0.0
            return float(L + np.clip(off, -0.5, 0.5)), float(prom / rng)
    return None


def estimate(G, lag_min=4):
    n = len(G); sd = G.std(axis=0); mask = sd >= np.percentile(sd, 90)
    lags = np.arange(1, int(n / 1.3) + 1)
    D = dcurve(G, lags, mask)
    m = first_min(lags[lag_min - 1:], D[lag_min - 1:])
    return m, lags, D, mask


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('clip'); ap.add_argument('--fps', type=float, required=True)
    ap.add_argument('--skip', type=int, default=0); ap.add_argument('--release', action='store_true')
    ap.add_argument('--max-s', type=float, default=None, help='use at most this many seconds after start')
    ap.add_argument('--qc', default=None); a = ap.parse_args()
    F = load(a.clip, a.skip); G = prep(F); r0 = release_idx(G) if a.release else 0
    G = G[r0:]
    if a.max_s: G = G[: int(round(a.max_s * a.fps)) + 1]
    m, lags, D, mask = estimate(G)
    out = dict(clip=a.clip, fps=a.fps, skip=a.skip, release_frame=int(r0 + a.skip), n_used=len(G))
    if m is None:
        out.update(period_frames=None, period_s=None, flag='fail'); print(json.dumps(out)); return
    P, prom = m
    # 2P consistency: second minimum near 2P
    P2 = None
    if 2.3 * P < lags[-1]:
        sel = (lags > 1.6 * P) & (lags < 2.4 * P)
        if sel.sum() >= 3:
            k = np.argmin(np.where(sel, D, np.inf)); P2 = float(lags[k]) / 2
    # windowed estimates
    W = max(int(np.ceil(1.3 * P * 1.3)) + 2, len(G) // 2); ests = []
    for s in range(0, len(G) - W + 1, max(1, (len(G) - W) // 8 or 1)):
        mm = estimate(G[s:s + W])[0]
        if mm: ests.append(mm[0])
    k_per = len(G) / P
    q = 0.5 / np.sqrt(max(k_per, 1))
    lo, hi = (np.percentile(ests, [2.5, 97.5]) if len(ests) >= 3 else (P, P))
    lo, hi = min(lo, P) - q, max(hi, P) + q
    spread = (np.std(ests) / P) if len(ests) >= 3 else float('nan')
    ok = (P2 is None or abs(P2 - P) / P < 0.05) and (np.isfinite(spread) and spread < 0.10)
    out.update(period_frames=P, period_s=P / a.fps, ci95_frames=[float(lo), float(hi)], ci95_s=[float(lo / a.fps), float(hi / a.fps)],
               prominence=prom, P_from_2nd_min_frames=P2, window_ests_frames=[float(e) for e in ests], window_spread=float(spread),
               cycles_in_clip=float(k_per), flag='ok' if ok else 'check')
    if a.qc:
        import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 2, figsize=(12, 3.5))
        ax[0].plot(lags, D, '.-'); ax[0].axvline(P, c='r'); ax[0].set_xlabel('lag (frames)'); ax[0].set_ylabel('mean |I_t - I_t+lag|')
        ax[0].set_title(f"[{out['flag']}] P={P:.1f} f = {P / a.fps:.3f} s  2nd-min/2={P2}  spread={spread:.3f}", fontsize=9)
        ax[1].imshow(mask, cmap='gray'); ax[1].set_title('motion mask'); fig.tight_layout(); fig.savefig(a.qc, dpi=80)
    print(json.dumps(out))


if __name__ == '__main__':
    main()
