"""samball (raj-1): ball-drop g from a SAM2.1 mask track, for Cosmos clips whose held ball jitters before release.

Why: trk_ballfall v5 / realball take the first >=2 px upward reversal as the first impact. On Cosmos GAUGE clips the
held ball jitters during the hold, so they fit frames 1-4 of the hold and miss the fall (seen on gauge_ball1_noneg_s1:
v5 flag no_free_fall g=-0.007; realball g=0.65 on frames 1-4, while the ball visibly falls at frames ~26-33).

Method:
1. SAM2.1-hiera-small (transformers) video tracking from a point prompt on frame 0 (--point x,y; default: trk_ballfall
   blob centroid on frame 0). Per frame: mask centroid y, area.
2. Fall segment: y_top = median y of the first 5 tracked frames; y_bot = max y. First impact k = first frame with
   y >= y_bot - tol (tol = 0.15 * fall height in px). Window start = last frame before k with y <= y_top + tol, minus 6.
3. g: trk_ballfall v5 fit_onset (hinge locates release t0; free-v0 quadratic from t0 + 1 frame) on [start, k-1].
   Residual-bootstrap CI. Scale from --ppm (px/m) or --diam (m, median mask equivalent diameter on the fall frames).
Usage: python3 -I samball.py clip.mp4 --fps 24 --ppm 539.8 [--point x,y] [--pframe 0] [--device cpu] [--qc out.png]
"""
import sys, json, argparse, numpy as np, cv2, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../trk_ballfall')
import measure_ball as mb
VERSION = 'samball v1 (SAM2.1-small track + robust fall window + v5 fit_onset skip=1)'
SAM = os.environ.get('SAMBALL_MODEL', 'facebook/sam2.1-hiera-small')

def read(path):
    cap = cv2.VideoCapture(path); F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(f)
    return np.array(F)

def auto_point(F):
    import trk
    B = trk.blobs(F, mode='ball')
    for b in B:
        if b: return [float(b[0]), float(b[1])]
    raise SystemExit('no blob on first frames; pass --point')

def sam_track(F, point, device='cpu', pframe=0):
    import torch
    from transformers import Sam2VideoModel, Sam2VideoProcessor
    from PIL import Image
    dt = torch.float32 if device == 'cpu' else torch.bfloat16
    model = Sam2VideoModel.from_pretrained(SAM).to(device, dtype=dt).eval()
    proc = Sam2VideoProcessor.from_pretrained(SAM)
    frames = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in F]
    sess = proc.init_video_session(video=frames, inference_device=device, dtype=dt)
    proc.add_inputs_to_inference_session(inference_session=sess, frame_idx=pframe, obj_ids=1,
                                         input_points=[[[point]]], input_labels=[[[1]]])
    H, W = F.shape[1:3]
    out = {}
    with torch.inference_mode():
        model(inference_session=sess, frame_idx=pframe)
        for o in model.propagate_in_video_iterator(sess, start_frame_idx=pframe):
            m = proc.post_process_masks([o.pred_masks], original_sizes=[[H, W]], binarize=True)[0]
            out[o.frame_idx] = m[0, 0].cpu().numpy().astype(bool)
    cy, cx, area = np.full(len(F), np.nan), np.full(len(F), np.nan), np.zeros(len(F))
    for i, m in out.items():
        if m.sum() > 0:
            ys, xs = np.nonzero(m); cy[i], cx[i], area[i] = ys.mean(), xs.mean(), m.sum()
    return cx, cy, area

def fall_window(y, pre=6):
    ok = np.where(np.isfinite(y))[0]
    yt = np.median(y[ok[:5]]); yb = np.nanmax(y); tol = 0.15 * (yb - yt)
    k = int(ok[np.argmax(y[ok] >= yb - tol)])
    before = ok[(ok < k) & (y[ok] <= yt + tol)]
    s = int(before[-1]) if len(before) else int(ok[0])
    return max(int(ok[0]), s - pre), k, yt, yb

def measure(F, fps, ppm=None, diam=None, point=None, device='cpu', nboot=300, seed=0, skip=1, track=None, pframe=0):
    cx, cy, area = track if track is not None else sam_track(F, point or auto_point(F), device, pframe)
    w0, k, yt, yb = fall_window(cy)
    idx = np.array([i for i in range(w0, k) if np.isfinite(cy[i]) and area[i] > 0])
    t = idx / fps
    d_px = float(np.median(2 * np.sqrt(area[idx[-6:]] / np.pi)))
    s = 1.0 / ppm if ppm else diam / d_px
    Y = cy[idx] * s
    c, j, p = mb.fit_onset(t, Y, fps, skip=skip)
    tt, YY = t[j:], Y[j:]
    res = YY - np.polyval(c, tt)
    r2 = 1 - (res ** 2).sum() / max(((YY - YY.mean()) ** 2).sum(), 1e-12)
    cl = np.polyfit(tt, YY, 1); rl = YY - np.polyval(cl, tt); n = len(tt)
    aic = lambda r, kk: n * np.log(max((r ** 2).mean(), 1e-18)) + 2 * kk
    rng = np.random.default_rng(seed)
    gs = [2 * np.polyfit(tt, np.polyval(c, tt) + rng.choice(res, n), 2)[0] for _ in range(nboot)]
    g_by_skip = {}
    for sk in range(4):
        try: g_by_skip[sk] = float(2 * mb.fit_onset(t, Y, fps, skip=sk)[0][0])
        except Exception: pass
    dAIC = float(aic(rl, 2) - aic(res, 3))
    flag = 'ok' if (dAIC > 10 and r2 > 0.98 and n >= 5) else ('no_free_fall' if dAIC <= 2 else 'weak')
    return dict(g=float(2 * c[0]), g_ci95=[float(np.percentile(gs, 2.5)), float(np.percentile(gs, 97.5))],
                g_sd=float(np.std(gs)), r2=float(r2), n_quad=int(n), dAIC_quad_vs_lin=dAIC, flag=flag,
                onset_t=float(p[2]), fit_frames=[int(idx[j]), int(idx[-1])], impact_frame=int(k),
                fall_px=float(yb - yt), fall_m=float((yb - yt) * s), d_px=d_px, m_per_px=float(s),
                g_by_skip=g_by_skip, g_hinge_v0=float(p[1]), method=VERSION), (cx, cy, area)

def qc_png(path, F, track, r):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    cx, cy, area = track; t = np.arange(len(cy))
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    ax[0].plot(t, cy, '.', ms=3); ax[0].invert_yaxis(); ax[0].set_xlabel('frame'); ax[0].set_ylabel('y px (down)')
    for f, col in [(r['fit_frames'][0], 'g'), (r['fit_frames'][1], 'b'), (r['impact_frame'], 'r')]: ax[0].axvline(f, color=col, ls='--')
    ax[0].set_title(f"[{r['flag']}] g={r['g']:.2f} CI {r['g_ci95'][0]:.2f}-{r['g_ci95'][1]:.2f} R2={r['r2']:.3f} n={r['n_quad']}")
    a, b = r['fit_frames'][0], r['impact_frame']
    sel = sorted(set(np.linspace(max(a - 2, 0), min(b + 1, len(F) - 1), 8).astype(int)))
    tiles = []
    for i in sel:
        im = F[i].copy()
        if np.isfinite(cy[i]): cv2.circle(im, (int(cx[i]), int(cy[i])), int(max(4, np.sqrt(area[i] / np.pi))), (0, 0, 255), 2)
        cv2.putText(im, str(i), (5, 30), 0, 1, (0, 255, 255), 2); tiles.append(cv2.resize(im, (im.shape[1] // 2, im.shape[0] // 2)))
    while len(tiles) % 4: tiles.append(np.zeros_like(tiles[0]))
    grid = np.vstack([np.hstack(tiles[i:i + 4]) for i in range(0, len(tiles), 4)])
    ax[1].imshow(cv2.cvtColor(grid, cv2.COLOR_BGR2RGB)); ax[1].axis('off')
    fig.tight_layout(); fig.savefig(path, dpi=80); plt.close(fig)

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('clip'); ap.add_argument('--fps', type=float, required=True)
    ap.add_argument('--ppm', type=float); ap.add_argument('--diam', type=float)
    ap.add_argument('--point'); ap.add_argument('--device', default='cpu'); ap.add_argument('--qc')
    ap.add_argument('--track_out'); ap.add_argument('--pframe', type=int, default=0)
    a = ap.parse_args()
    F = read(a.clip)
    pt = [float(v) for v in a.point.split(',')] if a.point else None
    r, tr = measure(F, a.fps, a.ppm, a.diam, pt, a.device, pframe=a.pframe)
    if a.qc: qc_png(a.qc, F, tr, r)
    if a.track_out: json.dump(dict(cx=[None if not np.isfinite(v) else float(v) for v in tr[0]],
                                   cy=[None if not np.isfinite(v) else float(v) for v in tr[1]], area=tr[2].tolist()), open(a.track_out, 'w'))
    print(json.dumps(r, indent=1))
