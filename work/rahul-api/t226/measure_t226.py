#!/usr/bin/env python3
"""t226 per-clip measurements (written before any t226 clip was fetched; see PREREG.md + Amendment 1).
usage: python measure_t226.py <clip_dir> <out.json>   (clips named t226_<scene>_<arm>_s<seed>.mp4)"""
import sys, os, re, json, glob
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'realball')); sys.path.insert(0, os.path.join(REPO, 'tools', 'trk_ballfall'))
sys.path.insert(0, os.path.join(REPO, 'work', 'rahul-api', 't193'))
import firstfall as ff
import rec_period as rp

ROI = {'P': (180, 95, 460, 300), 'F': (230, 95, 345, 400), 'H': (230, 95, 345, 400)}  # x0, y0, x1, y1
SEED_PT = {'F': (284.0, 150.0), 'H': (281.0, 118.0)}
D_BALL = 21.0
NCC_STAY = 0.8   # Amendment 1: stay-check threshold
HALF = 15        # stay-check patch = 31x31 around the seed point


def load_bgr(path):
    c = cv2.VideoCapture(path); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        if f.shape[:2] != (480, 832): f = cv2.resize(f, (832, 480), interpolation=cv2.INTER_AREA)
        F.append(f)
    return np.array(F), c.get(cv2.CAP_PROP_FPS)


def motion_energy(G, box=None):
    if box is not None:
        x0, y0, x1, y1 = box; G = G[:, y0:y1, x0:x1]
    return float(np.abs(np.diff(G, axis=0)).mean())


def stays(F, pt, t):
    """NCC of the input ball patch vs frame t at the same place (Amendment 1)."""
    x, y = int(round(pt[0])), int(round(pt[1]))
    a = cv2.cvtColor(F[0], cv2.COLOR_BGR2GRAY)[y - HALF:y + HALF + 1, x - HALF:x + HALF + 1].astype(np.float32)
    b = cv2.cvtColor(F[t], cv2.COLOR_BGR2GRAY)[y - HALF:y + HALF + 1, x - HALF:x + HALF + 1].astype(np.float32)
    a = a - a.mean(); b = b - b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))


def ball_stats(F, scene):
    pt = SEED_PT[scene]
    cx, cy, area, info = ff.track(F, point=pt, pframe=0)
    T = len(F); ok = np.isfinite(cy)
    last = int(np.nonzero(ok)[0].max()); y0 = float(cy[0])
    lost_up = (last < T - 1) and (cy[last] < 2 * D_BALL)
    out = dict(track_frames=int(ok.sum()), last_tracked=last, lost_up=bool(lost_up), y0=y0,
               ncc8=stays(F, pt, 8), ncc_end=float(np.median([stays(F, pt, t) for t in range(84, min(93, T))])))
    # dy8 (F primary)
    if ok[8]: out['dy8'], out['dy8_src'] = float(cy[8] - y0), 'track'
    elif lost_up and last < 8: out['dy8'], out['dy8_src'] = float(-(y0 + D_BALL)), 'lost_up'
    elif out['ncc8'] >= NCC_STAY: out['dy8'], out['dy8_src'] = 0.0, 'stay'
    else: out['dy8'], out['dy8_src'] = None, 'missing'
    # dyEnd (H primary)
    seg = cy[84:93]
    if np.isfinite(seg).sum() >= 3: out['dyEnd'], out['dyEnd_src'] = float(np.nanmedian(seg) - y0), 'track'
    elif lost_up: out['dyEnd'], out['dyEnd_src'] = float(-(y0 + D_BALL)), 'lost_up'
    elif out['ncc_end'] >= NCC_STAY: out['dyEnd'], out['dyEnd_src'] = 0.0, 'stay'
    else: out['dyEnd'], out['dyEnd_src'] = None, 'missing'
    d = np.abs(np.diff(cy[46:93])); out['LM'] = float(np.nanmean(d)) if np.isfinite(d).sum() >= 5 else None
    out['cy'] = [None if not np.isfinite(v) else round(float(v), 2) for v in cy]
    return out


def period_stats(G, fps):
    r1 = rp.measure(G, fps)
    tmin0 = rp.TMIN; rp.TMIN = 0.25
    try: r2 = rp.measure(G, fps)   # Amendment 1 sensitivity window 0.25-3.2 s
    finally: rp.TMIN = tmin0
    keep = ('period_s', 'depth', 'flag', 'octave_depth', 'boot_se', 'mask_frac')
    return dict(period_v1={k: r1.get(k) for k in keep}, period_w025={k: r2.get(k) for k in keep})


def main(clip_dir, out_path):
    res = {}
    for p in sorted(glob.glob(os.path.join(clip_dir, 't226_*.mp4'))):
        m = re.match(r't226_([PFH])_(\w+?)_s(\d+)\.mp4$', os.path.basename(p))
        if not m: continue
        scene, arm, seed = m.group(1), m.group(2), int(m.group(3))
        F, fps = load_bgr(p)
        G = np.array([cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32) for f in F])
        r = dict(scene=scene, arm=arm, seed=seed, n_frames=len(F), fps=fps,
                 ME_roi=motion_energy(G, ROI[scene]), ME_full=motion_energy(G))
        if scene == 'P': r.update(period_stats(G, 24.0))
        else: r.update(ball_stats(F, scene))
        res[os.path.basename(p)[:-4]] = r
        print(os.path.basename(p), {k: r[k] for k in r if k not in ('cy',)}, flush=True)
    json.dump(res, open(out_path, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
