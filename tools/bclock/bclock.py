#!/usr/bin/env python3
"""bclock v1 (ro-1): bounce clock. Impact times, flight durations, and timing-based restitution/g for a bouncing ball.

Idea: impact *timing* is scale-free and robust to perspective, so frames-per-bounce and the flight-time ratio
(e = T_{k+1}/T_k under constant g; e_1 = T_1 / (2 t_fall) for a drop from rest) can be read even when the metric
scale is uncertain (Cosmos clips). g is reported two ways: parabola curvature per flight (2a/ppm) and the timing
form g = 8 h / T^2 (h = apex height above the impact level).

Track: NCC template match of a ball patch seeded at --point on --pframe (default: auto, largest frame-0 vs
temporal-median blob), local search window, sub-pixel parabolic peak; the template is refreshed from the last
confident match (score >= --refresh) so a ball that changes size/shading (Cosmos) keeps being tracked.
Impacts: local maxima of image-y (down) with prominence >= --prom px, then refined to sub-frame as the time the
two neighbouring flight parabolas hit the common impact level.

usage: python3 -I bclock.py clip.mp4 --fps 24 [--ppm P | --diam 0.10] [--point x,y] [--pframe N] [--tmax N] [--qc qc.png] [--json out.json]
       python3 -I bclock.py --planted planted.json clipdir --out est.json
"""
import argparse, json, sys, os
import numpy as np
import cv2


def read_frames(path, tmax=None):
    cap = cv2.VideoCapture(path); F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(f)
        if tmax and len(F) >= tmax: break
    return F


def auto_seed(F, need_seed=True):
    # colour distance to the temporal-median background (a ball can match the background in grey level)
    g = np.stack([f.astype(np.float32) for f in F[:: max(1, len(F) // 30)]])
    med = np.median(g, 0)
    d = cv2.GaussianBlur(np.sqrt(((g[0] - med) ** 2).sum(-1)), (5, 5), 0)
    best = None
    if not need_seed: return None, None, med
    for thr in (max(12, 0.4 * d.max()), max(8, 0.25 * d.max())):
        m = (d > thr).astype(np.uint8)
        n, lab, st, cen = cv2.connectedComponentsWithStats(m)
        for j in range(1, n):
            A = st[j, cv2.CC_STAT_AREA]; w = st[j, cv2.CC_STAT_WIDTH]; h = st[j, cv2.CC_STAT_HEIGHT]
            if A < 15 or A > 20000: continue
            fill = A / (w * h); aspect = min(w, h) / max(w, h)
            if aspect < 0.6 or fill < 0.5: continue  # ball-like: roughly round and filled
            sc = float(d[lab == j].mean()) * np.sqrt(A)
            if best is None or sc > best[0]: best = (sc, j, cen[j])
        if best: break
    if best is None: raise SystemExit('auto seed failed; pass --point')
    cen = {best[1]: best[2]}; k = best[1]
    return float(cen[k][0]), float(cen[k][1]), med


def ball_radius(gray, med, x, y, rmax=60):
    """equivalent radius of the frame blob that differs from the median background around (x,y)."""
    x, y = int(round(x)), int(round(y))
    y0, y1, x0, x1 = max(0, y - rmax), y + rmax, max(0, x - rmax), x + rmax
    d = np.sqrt(((gray[y0:y1, x0:x1] - med[y0:y1, x0:x1]) ** 2).sum(-1))
    m = (d > 0.5 * np.percentile(d, 99.5)).astype(np.uint8)
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    if n < 2: return None
    # component containing / nearest to the seed
    cx, cy = x - x0, y - y0
    k = lab[min(cy, lab.shape[0] - 1), min(cx, lab.shape[1] - 1)]
    if k == 0:
        k = 1 + np.argmin([np.hypot(*(cen[j] - [cx, cy])) for j in range(1, n)])
    return float(np.sqrt(st[k, cv2.CC_STAT_AREA] / np.pi))


def subpix(r, i, j):
    def p(a, b, c):
        den = a - 2 * b + c
        return 0.0 if abs(den) < 1e-9 else 0.5 * (a - c) / den
    dy = p(r[i - 1, j], r[i, j], r[i + 1, j]) if 0 < i < r.shape[0] - 1 else 0.0
    dx = p(r[i, j - 1], r[i, j], r[i, j + 1]) if 0 < j < r.shape[1] - 1 else 0.0
    return dx, dy


def track(F, x, y, pframe, half, search, refresh, pen=0.002, mode='gray', med=None):
    if mode == 'diff':  # colour distance to the temporal-median background: a static-camera foreground map
        G = [cv2.GaussianBlur(np.sqrt(((f.astype(np.float32) - med) ** 2).sum(-1)), (3, 3), 0) for f in F]
    else:
        G = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in F]
    H, W = G[0].shape
    def patch(g, x, y):
        xi, yi = int(round(x)), int(round(y))
        if xi - half < 0 or yi - half < 0 or xi + half + 1 > W or yi + half + 1 > H: return None
        return g[yi - half: yi + half + 1, xi - half: xi + half + 1].copy()
    tpl0 = patch(G[pframe], x, y)
    xs = np.full(len(G), np.nan); ys = np.full(len(G), np.nan); sc = np.zeros(len(G))
    xs[pframe], ys[pframe], sc[pframe] = x, y, 1.0
    for direction in (1, -1):
        tpl = tpl0.copy(); cx, cy = x, y; vx = vy = 0.0
        rng = range(pframe + 1, len(G)) if direction == 1 else range(pframe - 1, -1, -1)
        for t in rng:
            # vertical strip search: x within +-search of the last position, full height (bounces reverse vy).
            # candidate score = NCC - pen * distance to the nearer of two predictions (constant velocity, reflected vy).
            x0 = int(max(0, cx - search - half)); x1 = int(min(W, cx + search + half + 1))
            roi = G[t][:, x0:x1]
            if roi.shape[1] <= tpl.shape[1]: break
            r = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
            jj, ii = np.meshgrid(np.arange(r.shape[1]) + x0 + half, np.arange(r.shape[0]) + half)
            d1 = np.hypot(jj - (cx + vx), ii - (cy + vy)); d2 = np.hypot(jj - (cx + vx), ii - (cy - vy))
            obj = r - pen * np.minimum(d1, d2)
            i, j = np.unravel_index(np.argmax(obj), r.shape)
            dx, dy = subpix(r, i, j)
            nx, ny = x0 + j + dx + half, i + dy + half
            sc[t] = r[i, j]
            if r[i, j] < 0.3: continue  # lost this frame; keep prediction
            vx, vy = (nx - cx), (ny - cy)
            cx, cy = nx, ny; xs[t], ys[t] = nx, ny
            if r[i, j] >= refresh:
                p = patch(G[t], nx, ny)
                if p is not None: tpl = 0.7 * tpl + 0.3 * p
    return xs, ys, sc, G


def find_impacts(y, prom):
    """local maxima of y (image-down) with prominence >= prom; plateau-safe."""
    idx = []
    n = len(y)
    for t in range(1, n - 1):
        if np.isnan(y[t]): continue
        lo = max(0, t - 1); hi = min(n, t + 2)  # strict local max; prominence does the rest (short flights at low fps)
        w = y[lo:hi]
        if np.nanmax(w) > y[t] or (t > 0 and y[t - 1] == y[t]): continue
        # prominence: rise on both sides
        left = y[:t][~np.isnan(y[:t])]; right = y[t + 1:][~np.isnan(y[t + 1:])]
        if len(left) == 0 or len(right) == 0: continue
        # min height between this max and the previous / next higher max
        # prominence against the higher of the neighbouring impacts' interval minima: search until a higher max
        L = t - 1
        while L > 0 and not (y[L] > y[t]): L -= 1
        R = t + 1
        while R < n - 1 and not (y[R] > y[t]): R += 1
        lmin = np.nanmin(y[L:t]); rmin = np.nanmin(y[t + 1:R + 1])
        if y[t] - lmin >= prom and y[t] - rmin >= prom:
            idx.append(t)
    return idx


def fit_flight(t, y, a, b, guard):
    m = (t >= a + guard) & (t <= b - guard) & ~np.isnan(y)
    if m.sum() < 3: return None
    c = np.polyfit(t[m], y[m], 2)
    res = y[m] - np.polyval(c, t[m])
    ss = np.sum((y[m] - y[m].mean()) ** 2)
    return dict(c=c.tolist(), n=int(m.sum()), r2=float(1 - np.sum(res ** 2) / ss) if ss > 0 else 0.0)


def roots_at(c, level):
    a, b, cc = c
    disc = b * b - 4 * a * (cc - level)
    if a <= 0 or disc < 0: return None
    s = np.sqrt(disc)
    return ((-b - s) / (2 * a), (-b + s) / (2 * a))


def analyse(ys, fps, ppm, prom, guard, release_at_rest=True):
    n = len(ys); t = np.arange(n, dtype=float)
    imp = find_impacts(ys, prom)
    out = dict(impact_frames=imp)
    if not imp:
        # drop without an impact in view: one parabola over the whole track
        ymax = np.nanmax(ys); land = int(np.argmax(ys >= ymax - 1.5))  # first frame at the resting level
        m = ~np.isnan(ys) & (t < land)
        out['land_frame'] = land
        if m.sum() < 3: out['flag'] = 'no_track'; return out
        c = np.polyfit(t[m], ys[m], 2); res = ys[m] - np.polyval(c, t[m]); ss = np.sum((ys[m] - ys[m].mean()) ** 2)
        r2 = float(1 - np.sum(res ** 2) / ss) if ss > 0 else 0.0
        out['flights'] = [dict(a=0, b=n - 1, c=c.tolist(), n=int(m.sum()), r2=r2, complete=False)]
        if ppm: out['g_curv_first_ok'] = float(2 * c[0] * fps * fps / ppm)
        out['flag'] = 'no_impact_fall' if r2 > 0.98 and c[0] > 0 else 'no_impact'
        return out
    bounds = [0] + imp + [n - 1]
    flights = []
    for k in range(len(bounds) - 1):
        a, b = bounds[k], bounds[k + 1]
        g0 = 0 if k == 0 else guard
        g1 = guard if k < len(bounds) - 2 else 0
        m = (t >= a + g0) & (t <= b - g1) & ~np.isnan(ys)
        if m.sum() < 4:  # short flight (low fps): drop the guard, keep the impact frames out only
            m = (t > a) & (t < b) & ~np.isnan(ys) if k > 0 else (t < b) & ~np.isnan(ys)
        if m.sum() < 3: flights.append(None); continue
        c = np.polyfit(t[m], ys[m], 2)
        res = ys[m] - np.polyval(c, t[m]); ss = np.sum((ys[m] - ys[m].mean()) ** 2)
        flights.append(dict(a=a, b=b, c=c.tolist(), n=int(m.sum()), r2=float(1 - np.sum(res ** 2) / ss) if ss > 0 else 0.0,
                            complete=(k > 0 and k < len(bounds) - 2)))
    # impact level: median of the y where neighbouring parabolas cross near each impact (fallback raw max)
    lev = float(np.nanmedian([ys[i] for i in imp]))
    # sub-frame impact times: the later root of flight k-1 and the earlier root of flight k at the impact level
    ti = []
    for k, i in enumerate(imp):
        cand = []
        fl, fr = flights[k], flights[k + 1]
        if fl is not None:
            r = roots_at(fl['c'], lev)
            if r and abs(r[1] - i) < 2.5: cand.append(r[1])
        if fr is not None:
            r = roots_at(fr['c'], lev)
            if r and abs(r[0] - i) < 2.5: cand.append(r[0])
        ti.append(float(np.mean(cand)) if cand else float(i))
    out['impact_t_frames'] = ti
    T = np.diff(ti)  # flight durations in frames between consecutive impacts
    out['flight_frames'] = T.tolist()
    out['flight_s'] = (T / fps).tolist()
    if len(T):
        out['frames_per_bounce_mean'] = float(np.mean(T))
        out['frames_per_bounce_se'] = float(np.std(T, ddof=1) / np.sqrt(len(T))) if len(T) > 1 else None
    # e from flight-time ratios
    out['e_ratio_seq'] = (T[1:] / T[:-1]).tolist() if len(T) > 1 else []
    # first fall from rest: vertex of the first parabola (release time) to first impact
    f0 = flights[0]
    if f0 is not None and f0['c'][0] > 0:
        tv = -f0['c'][1] / (2 * f0['c'][0])
        t_rel = max(0.0, tv) if release_at_rest else tv
        out['t_release_frames'] = float(tv)
        t_fall = ti[0] - t_rel
        out['t_fall_frames'] = float(t_fall)
        if len(T):
            out['e_timing_first'] = float(T[0] / (2 * t_fall))
    # g estimates
    gc, gt = [], []
    for k, fl in enumerate(flights):
        if fl is None: continue
        a2 = fl['c'][0]
        g_curv = 2 * a2 * fps * fps / ppm if ppm else None
        fl['g_curv'] = g_curv
        if fl.get('complete') and k - 1 < len(T):
            Tk = T[k - 1] / fps
            apex = fl['c'][2] - fl['c'][1] ** 2 / (4 * a2)
            h = (lev - apex) / ppm if ppm else None
            fl['h_m'] = h
            fl['g_timing'] = 8 * h / Tk ** 2 if ppm else None
            if ppm: gt.append(fl['g_timing'])
        if ppm and fl['r2'] > 0.98 and fl['n'] >= 5: gc.append((k, g_curv))
    out['flights'] = flights
    out['impact_level_px'] = lev
    if ppm:
        # primary g: first flight with a good curvature fit (first fall if clean, else first rebound)
        out['g_curv_first_ok'] = gc[0][1] if gc else None
        out['g_timing_first'] = gt[0] if gt else None
        # first fall timing: h0 = lev - y(vertex), g = 2 h0 / t_fall^2
        if f0 is not None and 't_fall_frames' in out:
            y_rel = np.polyval(f0['c'], max(0.0, out['t_release_frames']))
            h0 = (lev - y_rel) / ppm
            out['g_fall_timing'] = float(2 * h0 / (out['t_fall_frames'] / fps) ** 2)
    ok = len(imp) >= 1 and f0 is not None and f0['r2'] > 0.98
    out['flag'] = 'ok' if ok else 'check'
    return out


def measure(path, fps, ppm=None, diam=None, point=None, pframe=0, tmax=None, prom=8.0, guard=1, half=None,
            search=40, refresh=0.8, qc=None, mode='gray', pen=0.002):
    F = read_frames(path, tmax)
    sx, sy, med = auto_seed(F, need_seed=point is None)
    if point is not None: sx, sy = point
    g0 = cv2.cvtColor(F[pframe], cv2.COLOR_BGR2GRAY).astype(np.float32)
    r = ball_radius(F[pframe].astype(np.float32), med, sx, sy)
    if half is None: half = int(max(6, round(1.3 * (r or 10))))
    if ppm is None and diam:
        if r is None: raise SystemExit('cannot size ball; pass --ppm')
        ppm = 2 * r / diam
    xs, ys, sc, G = track(F, sx, sy, pframe, half, search, refresh, pen=pen, mode=mode, med=med)
    out = analyse(ys, fps, ppm, prom, guard)
    out.update(clip=os.path.basename(path), fps=fps, ppm=ppm, r_px=r, seed=[sx, sy], pframe=pframe,
               tracked_frac=float(np.mean(sc >= 0.3)), track_y=[None if np.isnan(v) else round(float(v), 2) for v in ys],
               track_x=[None if np.isnan(v) else round(float(v), 2) for v in xs], score=[round(float(s), 3) for s in sc])
    if qc: make_qc(F, xs, ys, out, qc)
    return out


def make_qc(F, xs, ys, out, path):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 2, figsize=(14, 4.5))
    t = np.arange(len(ys))
    ax[0].plot(t, ys, '.-', ms=3); ax[0].invert_yaxis()
    for ti in out.get('impact_t_frames', []): ax[0].axvline(ti, color='r', lw=0.8)
    for fl in out.get('flights', []):
        if fl is None: continue
        tt = np.linspace(fl['a'], fl['b'], 50); ax[0].plot(tt, np.polyval(fl['c'], tt), 'g-', lw=0.8)
    ax[0].set_title(f"{out['clip']} impacts {['%.1f' % v for v in out.get('impact_t_frames', [])]}", fontsize=8)
    ax[0].set_xlabel('frame'); ax[0].set_ylabel('y px (down)')
    idx = np.linspace(0, len(F) - 1, 8).astype(int)
    tiles = []
    for i in idx:
        f = F[i].copy()
        if not np.isnan(xs[i]): cv2.circle(f, (int(xs[i]), int(ys[i])), 14, (0, 0, 255), 2)
        cv2.putText(f, str(i), (8, 30), 0, 1, (0, 0, 255), 2)
        tiles.append(cv2.resize(f, (320, 185)))
    mont = np.vstack([np.hstack(tiles[:4]), np.hstack(tiles[4:])])
    ax[1].imshow(mont[:, :, ::-1]); ax[1].axis('off')
    fig.tight_layout(); fig.savefig(path, dpi=90); plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip', nargs='?'); ap.add_argument('--fps', type=float, default=24)
    ap.add_argument('--ppm', type=float); ap.add_argument('--diam', type=float)
    ap.add_argument('--point'); ap.add_argument('--pframe', type=int, default=0); ap.add_argument('--tmax', type=int)
    ap.add_argument('--prom', type=float, default=8.0); ap.add_argument('--half', type=int)
    ap.add_argument('--search', type=int, default=40)
    ap.add_argument('--mode', default='gray', choices=['gray', 'diff'])
    ap.add_argument('--pen', type=float, default=0.002, help='NCC penalty per px from the predicted position')
    ap.add_argument('--qc'); ap.add_argument('--json')
    ap.add_argument('--planted', nargs=2, metavar=('PLANTED_JSON', 'CLIPDIR')); ap.add_argument('--out')
    ap.add_argument('--qcdir')
    a = ap.parse_args()
    if a.planted:
        P = json.load(open(a.planted[0]))['clips']; est = {}; full = {}
        for c in P:
            if 'e' not in c['params'] and 'g' not in c['params']: continue
            p = os.path.join(a.planted[1], c['clip_id'] + '.mp4')
            if not os.path.exists(p): continue
            o = measure(p, c['fps'], diam=0.10, mode=a.mode, qc=os.path.join(a.qcdir, c['clip_id'] + '_qc.png') if a.qcdir else None)
            full[c['clip_id']] = {k: v for k, v in o.items() if not k.startswith('track') and k != 'score'}
            e = {}
            if 'g' in c['params']:
                e['g'] = o.get('g_curv_first_ok') or o.get('g_fall_timing')
            if 'e' in c['params'] and o.get('e_timing_first') is not None: e['e'] = o['e_timing_first']
            est[c['clip_id']] = e
            print(c['clip_id'], e, o.get('flag'), 'impacts', ['%.2f' % v for v in o.get('impact_t_frames', [])],
                  'g_fall_timing', o.get('g_fall_timing'), 'g_timing_first', o.get('g_timing_first'), file=sys.stderr)
        json.dump(dict(estimates=est, full=full), open(a.out, 'w'), indent=1)
        return
    pt = tuple(float(v) for v in a.point.split(',')) if a.point else None
    o = measure(a.clip, a.fps, a.ppm, a.diam, pt, a.pframe, a.tmax, a.prom, half=a.half, search=a.search, qc=a.qc, mode=a.mode, pen=a.pen)
    s = json.dumps(o, indent=1)
    if a.json: open(a.json, 'w').write(s)
    print(json.dumps({k: v for k, v in o.items() if k not in ('track_y', 'track_x', 'score', 'flights')}, indent=1))


if __name__ == '__main__':
    main()
