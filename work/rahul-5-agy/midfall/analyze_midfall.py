#!/usr/bin/env python3
import json
import numpy as np
import cv2

def analyze_clip(clip_path, seed_xy, mpp=0.001852538, fps=24.0):
    cap = cv2.VideoCapture(clip_path)
    ret, f0 = cap.read()
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sx, sy = seed_xy
    hw = 14
    tmpl = cv2.cvtColor(f0[sy-hw:sy+hw, sx-hw:sx+hw], cv2.COLOR_BGR2GRAY)

    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    traj = []
    cur_x, cur_y = sx, sy
    for i in range(n_frames):
        ret, fr = cap.read()
        if not ret: break
        gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        x_min = max(0, int(cur_x - 25))
        x_max = min(fr.shape[1], int(cur_x + 25))
        y_min = max(0, int(cur_y - 50))
        y_max = min(fr.shape[0], int(cur_y + 50))
        search = gray[y_min:y_max, x_min:x_max]
        res = cv2.matchTemplate(search, tmpl, cv2.TM_CCOEFF_NORMED)
        min_v, max_v, min_l, max_l = cv2.minMaxLoc(res)
        bx = max_l[0] + x_min + hw
        by = max_l[1] + y_min + hw
        traj.append((i, bx, by, max_v))
        # only update cur position if score is decent or within reasonable range
        if max_v > 0.4:
            cur_x, cur_y = bx, by

    times = np.array([p[0] / fps for p in traj])
    y_px = np.array([p[2] for p in traj])
    y_m = y_px * mpp

    return {
        "clip": clip_path,
        "n_frames": n_frames,
        "fps": fps,
        "mpp": mpp,
        "traj": traj,
        "times": times,
        "y_px": y_px,
        "y_m": y_m
    }

def fit_quadratic(t, y):
    # y = 0.5 * g * t^2 + v0 * t + y0
    A = np.vstack([0.5 * t**2, t, np.ones_like(t)]).T
    sol, residuals, rank, s = np.linalg.lstsq(A, y, rcond=None)
    g, v0, y0 = sol
    # R^2
    y_pred = A @ sol
    r2 = 1.0 - np.sum((y - y_pred)**2) / np.sum((y - np.mean(y))**2)
    return g, v0, y0, r2

if __name__ == "__main__":
    for name, seed in [("20261101T033939_0007_raj-3.mp4", (287, 155)),
                       ("20261101T040234_0012_raj-3.mp4", (290, 172))]:
        res = analyze_clip(f"/home/sha/swarm-work/rahul-5-agy/clips/{name}", seed)
        print(f"\n==========================================")
        print(f"Results for {name}:")
        y_px = res["y_px"]
        fps = res["fps"]
        mpp = res["mpp"]
        t = res["times"]

        # Find impacts (local maxima of y_px)
        # First impact:
        imp1 = np.argmax(y_px[:10])
        print(f"First impact at frame {imp1} (t={t[imp1]:.3f}s), y={y_px[imp1]:.1f}px")

        # Initial fall fit (frames 0 to imp1-1)
        # Note: frame imp1 is contact, drop it
        fall_idx = np.arange(0, imp1)
        t_fall = t[fall_idx]
        y_fall = y_px[fall_idx] * mpp
        g_fall, v0_fall, y0_fall, r2_fall = fit_quadratic(t_fall, y_fall)
        print(f"Initial mid-fall segment (frames 0..{imp1-1}, n={len(fall_idx)}):")
        print(f"  g_fall = {g_fall:.2f} m/s^2, v0 = {v0_fall:.2f} m/s, R^2 = {r2_fall:.4f}")

        # First rebound (from imp1+1 to next impact)
        # Find apex 1: min y between imp1 and imp1+15
        apex1 = imp1 + 1 + np.argmin(y_px[imp1+1:imp1+15])
        print(f"First apex at frame {apex1} (t={t[apex1]:.3f}s), y={y_px[apex1]:.1f}px (rise = {y_px[imp1] - y_px[apex1]:.1f}px = {(y_px[imp1] - y_px[apex1])*mpp*100:.1f}cm)")

        # Second impact:
        imp2 = apex1 + np.argmax(y_px[apex1:apex1+15])
        print(f"Second impact at frame {imp2} (t={t[imp2]:.3f}s), y={y_px[imp2]:.1f}px")

        # Fit rebound 1: flight between imp1 and imp2 (excluding contact frames)
        reb_idx = np.arange(imp1+1, imp2)
        t_reb = t[reb_idx] - t[reb_idx[0]]
        y_reb = y_px[reb_idx] * mpp
        g_reb, v0_reb, y0_reb, r2_reb = fit_quadratic(t_reb, y_reb)
        print(f"First rebound flight (frames {imp1+1}..{imp2-1}, n={len(reb_idx)}):")
        print(f"  g_reb = {g_reb:.2f} m/s^2, v0 = {v0_reb:.2f} m/s, R^2 = {r2_reb:.4f}")
        flight_t1 = (imp2 - imp1) / fps
        print(f"  Flight time T1 = {flight_t1:.3f} s ({imp2 - imp1} frames)")
