"""kiro-1 t191: rod-angle pendulum tracker, independent of trk_ballfall/measure_pend (no shared code).

Idea: the GAUGE pendulum rod is a light wooden stick against a dark curtain. Per frame:
  1. tan mask (HSV H 6-26, S>45, V>90) in the pendulum ROI, minus pixels that are tan in >60% of frames
     (static parts: fixed crossbar, table edge);
  2. principal axis of the moving-rod pixels -> one line per frame;
  3. pivot = least-squares intersection of all per-frame lines (data-driven; no hand-placed pivot);
  4. rod tip = mask pixel farthest from the pivot along the axis; L(t) = |tip - pivot| (projected rod length),
     theta(t) = atan2(tip_x - px, tip_y - py) (0 = hanging down, + = toward image left);
  5. rigidity diagnostics: pivot residual (median distance of per-frame lines from the pivot),
     and L(t) compared with the real clip's L(theta) curve (projection makes L depend on theta even for a rigid rod);
  6. period: damped sinusoid theta = c + A exp(-g t) cos(2 pi t / T + phi), T grid 0.3-5 s, linear LS inside;
     95% CI by residual block bootstrap (200 draws).
Usage: python3 rodtrack.py out.json qc_dir clip1.mp4 [clip2.mp4 ...]   (fps from sidecar .json if present, else 24)
"""
import sys, os, json, numpy as np, cv2

ROI = (0, 40, 420, 275)  # x0, y0, x1, y1 in 832x480 letterboxed frames


def load(path, maxf=93):
    c = cv2.VideoCapture(path); F = []
    while len(F) < maxf:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    return np.array(F)


def tan_mask(F):
    x0, y0, x1, y1 = ROI
    M = []
    for f in F:
        h = cv2.cvtColor(f[y0:y1, x0:x1], cv2.COLOR_BGR2HSV)
        m = (h[..., 0] >= 6) & (h[..., 0] <= 26) & (h[..., 1] > 45) & (h[..., 2] > 90)
        M.append(m)
    M = np.array(M)
    static = M.mean(0) > 0.6
    M &= ~static[None]
    out = []
    for m in M:
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
        if n <= 1: out.append(np.zeros_like(m, bool)); continue
        k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
        out.append(lab == k)
    return np.array(out)


def lines(M):
    x0, y0 = ROI[:2]; L = []
    for m in M:
        ys, xs = np.nonzero(m)
        if len(xs) < 40: L.append(None); continue
        P = np.c_[xs + x0, ys + y0].astype(float); mu = P.mean(0)
        _, s, Vt = np.linalg.svd(P - mu, full_matrices=False)
        elong = s[0] / max(s[1], 1e-6)
        L.append((mu, Vt[0], elong, P))
    return L


def pivot(L):
    A = np.zeros((2, 2)); b = np.zeros(2); used = 0
    for l in L:
        if l is None or l[2] < 4: continue
        mu, d = l[0], l[1]; Pm = np.eye(2) - np.outer(d, d); A += Pm; b += Pm @ mu; used += 1
    p = np.linalg.solve(A, b)
    res = [np.linalg.norm((np.eye(2) - np.outer(l[1], l[1])) @ (p - l[0])) for l in L if l is not None and l[2] >= 4]
    return p, float(np.median(res)), used


def fit_period(t, th, nboot=200, seed=0):
    def best(y):
        bestv = None
        for T in np.linspace(0.3, 5.0, 471):
            for g in (0.0, 0.1, 0.25, 0.5, 1.0):
                e = np.exp(-g * t); w = 2 * np.pi / T
                X = np.c_[np.ones_like(t), e * np.cos(w * t), e * np.sin(w * t)]
                c, *_ = np.linalg.lstsq(X, y, rcond=None); r = y - X @ c; sse = float(r @ r)
                if bestv is None or sse < bestv[0]: bestv = (sse, T, g, X @ c)
        return bestv
    sse, T, g, yh = best(th)
    r2 = 1 - sse / float(((th - th.mean()) ** 2).sum())
    rng = np.random.default_rng(seed); res = th - yh; B = 6; Ts = []
    nb = int(np.ceil(len(t) / B))
    for _ in range(nboot):
        idx = np.concatenate([np.arange(s, min(s + B, len(t))) for s in rng.integers(0, len(t) - B, nb)])[:len(t)]
        Ts.append(best(yh + res[idx])[1])
    return dict(T=float(T), gamma=float(g), r2=float(r2), ci95=[float(np.percentile(Ts, 2.5)), float(np.percentile(Ts, 97.5))], fit=yh)


def measure(F, fps):
    M = tan_mask(F); L = lines(M); p, pres, used = pivot(L)
    t, th, Ln, el = [], [], [], []
    for i, l in enumerate(L):
        if l is None or l[2] < 4: continue
        P = l[3]; dd = np.linalg.norm(P - p, axis=1); tip = P[np.argmax(dd)]
        t.append(i / fps); th.append(np.degrees(np.arctan2(p[0] - tip[0], tip[1] - p[1]))); Ln.append(float(dd.max())); el.append(l[2])
    t, th, Ln = map(np.array, (t, th, Ln))
    out = dict(pivot=p.tolist(), pivot_resid_px=pres, n_frames=len(F), n_valid=int(len(t)), valid_frac=len(t) / len(F),
               L_med=float(np.median(Ln)) if len(Ln) else None, L_cv=float(Ln.std() / Ln.mean()) if len(Ln) else None,
               t=t.tolist(), theta=th.tolist(), L=Ln.tolist())
    if len(t) >= 20:
        f = fit_period(t, th); out.update(T=f['T'], gamma=f['gamma'], r2=f['r2'], ci95=f['ci95']); out['fit'] = f['fit'].tolist()
    return out


def qc(F, r, path, title=''):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(1, 3, figsize=(16, 4))
    ax[0].plot(r['t'], r['theta'], '.', ms=3)
    if 'fit' in r: ax[0].plot(r['t'], r['fit'])
    ax[0].set_title(f"{title} T={r.get('T', float('nan')):.3f} R2={r.get('r2', float('nan')):.2f} valid={r['valid_frac']:.2f}", fontsize=8)
    ax[0].set_xlabel('t (s)'); ax[0].set_ylabel('theta (deg)')
    ax[1].plot(r['theta'], r['L'], '.', ms=3); ax[1].set_xlabel('theta'); ax[1].set_ylabel('L px'); ax[1].set_title(f"pivot resid {r['pivot_resid_px']:.1f}px", fontsize=8)
    idx = [0, len(F) // 4, len(F) // 2, 3 * len(F) // 4]
    tiles = []
    for i in idx:
        im = F[i].copy(); px, py = map(int, r['pivot']); cv2.circle(im, (px, py), 5, (0, 0, 255), 2)
        tiles.append(im[0:300, 0:450, ::-1])
    ax[2].imshow(np.hstack(tiles)); ax[2].axis('off')
    plt.tight_layout(); plt.savefig(path, dpi=80); plt.close()


if __name__ == '__main__':
    out_json, qcd = sys.argv[1:3]; os.makedirs(qcd, exist_ok=True); res = {}
    for p in sys.argv[3:]:
        sc = p[:-4] + '.json'; fps = json.load(open(sc)).get('fps', 24) if os.path.exists(sc) else 24
        F = load(p); r = measure(F, float(fps)); name = os.path.basename(p)[:-4]
        qc(F, r, f'{qcd}/{name}.png', name); res[name] = {k: v for k, v in r.items() if k not in ('t', 'theta', 'L', 'fit')}
        res[name]['series'] = dict(t=r['t'], theta=r['theta'], L=r['L'])
        print(name, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res[name].items() if k in ('T', 'r2', 'ci95', 'valid_frac', 'pivot', 'pivot_resid_px', 'L_cv')})
    json.dump(res, open(out_json, 'w'), default=float)
