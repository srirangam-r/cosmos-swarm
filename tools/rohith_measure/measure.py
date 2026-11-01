"""rohith-cc-1 planted-case measurer: ball free fall (g, e), pendulum (period_s), incline (a).

Approach
- Background = per-pixel median over all frames. Foreground strength d = |frame - bg| (Lab, L2).
- Object = largest connected blob of d > thr; position = d-weighted centroid.
- Scale (px per metre) is measured on frame 0, where the object is at rest (no motion blur),
  using half-max edge crossings of a 1-D profile through the object (sub-pixel).
- Kinematics fit by least squares on t = frame / fps.
"""
from __future__ import annotations

import json
import sys

import cv2
import numpy as np
from scipy.optimize import least_squares


def load(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2LAB).astype(np.float32))
    return np.stack(frames), fps


def diff_stack(F):
    bg = np.median(F, axis=0)
    D = np.sqrt(((F - bg) ** 2).sum(-1))
    D = np.stack([cv2.GaussianBlur(d, (0, 0), 0.7) for d in D])
    return D, bg


def blob(d, thr):
    m = (d > thr).astype(np.uint8)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n <= 1:
        return None
    k = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    mk = lab == k
    mk = cv2.dilate(mk.astype(np.uint8), np.ones((5, 5), np.uint8)).astype(bool)
    return mk


def body_level(d, mk):
    return float(np.median(d[mk & (d > THR)]))


def centroid(d, mk, thr):
    lv = body_level(d, mk)
    w = np.where(mk, np.clip(d / lv, 0, 1), 0)  # saturating: highlights don't bias it
    ys, xs = np.mgrid[: d.shape[0], : d.shape[1]]
    s = w.sum()
    return (xs * w).sum() / s, (ys * w).sum() / s


def track(D, thr):
    pts = []
    H, W = D.shape[1:]
    for d in D:
        mk = blob(d, thr)
        if mk is None:
            pts.append((np.nan, np.nan)); continue
        ys, xs = np.where(mk)
        if ys.min() <= 1 or xs.min() <= 1 or ys.max() >= H - 2 or xs.max() >= W - 2:
            pts.append((np.nan, np.nan)); continue  # touching the frame edge: centroid biased
        pts.append(centroid(d, mk, thr))
    return np.array(pts)


def hm_width(profile, level):
    """Distance between outermost crossings of `level` (= half the object's body contrast),
    linear sub-pixel interpolation."""
    p = np.asarray(profile, float)
    above = np.where(p > level)[0]
    l, r = above[0], above[-1]
    xl = (l - 1) + (level - p[l - 1]) / (p[l] - p[l - 1])
    xr = r + (p[r] - level) / (p[r] - p[r + 1])
    return xr - xl


def sample_line(img, c, u, half):
    s = np.arange(-half, half + 1, 0.25)
    xs = c[0] + s * u[0]
    ys = c[1] + s * u[1]
    v = cv2.remap(img, xs.astype(np.float32)[None], ys.astype(np.float32)[None], cv2.INTER_LINEAR)[0]
    return s, v


def chord(d0, c, u, level, half=40):
    s, v = sample_line(d0, c, u, half)
    return hm_width(v, level) * 0.25


def ball_diameter_px(d0, c):
    """Median of half-level chords through the centroid at several angles."""
    lv = 0.5 * body_level(d0, blob(d0, THR))
    ws = [chord(d0, c, (np.cos(a), np.sin(a)), lv) for a in np.linspace(0, np.pi, 12, endpoint=False)]
    return float(np.median(ws)), ws


THR = 12.0


def thr_for(D):
    return THR


# ---------------------------------------------------------------- ball
def fit_ball(path, diam_m, want_e):
    F, fps = load(path)
    D, _ = diff_stack(F)
    thr = thr_for(D)
    P = track(D, thr)
    dpx, _ = ball_diameter_px(D[0], P[0])
    ppm = dpx / diam_m
    t = np.arange(len(P)) / fps
    y = P[:, 1]
    ok = ~np.isnan(y)
    # first impact: first local max of y (y grows downward)
    vy = np.gradient(y)
    imp = None
    for i in range(2, len(y) - 1):
        if ok[i] and vy[i - 1] > 0 and vy[i + 1] < 0 and y[i] >= y[i - 1] and y[i] >= y[i + 1]:
            imp = i
            break
    end = imp - 1 if imp is not None else len(y)
    seg = np.arange(0, end)
    seg = seg[ok[seg]]
    c = np.polyfit(t[seg], y[seg], 2)
    # v4: trim trailing outliers (ball merging with floor/shadow just before contact)
    while len(seg) > 6:
        r = np.abs(np.polyval(c, t[seg]) - y[seg])
        if r[-1] > max(0.5, 4 * np.median(r)):
            seg = seg[:-1]
            c = np.polyfit(t[seg], y[seg], 2)
        else:
            break
    g = 2 * c[0] / ppm
    rms = float(np.sqrt(np.mean((np.polyval(c, t[seg]) - y[seg]) ** 2)))
    c0 = np.polyfit(t[seg] ** 2, y[seg] - y[seg][0] * 0, 1)  # v0 = 0 variant
    A = np.vstack([t[seg] ** 2, np.ones_like(t[seg])]).T
    g_rest = 2 * np.linalg.lstsq(A, y[seg], rcond=None)[0][0] / ppm
    out = {"g": float(g), "_g_v0fixed": float(g_rest), "_rms_px": rms, "_last_frame": int(seg[-1]), "_ppm": ppm, "_dpx": dpx, "_v0_mps": float(c[1] / ppm), "_n_fall": int(len(seg)), "_impact_frame": imp}
    if want_e and imp is not None:
        # second segment: after impact until next impact
        j0 = imp + 1
        j1 = None
        for i in range(j0 + 2, len(y) - 1):
            if vy[i - 1] > 0 and vy[i + 1] < 0 and y[i] >= y[i - 1] and y[i] >= y[i + 1]:
                j1 = i
                break
        seg2 = np.arange(j0, (j1 - 1) if j1 else len(y))
        seg2 = seg2[ok[seg2]]
        # joint fit: shared curvature g, floor contact height yf, impact time ti, e
        a = c[0]
        c2 = np.polyfit(t[seg2], y[seg2], 2)

        def model(p, tt, which):
            ti, yf, e, aa = p
            vin = 2 * aa * 0  # placeholder
            return None

        # simpler: contact height = where both parabolas meet; use fitted pre-impact parabola
        # with curvature a, and post-impact parabola with curvature fixed to a.
        A = np.vstack([t[seg2], np.ones_like(t[seg2])]).T
        rhs = y[seg2] - a * t[seg2] ** 2
        b2, c2c = np.linalg.lstsq(A, rhs, rcond=None)[0]
        p1 = np.array([a, c[1], c[2]])
        p2 = np.array([a, b2, c2c])
        # intersection: (p1-p2)·[t^2,t,1]=0 -> linear in t
        ti = -(p1[2] - p2[2]) / (p1[1] - p2[1])
        vin = 2 * a * ti + p1[1]
        vout = 2 * a * ti + p2[1]
        e = -vout / vin
        out.update({"e": float(e), "_t_impact": float(ti), "_n_bounce": int(len(seg2))})
    return out, P


# ---------------------------------------------------------------- pendulum
def fit_pendulum(path):
    F, fps = load(path)
    D, _ = diff_stack(F)
    thr = thr_for(D)
    P = track(D, thr)
    t = np.arange(len(P)) / fps
    x = P[:, 0] - np.nanmean(P[:, 0])
    ok = ~np.isnan(x)
    t, x = t[ok], x[ok]
    # initial period from zero crossings
    zc = []
    for i in range(len(x) - 1):
        if x[i] == 0 or x[i] * x[i + 1] < 0:
            zc.append(t[i] + (t[i + 1] - t[i]) * x[i] / (x[i] - x[i + 1]))
    T0 = 2 * np.mean(np.diff(zc)) if len(zc) > 2 else 1.5

    def res(p):
        A, g, w, ph, c = p
        return A * np.exp(-g * t) * np.cos(w * t + ph) + c - x

    A0 = np.abs(x).max()
    best = None
    for ph in np.linspace(0, 2 * np.pi, 8, endpoint=False):
        w0 = 2 * np.pi / T0
        r = least_squares(res, [A0, 0.0, w0, ph, 0.0],
                          bounds=([0, -1, 0.7 * w0, -10, -1e3], [1e4, 5, 1.3 * w0, 20, 1e3]))
        if best is None or r.cost < best.cost:
            best = r
    T = 2 * np.pi / best.x[2]
    return {"period_s": float(abs(T)), "_T_zc": float(T0), "_n_zc": len(zc), "_rms_px": float(np.sqrt(2 * best.cost / len(t)))}, P


# ---------------------------------------------------------------- incline
def fit_incline(path, length_m):
    F, fps = load(path)
    D, _ = diff_stack(F)
    thr = thr_for(D)
    P = track(D, thr)
    ok = ~np.isnan(P[:, 0])
    Q = P[ok]
    t = (np.arange(len(P)) / fps)[ok]
    # slope direction from trajectory (PCA)
    Qc = Q - Q.mean(0)
    _, _, vt = np.linalg.svd(Qc, full_matrices=False)
    u = vt[0]
    if np.dot(Q[-1] - Q[0], u) < 0:
        u = -u
    s = (Q - Q[0]) @ u
    # block length along slope from frame 0 (at rest): half-max of profile summed across the block
    d0 = D[0]
    c = P[0]
    nrm = np.array([-u[1], u[0]])
    lv = 0.5 * body_level(d0, blob(d0, THR))
    # chords along the slope at several offsets across the block's thickness; take the median
    Ls = [chord(d0, c + off * nrm, u, lv, 60) for off in np.linspace(-2, 2, 9)]
    Lpx_sum = float(np.max(Ls))
    Lpx_c = float(np.median(Ls))
    Lpx = Lpx_c
    ppm = Lpx / length_m
    # fit s = s0 + v0 t + 0.5 a t^2 over moving part; exclude frames after it stops/leaves
    vs = np.gradient(s)
    # stop if it reaches the bottom: velocity drops sharply
    end = len(s)
    for i in range(5, len(s) - 1):
        if vs[i] < 0.5 * vs[i - 1] and vs[i - 1] > 1:
            end = i
            break
    k = np.arange(end)
    cf = np.polyfit(t[k], s[k], 2)
    a = 2 * cf[0] / ppm
    return {"a": float(a), "_ppm": ppm, "_Lpx_c": float(Lpx_c), "_Lpx_sum": float(Lpx_sum), "_angle_deg": float(np.degrees(np.arctan2(u[1], u[0]))), "_n": int(end), "_v0": float(cf[1] / ppm)}, P


def main(index_path, clip_dir):
    idx = json.load(open(index_path))
    est, dbg = {}, {}
    for c in idx["clips"]:
        cid, notes, params = c["clip_id"], c["notes"], c["params"]
        path = f"{clip_dir}/{cid}.mp4"
        if "pendulum" in notes:
            r, _ = fit_pendulum(path)
        elif "incline" in notes:
            r, _ = fit_incline(path, 0.12 if "0.12" in notes else float(notes.split("slope ")[1].split(" m")[0]))
        else:
            import re
            dm = float(re.search(r"diameter ([0-9.]+) m", notes).group(1))
            r, _ = fit_ball(path, dm, "e" in params)
        est[cid] = {p: r[p] for p in params}
        dbg[cid] = r
        print(cid, json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()}))
    return est, dbg


if __name__ == "__main__":
    est, dbg = main(sys.argv[1], sys.argv[2])
    json.dump({"estimates": est, "debug": dbg}, open(sys.argv[3], "w"), indent=1)
