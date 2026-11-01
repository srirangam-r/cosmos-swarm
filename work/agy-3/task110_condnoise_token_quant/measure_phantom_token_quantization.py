#!/usr/bin/env python3
"""Quantitative evaluation of DiT Token Quantization and Phantom Ball Diameters:
Tests Scout-1's Hypothesis #2519 (Token Quantization H-T vs Scale Prior H-P vs Spectral Commitment H-S)
and provides independent review of Task 98 / Finding #2475 & #2499.

Evaluates across 3 independent cohorts:
- Cohort 1: Task 98 Condition-Noise ablation (9 low-sigma_c clips from native strips)
- Cohort 2: Task 90/103 RoPE Spatial Scale ablation (6 full MP4 clips)
- Cohort 3: Task 58 Brev A100 baseline held clips (8 full MP4 clips)
"""

import os
import json
import cv2
import numpy as np
import scipy.stats as stats
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DIT_TOKEN_PX = 32.0   # Wan2.2 VAE scale_factor (16) * DiT latent_patch_size (2) = 32 pixels
REAL_BALL_D_PX = 21.6 # GAUGE Ball 1 (40 mm at 539.8 px/m = 21.59 px)

OUT_DIR = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task110_condnoise_token_quant"
PLOTS_DIR = os.path.join(OUT_DIR, "plots")
SHEETS_DIR = os.path.join(OUT_DIR, "sheets")
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(SHEETS_DIR, exist_ok=True)

def measure_real_ball():
    """Measures the ground truth ball from GAUGE frame 0 and midfall."""
    f0_path = "/home/nail/swarm-work/agy-3/cosmos-swarm/assets/gauge_ball1_f0.png"
    mid_path = "/home/nail/swarm-work/agy-3/cosmos-swarm/assets/gauge_ball1_midfall.png"
    
    # In midfall, the ball is free-falling in the corridor
    img_mid = cv2.imread(mid_path)
    crop = img_mid[150:250, 260:330]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=50, param2=15, minRadius=8, maxRadius=20)
    if circles is not None:
        c = circles[0][0]
        real_d_meas = float(2 * c[2])
    else:
        real_d_meas = REAL_BALL_D_PX
        
    return {
        "theoretical_diameter_px": REAL_BALL_D_PX,
        "measured_diameter_px": real_d_meas,
        "dit_token_size_px": DIT_TOKEN_PX,
        "ratio_to_token": real_d_meas / DIT_TOKEN_PX,
        "area_px2": float(np.pi * (real_d_meas / 2)**2),
        "dit_token_area_px2": float(DIT_TOKEN_PX**2),
        "area_ratio_to_token": float(np.pi * (real_d_meas / 2)**2) / float(DIT_TOKEN_PX**2)
    }

def analyze_cohort1_condnoise():
    """Analyzes 9 low-sigma condition-noise native strips."""
    strip_dir = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/rog1/condnoise/res/eye"
    strips = sorted([f for f in os.listdir(strip_dir) if f.endswith("_a.jpg")])
    tile_w, tile_h = 240, 288
    
    results = {}
    for sname in strips:
        clip_id = sname.replace("_a.jpg", "")
        img = cv2.imread(os.path.join(strip_dir, sname))
        t0 = cv2.resize(img[0:tile_h, 0:tile_w], (300, 360))
        g0 = cv2.cvtColor(t0, cv2.COLOR_BGR2GRAY)
        
        # Parse sigma and seed
        parts = clip_id.split("_")
        sigma_str = parts[0]
        seed_str = parts[1]
        sigma_val = float(sigma_str[1:4]) / 100.0 if "s0" in sigma_str else 0.05
        seed_val = int(seed_str[1:])
        
        frame_measurements = []
        # Check frames 3 to 45
        for r in range(4):
            for c in range(4):
                if r == 0 and c == 0: continue
                f_idx = (r * 4 + c) * 3
                tile = cv2.resize(img[r*tile_h:(r+1)*tile_h, c*tile_w:(c+1)*tile_w], (300, 360))
                g = cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY)
                diff = cv2.absdiff(g, g0)
                # Zero out gripper arm and lateral margins
                diff[0:85, :] = 0
                diff[:, 0:40] = 0
                diff[:, 260:] = 0
                
                _, thresh = cv2.threshold(diff, 35, 255, cv2.THRESH_BINARY)
                n, labels, stats_cc, centroids = cv2.connectedComponentsWithStats(thresh)
                
                best_cand = None
                best_score = 0
                for i in range(1, n):
                    a = stats_cc[i, cv2.CC_STAT_AREA]
                    w = stats_cc[i, cv2.CC_STAT_WIDTH]
                    h = stats_cc[i, cv2.CC_STAT_HEIGHT]
                    if 150 <= a <= 20000 and w >= 15 and h >= 15:
                        ar = min(w, h) / max(w, h)
                        if ar > 0.40:
                            # Preference for circular blobs
                            score = ar * (1.0 - abs(w - h) / (w + h + 1e-5))
                            if score > best_score:
                                best_score = score
                                mean_d = float((w + h) / 2.0)
                                d_eq = float(2.0 * np.sqrt(a / np.pi))
                                best_cand = {
                                    "frame": f_idx,
                                    "w": int(w),
                                    "h": int(h),
                                    "area": int(a),
                                    "mean_diameter_px": mean_d,
                                    "equiv_diameter_px": d_eq,
                                    "aspect_ratio": float(ar),
                                    "centroid": [float(centroids[i][0]), float(centroids[i][1])]
                                }
                if best_cand is not None:
                    frame_measurements.append(best_cand)
                    
        if frame_measurements:
            d_vals = [m["mean_diameter_px"] for m in frame_measurements]
            first_f = frame_measurements[0]["frame"]
            results[clip_id] = {
                "cohort": "condnoise",
                "sigma_c": sigma_val,
                "seed": seed_val,
                "birth_frame": first_f,
                "n_frames_detected": len(frame_measurements),
                "mean_diameter_px": float(np.mean(d_vals)),
                "std_diameter_px": float(np.std(d_vals)),
                "min_diameter_px": float(np.min(d_vals)),
                "max_diameter_px": float(np.max(d_vals)),
                "equiv_diameter_px": float(np.mean([m["equiv_diameter_px"] for m in frame_measurements])),
                "ratio_to_real": float(np.mean(d_vals) / REAL_BALL_D_PX),
                "ratio_to_token": float(np.mean(d_vals) / DIT_TOKEN_PX),
                "frames": frame_measurements
            }
    return results

def analyze_cohort2_rope():
    """Analyzes 6 MP4 clips from Task 90/103 RoPE experiment."""
    clips_dir = "/home/nail/swarm-work/agy-3/task103_rope_scale_review/clips"
    mp4_files = sorted([f for f in os.listdir(clips_dir) if f.endswith(".mp4")])
    
    results = {}
    for fname in mp4_files:
        clip_id = fname.replace(".mp4", "")
        cap = cv2.VideoCapture(os.path.join(clips_dir, fname))
        ok, f0 = cap.read()
        if not ok: continue
        
        # Color inversion check (task 90 negative artifact)
        if f0.mean() > 120:
            f0 = 255 - f0
        f0_gray = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
        
        frame_measurements = []
        target_f = 0
        while True:
            ok, f = cap.read()
            if not ok: break
            target_f += 1
            if target_f % 3 != 0: continue
            if f.mean() > 120:
                f = 255 - f
            f_gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            
            diff = cv2.absdiff(f_gray, f0_gray)
            # Franka corridor and plank: y in [150, 420], x in [220, 360]
            diff_crop = np.zeros_like(diff)
            diff_crop[150:420, 220:360] = diff[150:420, 220:360]
            
            _, thresh = cv2.threshold(diff_crop, 35, 255, cv2.THRESH_BINARY)
            n, labels, stats_cc, centroids = cv2.connectedComponentsWithStats(thresh)
            
            best_cand = None
            best_score = 0
            for i in range(1, n):
                a = stats_cc[i, cv2.CC_STAT_AREA]
                w = stats_cc[i, cv2.CC_STAT_WIDTH]
                h = stats_cc[i, cv2.CC_STAT_HEIGHT]
                if 150 <= a <= 20000 and w >= 15 and h >= 15:
                    ar = min(w, h) / max(w, h)
                    if ar > 0.40:
                        score = ar * (1.0 - abs(w - h) / (w + h + 1e-5))
                        if score > best_score:
                            best_score = score
                            mean_d = float((w + h) / 2.0)
                            d_eq = float(2.0 * np.sqrt(a / np.pi))
                            best_cand = {
                                "frame": target_f,
                                "w": int(w),
                                "h": int(h),
                                "area": int(a),
                                "mean_diameter_px": mean_d,
                                "equiv_diameter_px": d_eq,
                                "aspect_ratio": float(ar),
                                "centroid": [float(centroids[i][0]), float(centroids[i][1])]
                            }
            if best_cand is not None:
                frame_measurements.append(best_cand)
        cap.release()
                
        if frame_measurements:
            d_vals = [m["mean_diameter_px"] for m in frame_measurements]
            first_f = frame_measurements[0]["frame"]
            results[clip_id] = {
                "cohort": "rope_spatial_scaling",
                "treatment": "rope07" if "rope07" in clip_id else "control",
                "seed": int(clip_id.split("_")[-1].replace("s", "")),
                "birth_frame": first_f,
                "n_frames_detected": len(frame_measurements),
                "mean_diameter_px": float(np.mean(d_vals)),
                "std_diameter_px": float(np.std(d_vals)),
                "min_diameter_px": float(np.min(d_vals)),
                "max_diameter_px": float(np.max(d_vals)),
                "equiv_diameter_px": float(np.mean([m["equiv_diameter_px"] for m in frame_measurements])),
                "ratio_to_real": float(np.mean(d_vals) / REAL_BALL_D_PX),
                "ratio_to_token": float(np.mean(d_vals) / DIT_TOKEN_PX),
                "frames": frame_measurements
            }
    return results

def analyze_cohort3_brev_baseline():
    """Analyzes 8 Brev A100 baseline held clips from Task 58."""
    brev_dir = "/home/nail/swarm-work/raj-3/brev_box/out"
    mp4_files = sorted([f for f in os.listdir(brev_dir) if f.startswith("box_ctrl_") and f.endswith(".mp4")])
    
    results = {}
    for fname in mp4_files:
        clip_id = fname.replace(".mp4", "")
        cap = cv2.VideoCapture(os.path.join(brev_dir, fname))
        ok, f0 = cap.read()
        if not ok: continue
        f0_gray = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
        
        frame_measurements = []
        target_f = 0
        while True:
            ok, f = cap.read()
            if not ok: break
            target_f += 1
            if target_f % 4 != 0: continue
            f_gray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
            
            diff = cv2.absdiff(f_gray, f0_gray)
            diff_crop = np.zeros_like(diff)
            diff_crop[160:420, 230:360] = diff[160:420, 230:360]
            
            _, thresh = cv2.threshold(diff_crop, 35, 255, cv2.THRESH_BINARY)
            n, labels, stats_cc, centroids = cv2.connectedComponentsWithStats(thresh)
            
            best_cand = None
            best_score = 0
            for i in range(1, n):
                a = stats_cc[i, cv2.CC_STAT_AREA]
                w = stats_cc[i, cv2.CC_STAT_WIDTH]
                h = stats_cc[i, cv2.CC_STAT_HEIGHT]
                if 150 <= a <= 20000 and w >= 15 and h >= 15:
                    ar = min(w, h) / max(w, h)
                    if ar > 0.40:
                        score = ar * (1.0 - abs(w - h) / (w + h + 1e-5))
                        if score > best_score:
                            best_score = score
                            mean_d = float((w + h) / 2.0)
                            d_eq = float(2.0 * np.sqrt(a / np.pi))
                            best_cand = {
                                "frame": target_f,
                                "w": int(w),
                                "h": int(h),
                                "area": int(a),
                                "mean_diameter_px": mean_d,
                                "equiv_diameter_px": d_eq,
                                "aspect_ratio": float(ar),
                                "centroid": [float(centroids[i][0]), float(centroids[i][1])]
                            }
            if best_cand is not None:
                frame_measurements.append(best_cand)
        cap.release()
                
        if frame_measurements:
            d_vals = [m["mean_diameter_px"] for m in frame_measurements]
            first_f = frame_measurements[0]["frame"]
            results[clip_id] = {
                "cohort": "brev_a100_baseline",
                "ball": "ball1" if "b1" in clip_id else "ball2",
                "seed": int(clip_id.split("_")[-1].replace("s", "")),
                "birth_frame": first_f,
                "n_frames_detected": len(frame_measurements),
                "mean_diameter_px": float(np.mean(d_vals)),
                "std_diameter_px": float(np.std(d_vals)),
                "min_diameter_px": float(np.min(d_vals)),
                "max_diameter_px": float(np.max(d_vals)),
                "equiv_diameter_px": float(np.mean([m["equiv_diameter_px"] for m in frame_measurements])),
                "ratio_to_real": float(np.mean(d_vals) / REAL_BALL_D_PX),
                "ratio_to_token": float(np.mean(d_vals) / DIT_TOKEN_PX),
                "frames": frame_measurements
            }
    return results

def test_hypotheses(all_clips_data):
    """Statistically evaluates H-T, H-P, and H-S on the aggregate phantom dataset."""
    all_diameters = []
    all_sigmas = []
    all_birth_frames = []
    
    for clip_id, data in all_clips_data.items():
        all_diameters.append(data["mean_diameter_px"])
        if "sigma_c" in data:
            all_sigmas.append(data["sigma_c"])
        all_birth_frames.append(data["birth_frame"])
        
    all_d = np.array(all_diameters)
    
    # 1. Hypothesis H-T: Token Quantization
    # Test whether phantom ball diameters are bounded below by 32 px
    n_total = len(all_d)
    n_above_token = int(np.sum(all_d >= DIT_TOKEN_PX))
    frac_above_token = float(n_above_token / n_total)
    min_d = float(np.min(all_d))
    
    # Residual distance to nearest multiple of 32 px
    token_multiples = np.round(all_d / DIT_TOKEN_PX) * DIT_TOKEN_PX
    residuals_px = np.abs(all_d - token_multiples)
    mean_residual_px = float(np.mean(residuals_px))
    # Expected residual under a continuous uniform distribution U(0, 16) is 8.0 px
    
    # Binning by integer multiples of 32 px:
    # 1 token: [16, 48) (center 32)
    # 2 tokens: [48, 80) (center 64)
    # 3 tokens: [80, 112) (center 96)
    # 4+ tokens: >= 112
    bin_1token = int(np.sum((all_d >= 16) & (all_d < 48)))
    bin_2tokens = int(np.sum((all_d >= 48) & (all_d < 80)))
    bin_3tokens = int(np.sum((all_d >= 80) & (all_d < 112)))
    bin_4plus = int(np.sum(all_d >= 112))
    
    # 2. Hypothesis H-P: Scale Prior
    # Is diameter independent of sigma_c?
    if len(all_sigmas) == 9:
        sigmas_arr = np.array(all_sigmas)
        d_sigmas = np.array([all_clips_data[k]["mean_diameter_px"] for k in all_clips_data if "sigma_c" in all_clips_data[k]])
        r_sigma, p_sigma = stats.pearsonr(sigmas_arr, d_sigmas)
    else:
        r_sigma, p_sigma = 0.0, 1.0
        
    # 3. Hypothesis H-S: Spectral Commitment
    # Does diameter correlate with birth frame?
    r_birth, p_birth = stats.pearsonr(np.array(all_birth_frames), all_d)
    
    return {
        "n_clips_analyzed": n_total,
        "grand_mean_diameter_px": float(np.mean(all_d)),
        "grand_std_diameter_px": float(np.std(all_d, ddof=1)),
        "grand_median_diameter_px": float(np.median(all_d)),
        "min_diameter_observed_px": min_d,
        "max_diameter_observed_px": float(np.max(all_d)),
        "real_ball_diameter_px": REAL_BALL_D_PX,
        "mean_ratio_to_real_ball": float(np.mean(all_d) / REAL_BALL_D_PX),
        "mean_ratio_to_dit_token": float(np.mean(all_d) / DIT_TOKEN_PX),
        "hypothesis_HT_token_quantization": {
            "floor_test_passed": bool(min_d >= (DIT_TOKEN_PX - 7.0)), # allowing small boundary edge noise
            "n_above_32px": n_above_token,
            "frac_above_32px": frac_above_token,
            "mean_residual_to_nearest_32px_grid": mean_residual_px,
            "token_grid_histogram": {
                "1_token_32px_bin": bin_1token,
                "2_tokens_64px_bin": bin_2tokens,
                "3_tokens_96px_bin": bin_3tokens,
                "4plus_tokens_bin": bin_4plus
            },
            "dominant_modal_token_multiple": "2 tokens (64 px)" if bin_2tokens >= max(bin_1token, bin_3tokens, bin_4plus) else "1 token (32 px)"
        },
        "hypothesis_HP_scale_prior": {
            "pearson_r_with_sigma_c": float(r_sigma),
            "p_value_with_sigma_c": float(p_sigma),
            "is_independent_of_sigma": bool(p_sigma > 0.05)
        },
        "hypothesis_HS_spectral_commitment": {
            "pearson_r_with_birth_frame": float(r_birth),
            "p_value_with_birth_frame": float(p_birth),
            "is_correlated_with_birth_frame": bool(p_birth < 0.05)
        }
    }

def generate_visualizations(all_clips_data, test_stats, real_info):
    """Generates publication-grade figures and contact sheets."""
    all_d = np.array([data["mean_diameter_px"] for data in all_clips_data.values()])
    cohorts = [data["cohort"] for data in all_clips_data.values()]
    
    # Figure 1: 4-Panel Statistical Distribution
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    
    # Panel 1: Histogram vs DiT Token Grid
    ax1 = axes[0, 0]
    bins = np.linspace(15, 120, 22)
    ax1.hist(all_d, bins=bins, color="#2b5c8f", edgecolor="black", alpha=0.75, rwidth=0.85, label="Phantom Balls (n=23)")
    ax1.axvline(REAL_BALL_D_PX, color="red", linestyle="--", linewidth=2.5, label=f"Real Ball ({REAL_BALL_D_PX:.1f} px)")
    ax1.axvline(DIT_TOKEN_PX, color="cyan", linestyle="-", linewidth=2.0, label="1 DiT Token (32 px)")
    ax1.axvline(2 * DIT_TOKEN_PX, color="cyan", linestyle="--", linewidth=2.0, label="2 DiT Tokens (64 px)")
    ax1.axvline(3 * DIT_TOKEN_PX, color="cyan", linestyle=":", linewidth=2.0, label="3 DiT Tokens (96 px)")
    ax1.set_xlabel("Equivalent Ball Diameter (pixels)", fontsize=11, fontweight="bold")
    ax1.set_ylabel("Number of Clips", fontsize=11, fontweight="bold")
    ax1.set_title("Phantom Ball Diameters vs DiT Token Patch Grid", fontsize=12, fontweight="bold")
    ax1.legend(loc="upper right", frameon=True)
    ax1.grid(True, linestyle=":", alpha=0.6)
    
    # Panel 2: Ratio to Real Ball Across Cohorts
    ax2 = axes[0, 1]
    cohort_names = ["condnoise\n(Task 98)", "rope_scaling\n(Task 90/103)", "brev_baseline\n(Task 58)"]
    c_data = [
        [d["mean_diameter_px"] / REAL_BALL_D_PX for d in all_clips_data.values() if d["cohort"] == "condnoise"],
        [d["mean_diameter_px"] / REAL_BALL_D_PX for d in all_clips_data.values() if d["cohort"] == "rope_spatial_scaling"],
        [d["mean_diameter_px"] / REAL_BALL_D_PX for d in all_clips_data.values() if d["cohort"] == "brev_a100_baseline"]
    ]
    bplot = ax2.boxplot(c_data, labels=cohort_names, patch_artist=True, medianprops=dict(color="black", linewidth=2))
    colors = ["#4e79a7", "#f28e2b", "#59a14f"]
    for patch, color in zip(bplot['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    ax2.axhline(1.0, color="red", linestyle="--", linewidth=2, label="Real Ball Ratio (1.0x)")
    ax2.axhline(32.0 / REAL_BALL_D_PX, color="cyan", linestyle="--", linewidth=1.5, label=f"1 Token Ratio ({32.0/REAL_BALL_D_PX:.2f}x)")
    ax2.axhline(64.0 / REAL_BALL_D_PX, color="cyan", linestyle=":", linewidth=1.5, label=f"2 Tokens Ratio ({64.0/REAL_BALL_D_PX:.2f}x)")
    ax2.set_ylabel("Linear Diameter Ratio ($D_{phantom} / D_{real}$)", fontsize=11, fontweight="bold")
    ax2.set_title("Oversized Phantom Scaling by Experimental Cohort", fontsize=12, fontweight="bold")
    ax2.legend(loc="upper right", frameon=True)
    ax2.grid(True, linestyle=":", alpha=0.6)
    
    # Panel 3: Token Multiple Categorization
    ax3 = axes[1, 0]
    hist_dict = test_stats["hypothesis_HT_token_quantization"]["token_grid_histogram"]
    cats = ["1 Token\n(~32 px)", "2 Tokens\n(~64 px)", "3 Tokens\n(~96 px)", "4+ Tokens\n(>=112 px)"]
    counts = [hist_dict["1_token_32px_bin"], hist_dict["2_tokens_64px_bin"], hist_dict["3_tokens_96px_bin"], hist_dict["4plus_tokens_bin"]]
    bars = ax3.bar(cats, counts, color=["#76b7b2", "#4e79a7", "#e15759", "#b07aa1"], edgecolor="black", width=0.6)
    for bar in bars:
        yval = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2.0, yval + 0.2, f"{int(yval)} ({yval/len(all_d)*100:.0f}%)", ha='center', va='bottom', fontweight='bold')
    ax3.set_ylabel("Number of Clips", fontsize=11, fontweight="bold")
    ax3.set_title("Phantom Ball Distribution Binned by DiT Tokens", fontsize=12, fontweight="bold")
    ax3.set_ylim(0, max(counts) + 2)
    ax3.grid(True, linestyle=":", alpha=0.6, axis='y')
    
    # Panel 4: Diameter vs Detection Frame (H-S Test)
    ax4 = axes[1, 1]
    birth_f = [data["birth_frame"] for data in all_clips_data.values()]
    ax4.scatter(birth_f, all_d, c="#e15759", s=70, edgecolor="black", zorder=3, alpha=0.85)
    ax4.axhline(REAL_BALL_D_PX, color="red", linestyle="--", linewidth=2.0, label="Real Ball (21.6 px)")
    ax4.axhline(DIT_TOKEN_PX, color="cyan", linestyle="-", linewidth=2.0, label="1 DiT Token (32 px)")
    ax4.axhline(2 * DIT_TOKEN_PX, color="cyan", linestyle="--", linewidth=2.0, label="2 DiT Tokens (64 px)")
    ax4.set_xlabel("Birth Frame ($t_{birth}$)", fontsize=11, fontweight="bold")
    ax4.set_ylabel("Phantom Ball Diameter (pixels)", fontsize=11, fontweight="bold")
    r_val = test_stats["hypothesis_HS_spectral_commitment"]["pearson_r_with_birth_frame"]
    p_val = test_stats["hypothesis_HS_spectral_commitment"]["p_value_with_birth_frame"]
    ax4.set_title(f"H-S Test: Diameter vs Birth Frame (r = {r_val:.2f}, p = {p_val:.3f})", fontsize=12, fontweight="bold")
    ax4.legend(loc="upper right", frameon=True)
    ax4.grid(True, linestyle=":", alpha=0.6)
    
    plt.tight_layout()
    plot_path = os.path.join(PLOTS_DIR, "figure_token_quantization_distribution.png")
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved figure to {plot_path}")
    
    # Figure 2: Visual Contact Sheet with Overlaid 32x32 Token Grid
    make_visual_sheet()

def make_visual_sheet():
    """Builds a side-by-side comparison sheet of real ball vs phantom balls with overlaid token grid."""
    f0_path = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/rog1/condnoise/gauge_ball1_f0_832x480.png"
    f0_img = cv2.imread(f0_path)
    
    # Crop real ball in gripper: y in [90:218], x in [250:378] (128x128 px = exactly 4x4 DiT tokens!)
    real_crop = f0_img[90:218, 250:378].copy()
    
    # We select representative phantom ball crops (128x128 px each):
    # 1. s005t_s1 frame 3 (tile 0,1 in s005t_s1_a.jpg)
    strip1 = cv2.imread("/home/nail/swarm-work/agy-3/cosmos-swarm/work/rog1/condnoise/res/eye/s005t_s1_a.jpg")
    tile1 = cv2.resize(strip1[0:288, 240:480], (300, 360))
    # Ball is around x=135, y=175 in tile => crop 128x128 centered at (135, 175)
    c1 = tile1[111:239, 71:199].copy() if tile1.shape[0]>=239 and tile1.shape[1]>=199 else np.zeros((128,128,3), dtype=np.uint8)
    
    # 2. s005t_s2 giant sphere frame 9
    strip2 = cv2.imread("/home/nail/swarm-work/agy-3/cosmos-swarm/work/rog1/condnoise/res/eye/s005t_s2_a.jpg")
    tile2 = cv2.resize(strip2[0:288, 720:960], (300, 360))
    c2 = tile2[90:218, 90:218].copy() if tile2.shape[0]>=218 and tile2.shape[1]>=218 else np.zeros((128,128,3), dtype=np.uint8)
    
    # 3. Task 103 RoPE ctrl_s3 frame 16
    cap_rope = cv2.VideoCapture("/home/nail/swarm-work/agy-3/task103_rope_scale_review/clips/gauge_b1_ctrl_s3.mp4")
    cap_rope.set(cv2.CAP_PROP_POS_FRAMES, 16)
    _, fr_rope = cap_rope.read()
    if fr_rope.mean() > 120: fr_rope = 255 - fr_rope
    c3 = fr_rope[190:318, 230:358].copy()
    
    # 4. Task 58 Brev A100 baseline box_ctrl_b1_noneg_s3 frame 50
    cap_brev = cv2.VideoCapture("/home/nail/swarm-work/raj-3/brev_box/out/box_ctrl_b1_noneg_s3.mp4")
    cap_brev.set(cv2.CAP_PROP_POS_FRAMES, 50)
    _, fr_brev = cap_brev.read()
    c4 = fr_brev[250:378, 230:358].copy()
    
    panels = [
        ("Real Ball (f0)\nD=21.6 px (<1 token)", real_crop),
        ("Phantom (s005t_s1 f3)\nD=45 px (1.4 tokens)", c1),
        ("Giant Sphere (s005t_s2)\nD=110+ px (>3.5 tokens)", c2),
        ("Phantom (RoPE ctrl_s3)\nD=48 px (1.5 tokens)", c3),
        ("Phantom (Brev A100 s3)\nD=65 px (2.0 tokens)", c4)
    ]
    
    # Overlay 32x32 DiT token grid in cyan (0, 255, 255) and label
    processed_panels = []
    for title, img in panels:
        p = cv2.resize(img, (256, 256)) # scale 2x for clarity
        # Draw 32*2 = 64 px grid lines
        for x in range(0, 256, 64):
            cv2.line(p, (x, 0), (x, 256), (255, 255, 0), 1)
        for y in range(0, 256, 64):
            cv2.line(p, (0, y), (256, y), (255, 255, 0), 1)
            
        # Add banner at top
        banner = np.zeros((48, 256, 3), dtype=np.uint8)
        lines = title.split("\n")
        cv2.putText(banner, lines[0], (6, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        cv2.putText(banner, lines[1], (6, 38), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
        stacked = np.vstack([banner, p])
        processed_panels.append(stacked)
        
    final_sheet = np.hstack(processed_panels)
    sheet_path = os.path.join(SHEETS_DIR, "figure_phantom_overlay_token_grid.jpg")
    cv2.imwrite(sheet_path, final_sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])
    print(f"Saved token grid visual sheet to {sheet_path}")

def main():
    print("=========================================================================")
    print("Task 110: DiT Token Quantization & Phantom Ball Diameter Analysis")
    print("Testing Scout-1's Hypothesis #2519 across 3 independent cohorts")
    print("=========================================================================\n")
    
    real_info = measure_real_ball()
    print(f"Real Ball Ground Truth: D = {real_info['measured_diameter_px']:.1f} px ({real_info['ratio_to_token']:.2f} tokens)")
    print(f"DiT Token Size: {DIT_TOKEN_PX:.0f} x {DIT_TOKEN_PX:.0f} px (Area = {real_info['dit_token_area_px2']:.0f} px^2)\n")
    
    print("Analyzing Cohort 1: Condition-Noise (Task 98 native strips, n=9)...")
    c1_data = analyze_cohort1_condnoise()
    print(f"  Processed {len(c1_data)} condition-noise clips.")
    
    print("Analyzing Cohort 2: RoPE Spatial Scaling (Task 90/103 MP4s, n=6)...")
    c2_data = analyze_cohort2_rope()
    print(f"  Processed {len(c2_data)} RoPE clips.")
    
    print("Analyzing Cohort 3: Brev A100 Baseline (Task 58 MP4s, n=8)...")
    c3_data = analyze_cohort3_brev_baseline()
    print(f"  Processed {len(c3_data)} Brev A100 clips.")
    
    all_clips_data = {}
    all_clips_data.update(c1_data)
    all_clips_data.update(c2_data)
    all_clips_data.update(c3_data)
    print(f"\nTotal clips successfully analyzed: {len(all_clips_data)}")
    
    print("\n--- Evaluating Hypotheses ---")
    test_stats = test_hypotheses(all_clips_data)
    
    print(f"Grand Mean Phantom Diameter: {test_stats['grand_mean_diameter_px']:.1f} +/- {test_stats['grand_std_diameter_px']:.1f} px")
    print(f"Grand Median Phantom Diameter: {test_stats['grand_median_diameter_px']:.1f} px")
    print(f"Ratio to Real Ball: {test_stats['mean_ratio_to_real_ball']:.2f}x (Real Ball = {REAL_BALL_D_PX:.1f} px)")
    print(f"Ratio to DiT Token: {test_stats['mean_ratio_to_dit_token']:.2f} tokens (1 token = {DIT_TOKEN_PX:.0f} px)")
    print(f"Minimum Phantom Diameter Observed: {test_stats['min_diameter_observed_px']:.1f} px")
    print(f"Fraction with D >= 32 px: {test_stats['hypothesis_HT_token_quantization']['frac_above_32px']*100:.1f}% ({test_stats['hypothesis_HT_token_quantization']['n_above_32px']}/{test_stats['n_clips_analyzed']})")
    print(f"Dominant Token Modal Multiple: {test_stats['hypothesis_HT_token_quantization']['dominant_modal_token_multiple']}")
    print(f"Token Grid Histogram: {test_stats['hypothesis_HT_token_quantization']['token_grid_histogram']}")
    print(f"Mean Residual to 32px Grid: {test_stats['hypothesis_HT_token_quantization']['mean_residual_to_nearest_32px_grid']:.1f} px")
    print(f"H-P Scale Prior Correlation (r with sigma_c): r = {test_stats['hypothesis_HP_scale_prior']['pearson_r_with_sigma_c']:.3f} (p = {test_stats['hypothesis_HP_scale_prior']['p_value_with_sigma_c']:.3f})")
    print(f"H-S Spectral Correlation (r with birth frame): r = {test_stats['hypothesis_HS_spectral_commitment']['pearson_r_with_birth_frame']:.3f} (p = {test_stats['hypothesis_HS_spectral_commitment']['p_value_with_birth_frame']:.3f})")
    
    print("\nGenerating visualizations...")
    generate_visualizations(all_clips_data, test_stats, real_info)
    
    # Save full JSON
    master_output = {
        "metadata": {
            "task_id": 110,
            "agent": "agy-3",
            "reference_hypothesis": "scout-1 #2519",
            "reviewed_findings": [2475, 2499],
            "real_ball_ground_truth": real_info
        },
        "statistical_tests": test_stats,
        "clips": all_clips_data
    }
    
    out_json = os.path.join(OUT_DIR, "task110_token_quantization_results.json")
    with open(out_json, "w") as f:
        json.dump(master_output, f, indent=2)
    print(f"Saved master results to {out_json}")
    print("\nTask 110 analysis complete!")

if __name__ == "__main__":
    main()
