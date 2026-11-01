"""firstfall (raj-2): first free fall of ONE seeded ball, for Cosmos clips where the scene moves around the ball
(gripper retracts, plank tilts, a second ball spawns, the scene resets after impact).

Why: trk.blobs (used by realball / measure_ball v5) takes the largest frame-vs-background blob. On Cosmos GAUGE clips
that is often the retracting gripper or the moving plank, not the ball (task 9 first clip: both tools fit the gripper).

Tracker (no learned model, CPU, ~1 s/clip):
  1. Seed: a point on the ball at frame --pframe (default: trk.blobs centroid on the first frame that has one).
     Ball colour = median Lab colour of the seed component.
  2. Per frame t: candidate pixels = (Lab distance to ball colour < --ctol) AND (differs from frame 0 OR from the
     last window frame by > 30 in some channel). Static look-alikes (dark curtain) fail the second test; a light
     gripper or plank fails the first.
  3. Connected components; keep the one nearest the constant-velocity prediction (max jump --jump px), area within
     [0.15, 8] x the seed area (Cosmos balls grow). Track y = component centroid; d = equivalent diameter.
Fit (unchanged realball v1.1 recipe): motion-prior onset, trk_ballfall first_impact, v0=0 hinge for t0, then
free-v0 quadratic from onset+1 to the frame before impact, residual bootstrap CI. Flag as measure_ball v5
(ok: dAIC quad-vs-linear > 10, R^2 > 0.98, >= 5 points).
Also reports the scale-free readouts: fall_time_s (impact - t0), fall_px, g_from_h_T = 2 h / T^2, and d_growth
(blob size at impact / at the start of the fit window; on real GAUGE drops it is ~1, so >> 1 means the ball grew while
falling and any fixed px/m g is suspect). d_ratio (impact / seed frame) is NOT reliable: the held seed is occluded.
Usage:
  python3 -I firstfall.py clip.mp4 --fps 24 --ppm 539.8 [--point x,y] [--tmax N] [--qc qc.png]
  python3 -I firstfall.py --planted planted.json clip_dir out.json
"""
import sys, os, json, argparse, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); sys.path.insert(0, HERE + '/../trk_ballfall')
import trk, measure_ball as mb, realball
VERSION = 'firstfall v1 (seeded colour+change ball tracker, continuity; blob-minor scale; realball v1.1 fit)'

def lab(F):
    return np.array([cv2.cvtColor(f.clip(0, 255).astype(np.uint8), cv2.COLOR_BGR2LAB).astype(np.float32) for f in F])

def seed_component(F, L, point, pframe, ctol):
    """Seed colour = median Lab of a 5x5 patch at the point. Seed mask = component of (colour match AND change vs the
    first/last frame) containing or nearest the point (within 30 px)."""
    x, y = int(round(point[0])), int(round(point[1]))
    c = np.median(L[pframe][max(y - 2, 0):y + 3, max(x - 2, 0):x + 3].reshape(-1, 3), 0)
    f = F[pframe].astype(np.float32)
    col = np.linalg.norm(L[pframe] - c, axis=2) < ctol
    chg = (np.abs(f - F[-1]).max(2) > 30) | (np.abs(f - F[min(len(F) - 1, pframe + 12)]).max(2) > 30)
    m = cv2.morphologyEx((col & chg).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, l, st, cen = cv2.connectedComponentsWithStats(m)
    if n >= 2:
        d = [np.hypot(cen[i][0] - point[0], cen[i][1] - point[1]) for i in range(1, n)]
        i = 1 + int(np.argmin(d))
        if d[i - 1] < 30: return c, l == i, int(st[i, 4])
    yy, xx = np.mgrid[:F.shape[1], :F.shape[2]]
    return c, (xx - point[0]) ** 2 + (yy - point[1]) ** 2 < 36, 113

def track(F, point=None, pframe=0, ctol=25.0, jump=80):
    if point is None:
        B = trk.blobs(F, mode='ball'); pframe = next(i for i, b in enumerate(B) if b); point = B[pframe][:2]
    L = lab(F); c, mask0, a0 = seed_component(F, L, point, pframe, ctol)
    F32 = F.astype(np.float32); ref0, ref1 = F32[0], F32[-1]; info_minor = [None]
    ys, xs = np.nonzero(mask0); pos = np.array([xs.mean(), ys.mean()]); vel = np.zeros(2)
    T = len(F); cx, cy, area = np.full(T, np.nan), np.full(T, np.nan), np.zeros(T); minor = np.full(T, np.nan)
    cx[pframe], cy[pframe], area[pframe] = pos[0], pos[1], a0
    lost = 0
    for t in range(pframe + 1, T):
        col = np.linalg.norm(L[t] - c, axis=2) < ctol
        chg = (np.abs(F32[t] - ref0).max(2) > 30) | (np.abs(F32[t] - ref1).max(2) > 30)
        m = cv2.morphologyEx((col & chg).astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, l, st, cen = cv2.connectedComponentsWithStats(m)
        pred = pos + vel; best, bd = None, jump * (1 + lost)
        for i in range(1, n):
            if not (0.15 * a0 <= st[i, 4] <= 8 * a0): continue
            d = np.hypot(*(cen[i] - pred))
            if d < bd: best, bd = i, d
        if best is None:
            lost += 1
            if lost > 3: break
            continue
        new = np.array(cen[best]); vel = (new - pos) / (1 + lost); pos = new; lost = 0
        cx[t], cy[t], area[t] = pos[0], pos[1], st[best, 4]
        # size: minor side of the change-mask blob (no colour gate) that holds the colour component, as trk.blobs does
        cm = cv2.morphologyEx(chg.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        nl, ll, sl, _ = cv2.connectedComponentsWithStats(cm)
        lab_ids = ll[l == best]; lab_ids = lab_ids[lab_ids > 0]
        if len(lab_ids):
            j = int(np.bincount(lab_ids).argmax())
            if sl[j, 4] <= 6 * st[best, 4]:
                cnt = cv2.findContours((ll == j).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0][0]
                minor[t] = min(cv2.minAreaRect(cnt)[1])
    info_minor[0] = minor
    return cx, cy, area, dict(point=[float(point[0]), float(point[1])], pframe=int(pframe), ctol=ctol, seed_area=int(a0), minor=info_minor[0])

def measure(F, fps, ppm=None, diam=None, point=None, pframe=0, tmax=None, nboot=200, seed=0, skip=1, move_px=4.0, no_dedup=True):
    keep, P = (list(range(len(F))), 0) if no_dedup else realball.dedup(F)
    fps_true = fps * len(keep) / len(F); F = F[keep]
    if tmax: F = F[:tmax]
    cx, cy, area, info = track(F, point, pframe)
    ok = np.where(np.isfinite(cy))[0]
    def lost(reason):
        info.pop('minor', None)
        return (dict(flag='lost', reason=reason, n_tracked=int(len(ok)), fps_true=float(fps_true),
                     track_info=info, method=VERSION), (cx, cy, area))
    if len(ok) < 6:
        return lost('fewer than six tracked points')
    t = ok / fps_true; y = cy[ok]; dpx = 2 * np.sqrt(area[ok] / np.pi)
    mn = info.pop('minor')[ok]; mn[0] = dpx[0] if not np.isfinite(mn[0]) else mn[0]
    dsz = np.where(np.isfinite(mn), mn, dpx)                              # scale: blob minor side where clean, else colour-blob equiv. diameter
    s = 1.0 / ppm if ppm else diam / np.median(dsz)
    Y = y * s
    r = int(np.argmax(y > np.median(y[:3]) + move_px)) if np.any(y > np.median(y[:3]) + move_px) else 0
    a0 = max(r - 6, 0)
    k = a0 + mb.first_impact(Y[a0:], 0.006 if (diam and not ppm) else 2 * s)
    n = max(k - 1, a0 + 5)
    if n > len(ok):
        return lost('insufficient tracked points after motion onset')
    p = mb.fit_hinge(t[a0:n], Y[a0:n]); t0 = p[2]
    j0 = int(np.searchsorted(t, t0)) + skip
    if n - j0 < 4: j0 = max(n - 4, 0)
    if diam and not ppm:
        s = diam / np.median(dsz[j0:n]); Y = y * s
    tt, YY = t[j0:n], Y[j0:n]
    c = np.polyfit(tt, YY, 2); res = YY - np.polyval(c, tt); N = len(tt)
    r2 = 1 - (res ** 2).sum() / max(((YY - YY.mean()) ** 2).sum(), 1e-12)
    cl = np.polyfit(tt, YY, 1); rl = YY - np.polyval(cl, tt)
    aic = lambda rr, kk: N * np.log(max((rr ** 2).mean(), 1e-18)) + 2 * kk
    dAIC = float(aic(rl, 2) - aic(res, 3))
    flag = 'ok' if (dAIC > 10 and r2 > 0.98 and N >= 5) else ('no_free_fall' if dAIC <= 2 else 'weak')
    rng = np.random.default_rng(seed)
    gs = [2 * np.polyfit(tt, np.polyval(c, tt) + rng.choice(res, N), 2)[0] for _ in range(nboot)]
    e = None
    if k < len(Y) - 6:
        j = k + 1
        while j < len(Y) - 1 and Y[j + 1] < Y[j] + 0.003: j += 1
        tr, yr = t[k:j + 1], Y[k:j + 1]
        if len(tr) >= 4:
            cr = np.polyfit(tr, yr, 2)
            if cr[0] > 0:
                h0 = Y[k] - np.median(Y[:max(r, 1)]); hr = Y[k] - np.polyval(cr, -cr[1] / (2 * cr[0]))
                if h0 > 0 and hr > 0: e = float(np.sqrt(hr / h0))
    fall_px = float(y[k] - np.median(y[:max(r, 1)])); T_fall = float(t[k] - t0)
    out = dict(g=float(2 * c[0]), g_ci95=[float(np.percentile(gs, 2.5)), float(np.percentile(gs, 97.5))], g_sd=float(np.std(gs)),
               r2=float(r2), dAIC_quad_vs_lin=dAIC, flag=flag, n_fit=int(N), t0=float(t0),
               fit_frames=[int(ok[j0]), int(ok[n - 1])], motion_frame=int(ok[r]), impact_frame=int(ok[k]),
               fall_time_s=T_fall, fall_px=fall_px, fall_m=fall_px * s, g_from_h_T=float(2 * fall_px * s / T_fall ** 2) if T_fall > 0 else None,
               d_seed_px=float(dsz[0]), d_impact_px=float(np.median(dsz[max(k - 2, 0):k + 1])), d_ratio=float(np.median(dsz[max(k - 2, 0):k + 1]) / dsz[0]),
               d_fallstart_px=float(np.median(dsz[j0:j0 + 3])), d_growth=float(np.median(dsz[max(k - 2, 0):k + 1]) / np.median(dsz[j0:j0 + 3])),
               e=e, m_per_px=float(s), fps_true=float(fps_true), n_tracked=int(len(ok)), track_info=info, method=VERSION)
    return out, (cx, cy, area)

def qc_png(path, F, trk_, r):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    cx, cy, area = trk_
    fig, ax = plt.subplots(1, 2, figsize=(15, 5), gridspec_kw=dict(width_ratios=[1, 2]))
    ax[0].plot(np.arange(len(cy)), cy, '.'); ax[0].invert_yaxis(); ax[0].set_xlabel('frame'); ax[0].set_ylabel('y px (down)')
    if r['flag'] == 'lost':
        ax[0].set_title(f"[lost] {r['reason']} (n={r['n_tracked']})")
        ax[1].axis('off')
        fig.tight_layout(); fig.savefig(path, dpi=70); plt.close(fig)
        return
    for f, col in [(r['fit_frames'][0], 'g'), (r['fit_frames'][1], 'b'), (r['impact_frame'], 'r')]: ax[0].axvline(f, color=col, ls='--')
    ax[0].set_title(f"[{r['flag']}] g={r['g']:.2f} [{r['g_ci95'][0]:.2f},{r['g_ci95'][1]:.2f}] R2={r['r2']:.3f} n={r['n_fit']}\n"
                    f"T_fall={r['fall_time_s']:.3f}s fall={r['fall_px']:.0f}px d_ratio={r['d_ratio']:.2f}", fontsize=9)
    a, b = max(r['motion_frame'] - 3, 0), min(r['impact_frame'] + 3, len(F) - 1)
    sel = sorted(set(np.linspace(a, b, 8).astype(int)))
    tiles = []
    for i in sel:
        im = F[i].clip(0, 255).astype(np.uint8).copy()
        if np.isfinite(cy[i]): cv2.circle(im, (int(cx[i]), int(cy[i])), int(max(5, np.sqrt(area[i] / np.pi))), (0, 0, 255), 2)
        cv2.putText(im, str(i), (5, 30), 0, 1, (0, 255, 255), 2); tiles.append(cv2.resize(im, (im.shape[1] // 2, im.shape[0] // 2)))
    while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
    ax[1].imshow(cv2.cvtColor(np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)]), cv2.COLOR_BGR2RGB)); ax[1].axis('off')
    fig.tight_layout(); fig.savefig(path, dpi=70); plt.close(fig)

if __name__ == '__main__':
    if sys.argv[1] == '--planted':
        d = json.load(open(sys.argv[2])); est = {}
        for c in d['clips']:
            F = trk.load(f"{sys.argv[3]}/{c['clip_id']}.mp4"); p = c['params']
            if 'period_s' in p: r = trk.pend(F, c['fps'])
            elif 'a' in p: r = trk.incline(F, c['fps'])
            else: r = measure(F, c['fps'], diam=0.10, nboot=50)[0]
            est[c['clip_id']] = {k: v for k, v in r.items() if k in p and v is not None}
            print(c['clip_id'], est[c['clip_id']], {k: r.get(k) for k in ('flag', 't0', 'n_fit', 'r2', 'fall_time_s', 'd_ratio')}, flush=True)
        json.dump(est, open(sys.argv[4], 'w'), indent=1); sys.exit()
    a = argparse.ArgumentParser(); a.add_argument('clip'); a.add_argument('--fps', type=float, required=True)
    a.add_argument('--ppm', type=float); a.add_argument('--diam', type=float); a.add_argument('--point'); a.add_argument('--pframe', type=int, default=0)
    a.add_argument('--tmax', type=int); a.add_argument('--qc'); a.add_argument('--dedup', action='store_true')
    o = a.parse_args(); assert o.ppm or o.diam
    F = trk.load(o.clip); pt = [float(v) for v in o.point.split(',')] if o.point else None
    r, tr = measure(F, o.fps, o.ppm, o.diam, pt, o.pframe, o.tmax, no_dedup=not o.dedup)
    if o.qc: qc_png(o.qc, F if not o.tmax else F[:o.tmax], tr, r)
    print(json.dumps(r, indent=1))
