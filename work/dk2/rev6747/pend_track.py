"""dk2 independent pendulum-period reader (rev6747). Not derived from pend_acf / measure_pend.
Method: per-pixel temporal median = static background; |frame - bg| > thr gives the moving pixels, restricted to the
largest connected blob of the temporal-std map (the swing corridor); x(t) = diff-weighted centroid column.
Period: (1) damped-sinusoid least-squares fit initialised from a zero-padded FFT peak; (2) independent check from
the median interval between upward mean-crossings (x2 half-period average). flag='ok' if both agree within 5% and fit R2>=0.8.
Usage: python pend_track.py out.json clip1.mp4 [clip2.mp4 ...]   (fps read from the container)"""
import sys, json, cv2, numpy as np
from scipy.optimize import least_squares
from scipy.ndimage import label, binary_dilation


def read(p):
    cap = cv2.VideoCapture(p); fps = cap.get(cv2.CAP_PROP_FPS) or 24.0; F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32))
    return np.stack(F), fps


def track(F):
    F = np.stack([cv2.GaussianBlur(f, (5, 5), 1.5) for f in F])
    bg = np.median(F, 0); D = np.abs(F - bg)
    sd = F.std(0); thr_sd = max(4.0, np.percentile(sd, 99) * 0.3)
    lab, n = label(sd > thr_sd)
    if n == 0: return None
    sizes = np.bincount(lab.ravel())[1:]; roi = binary_dilation(lab == (1 + sizes.argmax()), iterations=8)
    thr = max(12.0, np.percentile(D[:, roi], 90) * 0.5)
    W = np.where((D > thr) & roi[None], D, 0.0); xs = np.arange(F.shape[2])[None, None, :]
    m = W.sum((1, 2)); x = (W * xs).sum((1, 2)) / np.maximum(m, 1e-6)
    x[m < 1e-3] = np.nan
    if np.isnan(x).all(): return None
    t = np.arange(len(x)); ok = ~np.isnan(x); x = np.interp(t, t[ok], x[ok])
    return x, int(roi.sum()), float(np.mean(ok))


def period(x, fps):
    t = np.arange(len(x)) / fps; y = x - np.polyval(np.polyfit(t, x, 1), t)
    nfft = 16 * len(y); f = np.fft.rfftfreq(nfft, 1 / fps); S = np.abs(np.fft.rfft(y * np.hanning(len(y)), nfft))
    band = (f > 1.5 / t[-1]) & (f < fps / 4)  # at least 1.5 cycles in the clip
    if not band.any(): return None
    f0 = f[band][S[band].argmax()]
    def res(p):
        A, g, P, ph, c, d = p
        return A * np.exp(-g * t) * np.cos(2 * np.pi * t / P + ph) + c + d * t - y
    best = None
    for ph in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        r = least_squares(res, [y.std() * 1.4, 0.05, 1 / f0, ph, 0, 0], bounds=([0, -1, 0.5 / f0, -10, -np.inf, -np.inf], [np.inf, 5, 2 / f0, 10, np.inf, np.inf]))
        if best is None or r.cost < best.cost: best = r
    P_fit = float(best.x[2]); R2 = float(1 - 2 * best.cost / max(np.sum((y - y.mean()) ** 2), 1e-9))
    # zero-crossing check (upward crossings of the fitted offset)
    yc = y - (best.x[4] + best.x[5] * t); s = np.sign(yc); up = np.where((s[:-1] < 0) & (s[1:] >= 0))[0]
    # sub-frame interpolation
    tc = [(i + (-yc[i]) / (yc[i + 1] - yc[i])) / fps for i in up]
    P_zc = float(np.median(np.diff(tc))) if len(tc) >= 2 else None
    agree = P_zc is not None and abs(P_zc / P_fit - 1) < 0.05
    return dict(P_fft=float(1 / f0), P_fit=P_fit, R2=R2, P_zc=P_zc, n_cross=len(tc), damping=float(best.x[1]),
                amp_px=float(best.x[0]), flag="ok" if (agree and R2 >= 0.8) else "check")


if __name__ == "__main__":
    out = {}
    for p in sys.argv[2:]:
        F, fps = read(p); tr = track(F); name = p.split("/")[-1].rsplit(".", 1)[0]
        if tr is None: out[name] = dict(flag="fail", fps=fps); continue
        x, roi_px, cover = tr; r = period(x, fps) or dict(flag="fail")
        r.update(fps=fps, frames=len(F), roi_px=roi_px, cover=cover); out[name] = r
        print(name, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}, flush=True)
    json.dump(out, open(sys.argv[1], "w"), indent=1)
