#!/usr/bin/env python3
"""Task 71 Analysis Script:
Does guidance scale (CFG) or flow shift control Nano's undamped bounce (e_T) and allow settling to rest?
Evaluates 12 clips across 6 conditions x seeds 1-2 on real GAUGE ball 1 mid-fall:
1. cfg6p0_shift10p0 (Default baseline)
2. cfg4p0_shift10p0
3. cfg2p5_shift10p0
4. cfg1p0_shift10p0 (Unguided)
5. cfg3p0_shift5p0  (MSRA / Physics-IQ optimal)
6. cfg6p0_shift3p0  (Low flow shift)
"""

import os, sys, json
import cv2, numpy as np
from scipy.signal import find_peaks
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

MPP = 0.001852538  # 539.8 px/m for GAUGE ball 1
FPS = 24.0

CONDITIONS = [
    ("cfg6p0_shift10p0", 6.0, 10.0, "CFG 6.0, Shift 10.0 (Baseline)"),
    ("cfg4p0_shift10p0", 4.0, 10.0, "CFG 4.0, Shift 10.0"),
    ("cfg2p5_shift10p0", 2.5, 10.0, "CFG 2.5, Shift 10.0"),
    ("cfg1p0_shift10p0", 1.0, 10.0, "CFG 1.0, Shift 10.0 (Unguided)"),
    ("cfg3p0_shift5p0",  3.0,  5.0, "CFG 3.0, Shift 5.0 (MSRA)"),
    ("cfg6p0_shift3p0",  6.0,  3.0, "CFG 6.0, Shift 3.0 (Low Shift)")
]

def analyze_trajectory(clip_path, seed_xy=(285, 150), hw=12):
    cap = cv2.VideoCapture(clip_path)
    ret, f0 = cap.read()
    if not ret:
        cap.release()
        return None
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    sx, sy = seed_xy
    gray0 = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
    tmpl = gray0[max(0, sy-hw):min(f0.shape[0], sy+hw+1), max(0, sx-hw):min(f0.shape[1], sx+hw+1)]
    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    traj = []
    cur_x, cur_y = sx, sy
    for i in range(n_frames):
        ret, fr = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY)
        x_min = max(220, int(cur_x - 35))
        x_max = min(360, int(cur_x + 35))
        y_min = max(110, int(cur_y - 65))
        y_max = min(365, int(cur_y + 65))
        search = gray[y_min:y_max, x_min:x_max]
        res = cv2.matchTemplate(search, tmpl, cv2.TM_CCOEFF_NORMED)
        min_v, max_v, min_l, max_l = cv2.minMaxLoc(res)
        bx = max_l[0] + x_min + hw
        by = max_l[1] + y_min + hw
        traj.append((i, bx, by, max_v))
        if max_v > 0.35:
            cur_x, cur_y = bx, by
    cap.release()
    return traj

def fit_quadratic(t, y):
    # y = 0.5 * g * t^2 + v0 * t + y0
    A = np.vstack([0.5 * t**2, t, np.ones_like(t)]).T
    sol, residuals, rank, s = np.linalg.lstsq(A, y, rcond=None)
    g, v0, y0 = sol
    y_pred = A @ sol
    ss_tot = np.sum((y - np.mean(y))**2)
    r2 = 1.0 - (np.sum((y - y_pred)**2) / ss_tot) if ss_tot > 0 else 0.0
    return g, v0, y0, r2

def process_clip(clip_path, name, cond_key, cfg, shift, seed):
    traj = analyze_trajectory(clip_path)
    if traj is None or len(traj) < 10:
        return None
    
    frames = np.array([p[0] for p in traj])
    times = frames / FPS
    xs = np.array([p[1] for p in traj])
    ys = np.array([p[2] for p in traj])
    scores = np.array([p[3] for p in traj])
    
    # Impacts on the plank
    pks, _ = find_peaks(ys, prominence=10, distance=4)
    plank_pks = [p for p in pks if ys[p] > 300]
    
    # First fall segment
    first_imp = plank_pks[0] if len(plank_pks) > 0 else None
    g_fall, v0_fall, r2_fall = None, None, None
    if first_imp is not None and first_imp >= 3:
        fall_idx = np.arange(0, first_imp)
        t_f = times[fall_idx]
        y_f = ys[fall_idx] * MPP
        g_fall, v0_fall, y0_f, r2_fall = fit_quadratic(t_f, y_f)
    
    # Bounces analysis
    flights_fr = []
    flights_s = []
    rises_px = []
    rises_cm = []
    apexes_fr = []
    apexes_y = []
    
    for i in range(len(plank_pks) - 1):
        p1 = plank_pks[i]
        p2 = plank_pks[i+1]
        T_fr = p2 - p1
        sub_y = ys[p1:p2+1]
        apex_offset = np.argmin(sub_y)
        apex_fr = p1 + apex_offset
        rise_px = max(ys[p1], ys[p2]) - ys[apex_fr]
        
        flights_fr.append(int(T_fr))
        flights_s.append(float(T_fr / FPS))
        rises_px.append(float(rise_px))
        rises_cm.append(float(rise_px * MPP * 100))
        apexes_fr.append(int(apex_fr))
        apexes_y.append(float(ys[apex_fr]))
    
    # Restitution metrics
    e_T_ratios = []
    for i in range(len(flights_s) - 1):
        if flights_s[i] > 0:
            e_T_ratios.append(flights_s[i+1] / flights_s[i])
            
    e_h_ratios = []
    for i in range(len(rises_cm) - 1):
        if rises_cm[i] > 0 and rises_cm[i+1] > 0:
            e_h_ratios.append(np.sqrt(rises_cm[i+1] / rises_cm[i]))
            
    mean_e_T = float(np.mean(e_T_ratios)) if e_T_ratios else None
    se_e_T = float(np.std(e_T_ratios) / np.sqrt(len(e_T_ratios))) if len(e_T_ratios) > 1 else 0.0
    
    mean_e_h = float(np.mean(e_h_ratios)) if e_h_ratios else None
    se_e_h = float(np.std(e_h_ratios) / np.sqrt(len(e_h_ratios))) if len(e_h_ratios) > 1 else 0.0
    
    # Log-linear fit on flight times
    e_T_log = None
    if len(flights_s) >= 3:
        k_indices = np.arange(len(flights_s))
        ln_T = np.log(np.array(flights_s) + 1e-6)
        slope, intercept = np.polyfit(k_indices, ln_T, 1)
        e_T_log = float(np.exp(slope))
    elif len(flights_s) == 2:
        e_T_log = float(flights_s[1] / flights_s[0])
    
    # Settle detection
    # Ball comes to rest if in a late window (>= 10 frames), y stays > 310 and max(y) - min(y) < 4 px
    settled = False
    settle_frame = None
    settle_time = None
    for f in range(20, len(ys) - 12):
        window = ys[f:f+12]
        if np.mean(window) > 310 and (np.max(window) - np.min(window)) < 4.0:
            settled = True
            settle_frame = int(f)
            settle_time = float(f / FPS)
            break
            
    still_bouncing = (len(plank_pks) >= 3 and plank_pks[-1] > 70 and not settled)
    
    return {
        "name": name,
        "cond": cond_key,
        "cfg": cfg,
        "shift": shift,
        "seed": seed,
        "n_frames": len(ys),
        "mean_score": float(np.mean(scores)),
        "min_score": float(np.min(scores)),
        "first_imp_fr": int(first_imp) if first_imp is not None else None,
        "first_imp_s": float(first_imp / FPS) if first_imp is not None else None,
        "g_fall": float(g_fall) if g_fall is not None else None,
        "v0_fall": float(v0_fall) if v0_fall is not None else None,
        "r2_fall": float(r2_fall) if r2_fall is not None else None,
        "n_impacts": len(plank_pks),
        "impact_frames": [int(p) for p in plank_pks],
        "flights_fr": flights_fr,
        "flights_s": flights_s,
        "rises_px": rises_px,
        "rises_cm": rises_cm,
        "apexes_fr": apexes_fr,
        "apexes_y": apexes_y,
        "e_T_ratios": [float(x) for x in e_T_ratios],
        "mean_e_T": mean_e_T,
        "se_e_T": se_e_T,
        "mean_e_h": mean_e_h,
        "se_e_h": se_e_h,
        "e_T_log": e_T_log,
        "settled": bool(settled),
        "settle_frame": settle_frame,
        "settle_time": settle_time,
        "still_bouncing": bool(still_bouncing),
        "traj_y": [float(y) for y in ys],
        "traj_x": [float(x) for x in xs],
        "scores": [float(s) for s in scores]
    }

def main():
    clips_dir = "/home/sha/swarm-work/rahul-5-agy/task71_cfg_shift/clips"
    results = []
    
    for cond_key, cfg, shift, desc in CONDITIONS:
        for seed in [1, 2]:
            clip_name = f"{cond_key}_s{seed}.mp4"
            clip_path = os.path.join(clips_dir, clip_name)
            if not os.path.exists(clip_path):
                print(f"[WAITING] Missing {clip_name}")
                continue
            print(f"[ANALYZING] {clip_name} ({desc})...")
            res = process_clip(clip_path, f"{cond_key}_s{seed}", cond_key, cfg, shift, seed)
            if res:
                results.append(res)
                print(f"  -> g_fall: {res['g_fall']:.2f} m/s^2 (R2={res['r2_fall']:.4f})" if res['g_fall'] else "  -> No clean first fall")
                print(f"  -> {res['n_impacts']} impacts, {len(res['flights_s'])} flights")
                print(f"  -> mean e_T: {res['mean_e_T']:.3f} +/- {res['se_e_T']:.3f}, e_T_log: {res['e_T_log']:.3f}" if res['mean_e_T'] else "  -> e_T: N/A")
                print(f"  -> Settled? {res['settled']} (settle frame: {res['settle_frame']}), Still bouncing at end? {res['still_bouncing']}")
                print(f"  -> Tracking score: mean {res['mean_score']:.3f}, min {res['min_score']:.3f}")

    out_json = "/home/sha/swarm-work/rahul-5-agy/task71_cfg_shift/task71_results.json"
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved {len(results)} clip results to {out_json}")

    # Plot multi-condition comparison figure
    if results:
        plt.figure(figsize=(16, 12))
        
        # Subplot 1: Vertical Trajectories y(t)
        plt.subplot(2, 2, 1)
        colors = {
            "cfg6p0_shift10p0": "#d62728", # red
            "cfg4p0_shift10p0": "#ff7f0e", # orange
            "cfg2p5_shift10p0": "#2ca02c", # green
            "cfg1p0_shift10p0": "#1f77b4", # blue
            "cfg3p0_shift5p0":  "#9467bd", # purple
            "cfg6p0_shift3p0":  "#8c564b"  # brown
        }
        
        for r in results:
            t = np.arange(len(r["traj_y"])) / FPS
            ls = "-" if r["seed"] == 1 else "--"
            label = f"{r['cond']} (s{r['seed']})"
            plt.plot(t, r["traj_y"], label=label, color=colors.get(r["cond"], "gray"), linestyle=ls, alpha=0.85)
            
        plt.axhline(335, color="black", linestyle=":", label="Plank Surface (~335px)")
        plt.gca().invert_yaxis()
        plt.title("Ball Trajectory y(t): CFG & Flow Shift Sweep", fontsize=13, fontweight="bold")
        plt.xlabel("Time (s)", fontsize=11)
        plt.ylabel("Vertical Position (px, inverted)", fontsize=11)
        plt.legend(fontsize=8, loc="lower right", ncol=2)
        plt.grid(True, alpha=0.3)
        
        # Subplot 2: Flight-Time Decay Across Bounces
        plt.subplot(2, 2, 2)
        for r in results:
            if len(r["flights_s"]) >= 2:
                b_nums = np.arange(1, len(r["flights_s"]) + 1)
                ls = "-" if r["seed"] == 1 else "--"
                plt.plot(b_nums, r["flights_s"], marker="o", label=f"{r['cond']} s{r['seed']}", color=colors.get(r["cond"], "gray"), linestyle=ls)
                
        # Real GAUGE flight times reference
        # Real GAUGE ball 1 has flight times: ~0.33s, 0.23s, 0.16s, 0.11s, settled at 1.4s
        real_flights = [0.333, 0.233, 0.162, 0.112]
        plt.plot(np.arange(1, len(real_flights)+1), real_flights, marker="s", color="black", linewidth=2.5, linestyle="-", label="Real GAUGE Ball 1 (Restitution e~0.69)")
        plt.title("Bounce Flight Duration T_k (s) Across Successive Bounces", fontsize=13, fontweight="bold")
        plt.xlabel("Bounce Index k", fontsize=11)
        plt.ylabel("Flight Duration T_k (s)", fontsize=11)
        plt.legend(fontsize=8, loc="upper right", ncol=2)
        plt.grid(True, alpha=0.3)
        
        # Subplot 3: Bar chart of Restitution e_T across conditions
        plt.subplot(2, 2, 3)
        cond_names = [c[0] for c in CONDITIONS]
        cond_labels = ["CFG 6\nShift 10\n(Default)", "CFG 4\nShift 10", "CFG 2.5\nShift 10", "CFG 1.0\nShift 10\n(Unguided)", "CFG 3\nShift 5\n(MSRA)", "CFG 6\nShift 3\n(Low Shift)"]
        
        e_T_means = []
        e_T_errs = []
        for c in cond_names:
            c_res = [r for r in results if r["cond"] == c and r["mean_e_T"] is not None]
            if c_res:
                vals = [r["mean_e_T"] for r in c_res]
                e_T_means.append(np.mean(vals))
                e_T_errs.append(np.std(vals) if len(vals) > 1 else 0.0)
            else:
                e_T_means.append(0.0)
                e_T_errs.append(0.0)
                
        x_pos = np.arange(len(cond_names))
        plt.bar(x_pos, e_T_means, yerr=e_T_errs, capsize=5, color=[colors[c] for c in cond_names], alpha=0.85, edgecolor="black")
        plt.axhline(1.0, color="red", linestyle="--", label="Elastic Limit (e = 1.0, No Decay)")
        plt.axhline(0.693, color="green", linestyle="--", label="Real GAUGE Mocap (e = 0.693)")
        plt.xticks(x_pos, cond_labels, fontsize=9)
        plt.ylabel("Restitution Coefficient e_T", fontsize=11)
        plt.title("Mean Flight-Time Restitution e_T by Condition", fontsize=13, fontweight="bold")
        plt.ylim(0.0, 1.25)
        plt.legend(fontsize=9, loc="lower right")
        plt.grid(True, alpha=0.3, axis="y")
        
        # Subplot 4: Initial Fall Gravity g (m/s²)
        plt.subplot(2, 2, 4)
        g_means = []
        g_errs = []
        for c in cond_names:
            c_res = [r for r in results if r["cond"] == c and r["g_fall"] is not None]
            if c_res:
                vals = [r["g_fall"] for r in c_res]
                g_means.append(np.mean(vals))
                g_errs.append(np.std(vals) if len(vals) > 1 else 0.0)
            else:
                g_means.append(0.0)
                g_errs.append(0.0)
                
        plt.bar(x_pos, g_means, yerr=g_errs, capsize=5, color=[colors[c] for c in cond_names], alpha=0.85, edgecolor="black")
        plt.axhline(9.81, color="green", linestyle="--", label="Physical Earth Gravity (9.81 m/s²)")
        plt.axhline(0.45, color="red", linestyle="--", label="GAUGE Held-Ball Benchmark (0.45 m/s²)")
        plt.xticks(x_pos, cond_labels, fontsize=9)
        plt.ylabel("Measured Free-Fall g (m/s²)", fontsize=11)
        plt.title("Initial Free-Fall Gravity g by Condition", fontsize=13, fontweight="bold")
        plt.ylim(0.0, 13.0)
        plt.legend(fontsize=9, loc="upper right")
        plt.grid(True, alpha=0.3, axis="y")
        
        plt.tight_layout()
        plot_path = "/home/sha/swarm-work/rahul-5-agy/task71_cfg_shift/task71_cfg_flow_comparison.png"
        plt.savefig(plot_path, dpi=200)
        plt.close()
        print(f"Saved comparison figure to {plot_path}")

if __name__ == "__main__":
    main()
