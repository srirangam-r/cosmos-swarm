"""rog2 tracker-free pendulum period on real GAUGE video at Cosmos resolution.
No blob tracking: ROI pixel stack -> PCA -> PC1 time series; release = first sustained rise of frame-diff energy;
period = mean spacing of upward zero crossings of PC1 (after release), plus a sine-fit refinement.
Timing: dedup exact/near duplicate frames (25 fps content in 30 fps container), uniform 25 fps clock.
Input transform: 1280x720 -> 832x468 (+6px letterbox pad irrelevant for ROI), first 7.875 s of distinct frames."""
import json, sys, subprocess, numpy as np
from scipy.optimize import curve_fit
VID = '../data/gauge/data/rigid/pendulum/video/{}.mp4'
W, H = 832, 468
def frames(k, n=260):
    cmd = ['ffmpeg', '-v', 'error', '-i', VID.format(k), '-frames:v', str(n), '-vf', f'scale={W}:{H}:flags=bicubic',
           '-f', 'rawvideo', '-pix_fmt', 'gray', '-']
    b = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(b, np.uint8).reshape(-1, H, W).astype(np.float32)
def analyse(k):
    F = frames(k)
    d = np.abs(np.diff(F, axis=0)).mean((1, 2))
    keep = np.r_[True, d > 0.15 * np.median(d[d > 0]) if (d > 0).any() else d > 0]
    # duplicates: tiny diff relative to neighbours
    dup_idx = np.where(~keep)[0]
    F = F[keep]; fps = 25.0
    F = F[:int(round(7.875 * fps))]
    t = np.arange(len(F)) / fps
    roi = F[:, 40:260, 150:560]                     # swing region at 832x468 (rod + ball)
    X = roi.reshape(len(F), -1)
    e = np.abs(np.diff(X, axis=0)).mean(1)
    base = np.median(e[:15]); thr = base + 0.5 * (np.percentile(e, 90) - base)
    above = e > thr
    rel = next(i for i in range(len(above) - 5) if above[i:i + 5].all())
    Xs = X[rel:] - X[rel:].mean(0)
    U, S, Vt = np.linalg.svd(Xs, full_matrices=False)
    s = U[:, 0] * S[0]; ts = t[rel:]
    s = s - np.convolve(s, np.ones(31) / 31, mode='same') * 0  # no detrend (keep simple)
    z = np.where((s[:-1] < 0) & (s[1:] >= 0))[0]
    zc = ts[z] + (0 - s[z]) / (s[z + 1] - s[z]) / fps
    zc = zc[zc > ts[0] + 0.3]   # skip release transient
    T_zc = (zc[-1] - zc[0]) / (len(zc) - 1) if len(zc) >= 3 else np.nan
    f = lambda tt, A, w, p, c, b: A * np.exp(-b * tt) * np.sin(w * tt + p) + c
    try:
        m = ts > ts[0] + 0.3
        p, _ = curve_fit(f, ts[m] - ts[0], s[m], p0=[s.std() * 1.4, 2 * np.pi / T_zc, 0, 0, 0.0], maxfev=20000)
        r = s[m] - f(ts[m] - ts[0], *p); R2 = 1 - r.var() / s[m].var(); T_fit = 2 * np.pi / abs(p[1])
    except Exception:
        T_fit, R2 = np.nan, np.nan
    return dict(clip=k, n_dups=int(len(dup_idx)), t_release=float(t[rel]), swing_s=float(ts[-1] - ts[0]),
                n_zc=int(len(zc)), T_zc=float(T_zc), T_fit=float(T_fit), R2=float(R2), pc1_var=float(S[0]**2 / (S**2).sum()))
moc = {r['clip']: r for r in json.load(open('mocap_rog2.json'))}
# matched mocap reference: recompute mean period over the first `swing_s` s after release
sys.path.insert(0, '.')
import importlib.util
def mocap_matched(k, dur):
    d = json.load(open(f'../data/gauge/data/rigid/pendulum/json/{k}.json'))
    from mocap_rog2_lib import periods
    te, T = periods(d)
    w = (te[2:] - te[0]) <= dur
    return float(T[w].mean())
out = []
for k in range(1, 21):
    r = analyse(k); r['T_moc_matched'] = mocap_matched(k, r['swing_s'])
    r['ratio_zc'] = r['T_zc'] / r['T_moc_matched']; r['ratio_fit'] = r['T_fit'] / r['T_moc_matched']
    out.append(r); print({a: (round(b, 4) if isinstance(b, float) else b) for a, b in r.items()}, flush=True)
json.dump(out, open('video_rog2.json', 'w'), indent=1)
for key in ['ratio_zc', 'ratio_fit', 'T_moc_matched', 'T_zc']:
    a = np.array([r[key] for r in out]); a = a[np.isfinite(a)]
    print(f'{key}: mean {a.mean():.4f} sd {a.std(ddof=1):.4f} SE {a.std(ddof=1)/np.sqrt(len(a)):.4f} median {np.median(a):.4f} n={len(a)} within1%={np.sum(abs(a-1)<0.01) if key.startswith("ratio") else "-"}')
