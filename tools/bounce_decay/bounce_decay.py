#!/usr/bin/env python3
"""bounce_decay.py: multi-bounce restitution and time-to-rest from a static-camera ball clip.

Track: two-pass, ghost-free background. Pass 1 uses a temporal median and a seeded
nearest-blob track. Pass 2 rebuilds the background as a per-pixel median over the
frames where the pass-1 ball (or its last known position while lost) does NOT cover
that pixel, then tracks again. Centroid = diff-weighted centroid of the blob.
Scale (optional) = 50%-contrast diameter (median over tracked frames).

Bounces: impacts = local maxima of image y (down) with prominence >= --min-rise px.
All flights are fitted JOINTLY as y = a t^2 + b_k t + c_k (shared curvature a,
i.e. constant g). The peak (contact) frame of each impact is excluded. Impact time k
= intersection of flights k and k+1, which is linear with a shared a:
t = (c_{k+1}-c_k)/(b_k-b_{k+1}).
Outputs:
  e_v[k]  = -v_after/v_before at impact k (needs scale-free y only)
  T[k]    = flight time between impacts k and k+1
  e_T[k]  = T[k+1]/T[k]  (scale-free AND depth-free: independent of px/m drift)
  e_h[k]  = sqrt(h[k+1]/h[k]), h = impact y - apex y (px; sensitive to depth drift)
  e_T_fit = exp(slope) of log T_k vs k (geometric decay), with SE
  g       = 2a * m_per_px (if a diameter or --mpp is given), and the release-from-rest
            g of the first fall (--rest-at-0: v0=0 at t=0, impact frame dropped)
  n_impacts, last_impact_s, still_bouncing_at_end (a flight with rise >= --min-rise
  starts in the last --tail-frac of the clip), rest_s (first time the ball stays
  within --rest-px of the floor until the clip end, or null)
Flight segments with < --min-pts interior points end the fitted sequence.
"""
import argparse, json, sys, hashlib
import numpy as np, cv2
from scipy.signal import find_peaks


def load(p):
    c = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = c.read()
        if not ok: break
        fr.append(f.astype(np.float32))
    fps = c.get(cv2.CAP_PROP_FPS)
    return np.array(fr), fps


def track(fr, bg, seed, thr, maxjump, rest_hint=None):
    n = len(fr); pts = np.full((n, 2), np.nan); diam = np.full(n, np.nan)
    prev = np.array(seed, float); lost = 0
    for i, f in enumerate(fr):
        d = np.abs(f - bg).max(2)
        m = (d > thr).astype(np.uint8)
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        k, lab, st, cen = cv2.connectedComponentsWithStats(m)
        if k < 2: lost += 1; continue
        dist = np.linalg.norm(cen[1:] - prev, axis=1)
        asp = np.minimum(st[1:, 2], st[1:, 3]) / np.maximum(st[1:, 2], st[1:, 3])
        ok = (st[1:, 4] >= 6) & (dist < maxjump * (1 + lost))
        if (ok & (asp >= 0.5)).any(): ok &= asp >= 0.5  # skip flat blobs (contact shadows)
        if not ok.any(): lost += 1; continue
        j = 1 + np.argmin(np.where(ok, dist, np.inf))
        x0, y0, w, h = st[j, :4]
        sub = d[y0:y0 + h, x0:x0 + w] * (lab[y0:y0 + h, x0:x0 + w] == j)
        ys, xs = np.mgrid[y0:y0 + h, x0:x0 + w]
        wsum = sub.sum()
        c = np.array([(sub * xs).sum() / wsum, (sub * ys).sum() / wsum])
        # 50%-contrast diameter: area above half the blob's 90th-pct contrast
        pk = np.percentile(sub[sub > 0], 90)
        half = (sub > 0.5 * pk).astype(np.uint8)
        cnts, _ = cv2.findContours(half, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        if cnts:
            filled = np.zeros_like(half); cv2.drawContours(filled, cnts, -1, 1, -1)
            diam[i] = np.sqrt(4 * filled.sum() / np.pi)
        pts[i] = c; prev = c; lost = 0
    return pts, diam


def ghost_free_bg(fr, pts, r):
    n, H, W, _ = fr.shape
    med = np.median(fr, 0); bg = med.copy()
    ok = ~np.isnan(pts[:, 0])
    if not ok.any(): return bg
    R = int(np.ceil(3 * r)) + 2
    x0 = max(0, int(np.nanmin(pts[:, 0])) - R); x1 = min(W, int(np.nanmax(pts[:, 0])) + R + 1)
    y0 = max(0, int(np.nanmin(pts[:, 1])) - R); y1 = min(H, int(np.nanmax(pts[:, 1])) + R + 1)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    keep = np.ones((n, y1 - y0, x1 - x0), bool); last = None
    for i in range(n):
        p = pts[i] if ok[i] else last
        if ok[i]: last = pts[i]
        if p is None: continue
        keep[i] = (xx - p[0]) ** 2 + (yy - p[1]) ** 2 > (2.0 * r) ** 2
    # masked median, per pixel; fall back to plain median where every frame is masked
    sub = fr[:, y0:y1, x0:x1]
    cnt = keep.sum(0)
    arr = np.where(keep[..., None], sub, np.nan)
    with np.errstate(all='ignore'):
        bgm = np.nanmedian(arr, 0)
    bg[y0:y1, x0:x1] = np.where((cnt > 0)[..., None], bgm, med[y0:y1, x0:x1])
    return bg


def auto_seed(fr, bg, thr):
    d = np.abs(fr[0] - bg).max(2)
    m = (d > thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    k, lab, st, cen = cv2.connectedComponentsWithStats(m)
    if k < 2:
        # ball may sit on its median position in frame 0: use frame-0 vs frame-mid difference
        d = np.abs(fr[0] - fr[len(fr) // 2]).max(2)
        m = (d > thr).astype(np.uint8); m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        k, lab, st, cen = cv2.connectedComponentsWithStats(m)
    # compact blobs (fill*aspect >= 0.45); a resting ball's median ghost also shows up in
    # frame 0, on the floor, so take the HIGHEST compact blob (ball starts above its rest
    # place in a drop clip) among those with >= 30% of the largest compact area.
    cand = []
    for j in range(1, k):
        a = st[j, 4]; w, h = st[j, 2], st[j, 3]
        if a < 6: continue
        fill = a / (w * h); asp = min(w, h) / max(w, h)
        if fill * asp >= 0.45: cand.append((a, cen[j]))
    if not cand: return cen[1 + int(np.argmax(st[1:, 4]))]
    amax = max(c[0] for c in cand)
    cand = [c for c in cand if c[0] >= 0.3 * amax]
    return min(cand, key=lambda c: c[1][1])[1]


def analyse(t, y, min_rise, min_pts, hold_px=1.0):
    ok = ~np.isnan(y)
    yi = np.interp(np.arange(len(y)), np.flatnonzero(ok), y[ok])
    pk, _ = find_peaks(yi, prominence=min_rise)
    pk = [p for p in pk if ok[p]]
    # segments: [start, pk0), (pk0, pk1), ... (pk_last, end]
    bounds = [-1] + list(pk) + [len(y)]
    segs = []
    for k in range(len(bounds) - 1):
        lo, hi = bounds[k] + 1, bounds[k + 1]
        idx = np.arange(lo, hi); idx = idx[ok[idx]]
        segs.append(idx)
    # trim a hold before release: drop leading frames of the first segment that stay
    # within hold_px of the start position (keep the last one: the release frame)
    if segs and len(segs[0]) > 0:
        s0 = segs[0]; y0 = np.median(y[s0[:3]])
        still = np.abs(y[s0] - y0) <= hold_px
        nlead = 0
        while nlead < len(s0) and still[nlead]: nlead += 1
        # also: walk back from the end of segment 0 while the ball is clearly falling
        m = len(s0) - 1
        while m > 0 and y[s0[m]] - y[s0[m - 1]] > 0.3: m -= 1
        cut = max(nlead - 1, m - 1, 0)
        if cut > 0: segs[0] = s0[cut:]
    # cut the falling branch of each segment where the ball stops descending (landing into
    # rest or contact plateau): after the apex, keep only strictly descending (y increasing) frames
    for k, idx in enumerate(segs):
        if len(idx) < 3: continue
        j = int(np.argmin(y[idx]))
        m = j + 1
        while m < len(idx) and y[idx[m]] - y[idx[m - 1]] > 0.3: m += 1
        segs[k] = idx[:m]
    # usable consecutive flights from the start: stop at first short one
    use = []
    for k, idx in enumerate(segs):
        if len(idx) < min_pts: break
        use.append(k)
    if len(use) < 2:
        return dict(n_peaks=len(pk), n_fitted=len(use), impacts=[], peaks=[int(p) for p in pk])

    def fit(K, drop=None):
        rows, rhs, sid = [], [], []
        t0 = [float(np.mean(t[segs[k]])) for k in range(K)]
        for k in range(K):
            for i in segs[k]:
                if drop is not None and i in drop: continue
                tau = t[i] - t0[k]
                r = np.zeros(1 + 2 * K); r[0] = tau ** 2; r[1 + 2 * k] = tau; r[2 + 2 * k] = 1
                rows.append(r); rhs.append(y[i]); sid.append((k, i))
        A_ = np.array(rows); b_ = np.array(rhs)
        sol_, *_ = np.linalg.lstsq(A_, b_, rcond=None)
        return sol_, A_, b_, sid, t0

    def robust(K):
        drop = set()
        for it in range(3):
            sol, A, bvec, sid, t0 = fit(K, drop)
            rr = bvec - A @ sol; sig = 1.4826 * np.median(np.abs(rr - np.median(rr)))
            bad = {sid[j][1] for j in range(len(rr)) if abs(rr[j]) > max(3 * sig, 1.0)}
            if not (bad - drop): break
            drop |= bad
        ok_ = all(sum(1 for i in segs[k] if i not in drop) >= min_pts for k in range(K))
        sol, A, bvec, sid, t0 = fit(K, drop)
        rr = bvec - A @ sol
        seg_rmse = [float(np.sqrt(np.mean([rr[j] ** 2 for j in range(len(rr)) if sid[j][0] == k] or [np.inf])))
                    for k in range(K)]
        return ok_, drop, seg_rmse

    # grow: start with the first 2 flights, add flight K+1 while every flight stays
    # consistent (segment rmse <= seg_tol px and >= min_pts inliers)
    K = 0; drop = set(); seg_tol = max(1.5, 0.0); diag = []
    for Kc in range(2, len(use) + 1):
        okc, dropc, srm = robust(Kc)
        diag.append(dict(K=Kc, ok=bool(okc), seg_rmse=[round(v, 3) for v in srm]))
        if not okc or max(srm) > seg_tol: break
        K, drop = Kc, dropc
    if K < 2:
        return dict(n_peaks=len(pk), n_fitted=K, impacts=[], peaks=[int(p) for p in pk], grow=diag)
    sol, A, bvec, sid, t0 = fit(K, drop)
    a = sol[0]; Bl = sol[1::2]; Cl = sol[2::2]
    t0 = np.array(t0)
    sol = np.concatenate([[a], np.ravel(np.column_stack([Bl - 2 * a * t0, a * t0 ** 2 - Bl * t0 + Cl]))])
    A = None
    a = sol[0]; B = sol[1::2]; C = sol[2::2]
    rmse = float(np.sqrt(np.mean((bvec - fit(K, drop)[1] @ fit(K, drop)[0]) ** 2)))
    imps = []
    for k in range(K - 1):
        ti = (C[k + 1] - C[k]) / (B[k] - B[k + 1])
        yimp = a * ti ** 2 + B[k] * ti + C[k]
        vb = 2 * a * ti + B[k]; va = 2 * a * ti + B[k + 1]
        imps.append(dict(t=float(ti), y=float(yimp), v_before=float(vb), v_after=float(va), e_v=float(-va / vb)))
    apex = [dict(t=float(-B[k] / (2 * a)), y=float(C[k] - B[k] ** 2 / (4 * a))) for k in range(K)]
    return dict(a_px=float(a), B=B.tolist(), C=C.tolist(), rmse_px=rmse, impacts=imps, apex=apex,
                n_peaks=len(pk), n_fitted=K, n_dropped=len(drop), grow=diag, peaks=[int(p) for p in pk], segs=[s.tolist() for s in segs])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip'); ap.add_argument('--fps', type=float, default=None)
    ap.add_argument('--diam', type=float, default=None, help='ball diameter in m (scale)')
    ap.add_argument('--mpp', type=float, default=None, help='metres per pixel (overrides --diam)')
    ap.add_argument('--seed', type=str, default=None, help='x,y of the ball in frame 0')
    ap.add_argument('--thr', type=float, default=30.0)
    ap.add_argument('--maxjump', type=float, default=60.0)
    ap.add_argument('--min-rise', type=float, default=3.0)
    ap.add_argument('--min-pts', type=int, default=3)
    ap.add_argument('--rest-at-0', action='store_true', help='ball released from rest at frame 0')
    ap.add_argument('--hold-px', type=float, default=1.0)
    ap.add_argument('--tail-frac', type=float, default=0.15)
    ap.add_argument('--rest-px', type=float, default=2.0)
    ap.add_argument('--out', default=None)
    A = ap.parse_args()
    fr, fps0 = load(A.clip); fps = A.fps or fps0; n = len(fr); t = np.arange(n) / fps
    bg0 = np.median(fr, 0)
    seed = np.array([float(v) for v in A.seed.split(',')]) if A.seed else auto_seed(fr, bg0, A.thr)
    p1, d1 = track(fr, bg0, seed, A.thr, A.maxjump)
    r = np.nanmedian(d1) / 2 if np.isfinite(np.nanmedian(d1)) else 10
    bg = ghost_free_bg(fr, p1, r)
    pts, diam = track(fr, bg, seed, A.thr, A.maxjump)
    y = pts[:, 1]
    an = analyse(t, y, A.min_rise, A.min_pts, A.hold_px)
    # scale: 50%-contrast diameter over the first descent (ball isolated, before the
    # first contact); fallback = all tracked frames
    fp = an['peaks'][0] if an['peaks'] else n
    dd = diam[:max(fp - 2, 1)]
    dpx = float(np.nanmedian(dd)) if np.isfinite(dd).any() else float(np.nanmedian(diam))
    mpp = A.mpp if A.mpp else (A.diam / dpx if A.diam else None)
    out = dict(clip=A.clip, fps=fps, n_frames=n, seed=[float(seed[0]), float(seed[1])], diam_px=dpx,
               mpp=mpp, n_tracked=int((~np.isnan(y)).sum()), tool='bounce_decay.py',
               tool_sha=hashlib.sha256(open(__file__, 'rb').read()).hexdigest()[:12])
    out.update({k: v for k, v in an.items() if k not in ('segs',)})
    imps = an['impacts']
    if imps:
        out['e_v'] = [i['e_v'] for i in imps]
        ti = np.array([i['t'] for i in imps])
        T = np.diff(ti); out['T'] = T.tolist()
        out['e_T'] = (T[1:] / T[:-1]).tolist() if len(T) > 1 else []
        if len(T) >= 3:
            k = np.arange(len(T)); X = np.stack([np.ones_like(k), k], 1).astype(float)
            cf, *_ = np.linalg.lstsq(X, np.log(T), rcond=None)
            rs = np.log(T) - X @ cf; s2 = rs @ rs / (len(T) - 2)
            se = np.sqrt(s2 / ((k - k.mean()) ** 2).sum())
            out['e_T_fit'] = float(np.exp(cf[1])); out['e_T_fit_se'] = float(np.exp(cf[1]) * se)
        elif len(T) == 2:
            out['e_T_fit'] = float(T[1] / T[0]); out['e_T_fit_se'] = None
        # heights of complete flights between impacts (apex k+1 belongs to flight after impact k)
        h = []
        for k in range(len(imps)):
            if k + 1 < len(an['apex']):
                ap_ = an['apex'][k + 1]
                if imps[k]['t'] < ap_['t'] and (k + 1 >= len(imps) or ap_['t'] < imps[k + 1]['t']):
                    h.append(imps[k]['y'] - ap_['y'])
        out['h_px'] = h
        out['e_h'] = [float(np.sqrt(max(h[k + 1], 0) / h[k])) for k in range(len(h) - 1) if h[k] > 0]
        out['n_impacts'] = len(imps); out['last_impact_s'] = float(ti[-1])
    else:
        out['n_impacts'] = 0
    # still bouncing / rest
    peaks = an['peaks']; tail0 = int(n * (1 - A.tail_frac))
    ok = ~np.isnan(y)
    out['still_bouncing_at_end'] = bool(any(p >= tail0 for p in peaks))
    floor = np.nanmax(y) if ok.any() else np.nan
    near = ok & (np.abs(y - floor) <= A.rest_px)
    rest = None
    for i in range(n - 1, -1, -1):
        if not near[i] and ok[i]: break
        rest = i
    out['rest_s'] = float(t[rest]) if (rest is not None and rest < n - 3) else None
    if mpp:
        out['g_joint'] = float(2 * an['a_px'] * mpp) if 'a_px' in an else None
    if A.rest_at_0:
        # first fall: v0=0 at t=0; frames 0..(first peak - 1)
        # descent run from frame 0: stop at the first frame that is not clearly lower
        # than the previous one (impact/contact); that frame is dropped
        e = 1
        while e < n and ok[e] and y[e] - y[e - 1] > 0.3 and (e < 2 or not ok[e - 2] or
                                                            y[e] - y[e - 1] >= 0.6 * (y[e - 1] - y[e - 2])): e += 1
        e = e - 1 if e < n and ok[min(e, n - 1)] else e
        idx = np.arange(0, e); idx = idx[ok[idx]]
        X = np.stack([np.ones(len(idx)), t[idx] ** 2], 1)
        cf, *_ = np.linalg.lstsq(X, y[idx], rcond=None)
        out['a_fall_px'] = float(2 * cf[1])
        if mpp: out['g_fall'] = float(2 * cf[1] * mpp)
    out['track_y'] = [None if np.isnan(v) else round(float(v), 2) for v in y]
    s = json.dumps(out, indent=1)
    if A.out: open(A.out, 'w').write(s)
    summ = {k: out.get(k) for k in ('n_impacts', 'e_v', 'e_T', 'e_T_fit', 'e_T_fit_se', 'e_h', 'g_fall', 'g_joint',
                                    'still_bouncing_at_end', 'rest_s', 'rmse_px', 'diam_px')}
    print(json.dumps(summ))


if __name__ == '__main__':
    main()
