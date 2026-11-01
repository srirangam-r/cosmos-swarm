"""Synthetic hover-then-fall test (raj-3). Renders 832x480 @24fps clips: 0.06 m ball (22 px), hover tau s, fall with g, bounce e=0.6.
Compares v4 hinge fit, v3 free quadratic, and a GAUGE-style s=b+k t^2 fit from frame 0 (a=2k; segment start assumed = clip start).
Usage: python3 -I synth_hover_test.py <outdir>"""
import sys, os, json, numpy as np, cv2
sys.path.insert(0, __file__.rsplit('/', 1)[0])
import trk, measure_ball as mb
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
W, H, FPS, N, DPX, D = 832, 480, 24, 120, 22.0, 0.06
mpp = D / DPX; rng = np.random.default_rng(1)
bg = np.clip(170 + rng.normal(0, 6, (H, W, 3)), 0, 255).astype(np.uint8); bg = cv2.GaussianBlur(bg, (5, 5), 0)
cv2.rectangle(bg, (0, 400), (W, H), (90, 110, 130), -1)
def traj(g, tau, h=0.30, e=0.6):
    y = np.zeros(N); t = np.arange(N) / FPS
    for i, ti in enumerate(t):
        s = ti - tau
        if s <= 0: y[i] = 0; continue
        tf = np.sqrt(2 * h / g)
        if s < tf: y[i] = 0.5 * g * s * s; continue
        v = e * g * tf; s -= tf; hh = h
        while True:  # bounces
            tb = 2 * v / g
            if s < tb: y[i] = hh - (v * s - 0.5 * g * s * s); break
            s -= tb; v *= e
            if v < 0.05: y[i] = hh; break
    return y
rows = []
for g in (0.45, 2.0, 9.81):
    for tau in (0.0, 0.5, 1.0):
        y = traj(g, tau); yc0 = 400 - 0.30 / mpp - DPX / 2
        fn = f"{out}/hover_g{g}_tau{tau}.mp4"
        vw = cv2.VideoWriter(fn, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (W, H))
        for yi in y:
            f = bg.copy(); cy = yc0 + yi / mpp
            cv2.circle(f, (int(416 * 16), int(round(cy * 16))), int(DPX / 2 * 16), (30, 30, 200), -1, cv2.LINE_AA, 4)
            f = np.clip(f + rng.normal(0, 2, f.shape), 0, 255).astype(np.uint8); vw.write(f)
        vw.release()
        F = trk.load(fn); r = mb.measure(F, FPS, diam=D, nboot=100)
        B = trk.blobs(F, mode='ball'); ok = [i for i, b in enumerate(B) if b]
        t = np.array(ok) / FPS; Y = np.array([B[i][1] for i in ok]) * r['m_per_px']
        n = r['n_fit']; A = np.vstack([np.ones(n), t[:n] ** 2]).T
        k = np.linalg.lstsq(A, Y[:n], rcond=None)[0][1]
        row = dict(g_true=g, tau=tau, g_hinge=r['g'], g_ci95=r['g_ci95'], t0=r['t0'], r2_hinge=r['r2'],
                   g_poly_v3=r['g_poly_v3'], g_gauge_style=float(2 * k), n_fit=n, d_px=r['d_px'])
        rows.append(row); print(json.dumps(row))
        json.dump(dict(kind='synthetic', g=g, tau=tau, h=0.30, e=0.6, fps=FPS, frames=N, size=f'{W}x{H}', d_px=DPX, diam_m=D),
                  open(fn.replace('.mp4', '.json'), 'w'))
json.dump(rows, open(f'{out}/results.json', 'w'), indent=1)
