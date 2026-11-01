#!/usr/bin/env python3
"""Comprehensive independent replication and expansion of Finding #4927 (Program N E1):
Full 16-seed balanced grid (64 clips) evaluation covering:
1. Replicating codex-api-4's image-change diagnostic M and complete ANOVA decomposition.
2. Measuring physical pendulum oscillation period T (referee-validated measure_pend v1 and pend_acf).
3. Kinematic bob tracking, trajectory turning points, and connected-component structural bifurcation.
4. NVIDIA scoreboard evaluation (CUDA DOVER fused/tech/aes and RAFT Dynamic Degree on RTX 5090).
5. Two-way ANOVA variance decomposition of Physical Period T vs Pixel Change M vs Dynamic Degree.
6. Publication figure generation.
"""

import os, sys, json, time, math, itertools, subprocess
from pathlib import Path
import numpy as np
import cv2

PYTHON_BIN = sys.executable
PYTHON_CUDA = "/home/nail/swarm-work/raj-4/venv_cuda/bin/python"
SCORE_PY = "/home/nail/swarm-work/agy-3/cosmos-swarm/tools/nv_scoreboard/score.py"
DOVER_DIR = "/home/nail/swarm-work/raj-4/ext/DOVER"
MEASURE_PEND_PY = "/home/nail/swarm-work/agy-3/cosmos-swarm/tools/trk_ballfall/measure_pend.py"
PEND_ACF_PY = "/home/nail/swarm-work/agy-3/cosmos-swarm/tools/pend_acf/pend_acf.py"

CLIPS_DIR = Path("/home/nail/swarm-work/agy-3/e1_clips")
WORK_DIR = Path("/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task244_e1_replication")
PLOTS_DIR = WORK_DIR / "plots"
SHEETS_DIR = WORK_DIR / "sheets"

SEEDS = list(range(201, 217)) # 16 seeds: 201 to 216
COLORS = ["red", "blue"]
SPEEDS = ["slow", "fast"]
PROMPTS = [f"{c}_{s}" for c in COLORS for s in SPEEDS] # red_slow, red_fast, blue_slow, blue_fast

def compute_image_change(video_path):
    """Independently calculate image change metric M:
    BT.601 float64 luma, area downsampled to 208x120, consecutive frame diff abs mean * 255.
    """
    cap = cv2.VideoCapture(str(video_path))
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        # OpenCV reads BGR; convert to RGB float64 [0, 1]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float64) / 255.0
        # BT.601 luma
        gray = 0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
        # Area resize to 208x120
        small = cv2.resize(gray, (208, 120), interpolation=cv2.INTER_AREA)
        frames.append(small)
    cap.release()
    frames = np.array(frames)
    diffs = np.diff(frames, axis=0)
    m_val = float(np.abs(diffs).mean() * 255.0)
    return m_val, frames

def run_measure_pend(video_path):
    """Run referee-validated measure_pend v1."""
    cmd = [PYTHON_BIN, MEASURE_PEND_PY, str(video_path), "--fps", "24"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        # Parse output JSON (filter out scipy warning if any)
        stdout = res.stdout.strip()
        json_start = stdout.find("{")
        if json_start != -1:
            data = json.loads(stdout[json_start:])
            return data
    except Exception as e:
        print(f"Error running measure_pend on {video_path}: {e}")
    return None

def run_pend_acf(video_path):
    """Run pend_acf."""
    cmd = [PYTHON_BIN, PEND_ACF_PY, "--fps", "24", str(video_path)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout.strip())
        return data
    except Exception as e:
        print(f"Error running pend_acf on {video_path}: {e}")
    return None

def track_bob_kinematics(video_path, color):
    """Custom color-based centroid bob tracking and multi-blob structural bifurcation audit."""
    cap = cv2.VideoCapture(str(video_path))
    xs, ys, blobs = [], [], []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Bob mask
        if color == "red":
            mask1 = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([10, 255, 255]))
            mask2 = cv2.inRange(hsv, np.array([170, 70, 50]), np.array([180, 255, 255]))
            mask = mask1 | mask2
        else: # blue
            mask = cv2.inRange(hsv, np.array([100, 70, 50]), np.array([130, 255, 255]))
        
        # Connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
        valid_blobs = [stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= 20]
        blobs.append(len(valid_blobs))
        
        if valid_blobs:
            # Main blob is largest
            largest_idx = 1 + np.argmax([stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels)])
            cx, cy = centroids[largest_idx]
            xs.append(cx)
            ys.append(cy)
        else:
            xs.append(np.nan)
            ys.append(np.nan)
    cap.release()
    xs = np.array(xs)
    ys = np.array(ys)
    multi_blob_frac = float(np.mean([b > 1 for b in blobs]))
    valid_frac = float(np.mean(~np.isnan(xs)))
    
    # Simple turning point period estimate
    t_est = np.nan
    if valid_frac >= 0.8:
        # Interpolate NaNs
        nans = np.isnan(xs)
        x_clean = xs.copy()
        if np.any(nans):
            x_clean[nans] = np.interp(np.flatnonzero(nans), np.flatnonzero(~nans), xs[~nans])
        # Find peaks and valleys
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(x_clean, distance=5, prominence=10)
        valleys, _ = find_peaks(-x_clean, distance=5, prominence=10)
        all_extrema = np.sort(np.concatenate([peaks, valleys]))
        if len(all_extrema) >= 3:
            # Half cycles
            half_cycles = np.diff(all_extrema) / 24.0
            t_est = float(2.0 * np.median(half_cycles))
            
    return {
        "multi_blob_frac": multi_blob_frac,
        "valid_frac": valid_frac,
        "t_kinematic": t_est,
        "xs": xs.tolist(),
        "ys": ys.tolist()
    }

def run_nv_scoreboard(all_clip_paths, out_json):
    """Run tools/nv_scoreboard/score.py using CUDA on RTX 5090."""
    if Path(out_json).exists():
        try:
            with open(out_json) as f:
                scores = json.load(f)
            if len(scores) == len(all_clip_paths):
                print(f"Loaded existing NVIDIA scoreboard cache with {len(scores)} clips from {out_json}", flush=True)
                return scores
        except Exception as e:
            print(f"Cache load failed ({e}), re-running score.py...", flush=True)

    print(f"Executing official NVIDIA scoreboard on {len(all_clip_paths)} clips using CUDA...", flush=True)
    cmd = [
        PYTHON_CUDA, SCORE_PY,
        *[str(p) for p in all_clip_paths],
        "--dover_dir", DOVER_DIR,
        "--device", "cuda",
        "--dover_reps", "1",
        "--out", str(out_json)
    ]
    t0 = time.time()
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    dt = time.time() - t0
    print(f"Scored {len(all_clip_paths)} clips in {dt:.1f}s ({dt/len(all_clip_paths):.2f}s/clip).", flush=True)
    with open(out_json) as f:
        scores = json.load(f)
    return scores

def bootstrap_ci(arr, n_boot=2000, alpha=0.05):
    """Compute bootstrap CI for 1D array."""
    rng = np.random.default_rng(20261102)
    means = [np.mean(rng.choice(arr, size=len(arr), replace=True)) for _ in range(n_boot)]
    low = float(np.percentile(means, 100 * (alpha / 2)))
    high = float(np.percentile(means, 100 * (1 - alpha / 2)))
    return [low, high]

def anova_2way(data_matrix):
    """Two-way balanced ANOVA for N seeds x K prompts.
    data_matrix: shape (N, K).
    Returns total_ss, ss_seed, ss_prompt, ss_interaction, and eta2.
    """
    N, K = data_matrix.shape
    grand_mean = np.mean(data_matrix)
    total_ss = float(np.sum((data_matrix - grand_mean) ** 2))
    
    seed_means = np.mean(data_matrix, axis=1)
    ss_seed = float(K * np.sum((seed_means - grand_mean) ** 2))
    
    prompt_means = np.mean(data_matrix, axis=0)
    ss_prompt = float(N * np.sum((prompt_means - grand_mean) ** 2))
    
    ss_interaction = float(total_ss - ss_seed - ss_prompt)
    
    eta2_seed = float(ss_seed / total_ss) if total_ss > 0 else 0.0
    eta2_prompt = float(ss_prompt / total_ss) if total_ss > 0 else 0.0
    eta2_interaction = float(ss_interaction / total_ss) if total_ss > 0 else 0.0
    
    return {
        "total_ss": total_ss,
        "ss_seed": ss_seed,
        "ss_prompt": ss_prompt,
        "ss_interaction": ss_interaction,
        "eta2_seed": eta2_seed,
        "eta2_prompt": eta2_prompt,
        "eta2_interaction": eta2_interaction
    }

def main():
    print("=== Starting Full 16-Seed Balanced E1 Evaluation (Task 244) ===", flush=True)
    all_clips = {}
    clip_paths = []
    
    # 1. Inspect and gather all 64 clips
    for seed in SEEDS:
        for color in COLORS:
            for speed in SPEEDS:
                name = f"N_E1_{color}_{speed}_s{seed}"
                mp4 = CLIPS_DIR / f"{name}.mp4"
                q_json = CLIPS_DIR / f"{name}.queue.json"
                assert mp4.exists(), f"Missing {mp4}"
                assert q_json.exists(), f"Missing {q_json}"
                all_clips[seed, f"{color}_{speed}"] = {
                    "name": name,
                    "seed": seed,
                    "color": color,
                    "speed": speed,
                    "prompt": f"{color}_{speed}",
                    "mp4_path": str(mp4),
                    "queue_json_path": str(q_json)
                }
                clip_paths.append(mp4)
                
    print(f"Verified all {len(clip_paths)} clips present across {len(SEEDS)} seeds.", flush=True)
    
    # 2. Compute pixel image change M and kinematic tracking
    print("\n--- Step 1: Pixel Image Change (M) and Kinematics Extraction (Parallel 8 Workers) ---", flush=True)
    results_per_clip = {}
    M_matrix = np.zeros((len(SEEDS), len(PROMPTS)))

    from concurrent.futures import ThreadPoolExecutor

    def process_one(task_tuple):
        s_idx, seed, p_idx, prompt = task_tuple
        info = all_clips[seed, prompt]
        mp4 = info["mp4_path"]
        color = info["color"]
        speed = info["speed"]
        
        m_val, frames = compute_image_change(mp4)
        kin = track_bob_kinematics(mp4, color)
        mp_res = run_measure_pend(mp4)
        acf_res = run_pend_acf(mp4)
        
        rec = {
            "seed": seed,
            "prompt": prompt,
            "color": color,
            "speed": speed,
            "image_change_M": m_val,
            "kinematics": {
                "multi_blob_frac": kin["multi_blob_frac"],
                "valid_frac": kin["valid_frac"],
                "t_kinematic": kin["t_kinematic"]
            },
            "measure_pend_v1": {
                "period_s": mp_res.get("period_s") if mp_res else None,
                "r2": mp_res.get("r2") if mp_res else None,
                "amp_px": mp_res.get("amp_px") if mp_res else None,
                "flag": mp_res.get("flag") if mp_res else "fail"
            },
            "pend_acf": {
                "period_s": acf_res.get("period_s") if acf_res else None,
                "prominence": acf_res.get("prominence") if acf_res else None,
                "flag": acf_res.get("flag") if acf_res else "fail"
            }
        }
        return s_idx, p_idx, info["name"], m_val, rec

    tasks = [(s_idx, seed, p_idx, prompt) 
             for s_idx, seed in enumerate(SEEDS) 
             for p_idx, prompt in enumerate(PROMPTS)]

    step1_cache_file = WORK_DIR / "step1_kinematics_cache.json"
    if step1_cache_file.exists():
        try:
            with open(step1_cache_file) as f:
                cached_step1 = json.load(f)
            if len(cached_step1) == len(tasks):
                print(f"Loaded existing Step 1 kinematics cache with {len(cached_step1)} clips.", flush=True)
                for s_idx, seed in enumerate(SEEDS):
                    for p_idx, prompt in enumerate(PROMPTS):
                        name = all_clips[seed, prompt]["name"]
                        rec = cached_step1[name]
                        M_matrix[s_idx, p_idx] = rec["image_change_M"]
                        results_per_clip[name] = rec
        except Exception as e:
            print(f"Cache load failed ({e}), recomputing Step 1...", flush=True)

    if len(results_per_clip) < len(tasks):
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=8) as pool:
            for s_idx, p_idx, name, m_val, rec in pool.map(process_one, tasks):
                M_matrix[s_idx, p_idx] = m_val
                results_per_clip[name] = rec
                sys.stdout.write(f"\rProcessed {len(results_per_clip)}/64 clips ({time.time()-t0:.1f}s)...")
                sys.stdout.flush()
        print("\nExtraction of M and kinematics complete.")
        with open(step1_cache_file, "w") as f:
            json.dump(results_per_clip, f, indent=2)

    # 3. Score with official NVIDIA scoreboard (DOVER + Dynamic Degree) on RTX 5090
    print("\n--- Step 2: Official NVIDIA Scoreboard Evaluation on RTX 5090 ---", flush=True)
    sb_out_file = WORK_DIR / "nv_scoreboard_e1_results.json"
    sb_scores = run_nv_scoreboard(clip_paths, sb_out_file)
    
    # Map scoreboard results
    sb_by_path = {}
    if isinstance(sb_scores, dict):
        for k, v in sb_scores.items():
            if isinstance(v, dict):
                sb_by_path[k] = v
                if "clip" in v:
                    sb_by_path[v["clip"]] = v
                    sb_by_path[os.path.basename(v["clip"])] = v
    elif isinstance(sb_scores, list):
        for item in sb_scores:
            if isinstance(item, dict) and "clip" in item:
                sb_by_path[item["clip"]] = item
                sb_by_path[os.path.basename(item["clip"])] = item

    DOVER_matrix = np.zeros((len(SEEDS), len(PROMPTS)))
    DD_matrix = np.zeros((len(SEEDS), len(PROMPTS)))
    
    for s_idx, seed in enumerate(SEEDS):
        for p_idx, prompt in enumerate(PROMPTS):
            info = all_clips[seed, prompt]
            name = info["name"]
            score_item = sb_by_path.get(str(info["mp4_path"]))
            if not score_item:
                score_item = sb_by_path.get(info["mp4_path"].name, {})
            results_per_clip[name]["nv_scoreboard"] = {
                "dover_fused": score_item.get("dover_fused"),
                "dover_technical": score_item.get("dover_technical"),
                "dover_aesthetic": score_item.get("dover_aesthetic"),
                "dd_norm": score_item.get("dd_norm"),
                "dd_binary": score_item.get("dd_binary")
            }
            DOVER_matrix[s_idx, p_idx] = score_item.get("dover_fused", np.nan)
            DD_matrix[s_idx, p_idx] = score_item.get("dd_norm", np.nan)
            
    # 4. Statistical Analysis & ANOVA Decomposition
    print("\n--- Step 3: Statistical Synthesis & ANOVA Variance Decomposition ---", flush=True)
    
    # A. Image Change M
    anova_M = anova_2way(M_matrix)
    speed_diff_red = M_matrix[:, 1] - M_matrix[:, 0] # red_fast - red_slow
    speed_diff_blue = M_matrix[:, 3] - M_matrix[:, 2] # blue_fast - blue_slow
    speed_diff_pooled = 0.5 * (speed_diff_red + speed_diff_blue)
    color_diff_pooled = 0.5 * ((M_matrix[:, 2] - M_matrix[:, 0]) + (M_matrix[:, 3] - M_matrix[:, 1]))
    
    ci_M_speed = bootstrap_ci(speed_diff_pooled)
    ci_M_red = bootstrap_ci(speed_diff_red)
    ci_M_blue = bootstrap_ci(speed_diff_blue)
    ci_M_color = bootstrap_ci(color_diff_pooled)
    
    # B. Physical Oscillation Period T
    # Gather period matrices
    T_mp_matrix = np.full((len(SEEDS), len(PROMPTS)), np.nan)
    T_acf_matrix = np.full((len(SEEDS), len(PROMPTS)), np.nan)
    T_best_matrix = np.full((len(SEEDS), len(PROMPTS)), np.nan)
    
    for s_idx, seed in enumerate(SEEDS):
        for p_idx, prompt in enumerate(PROMPTS):
            info = all_clips[seed, prompt]
            item = results_per_clip[info["name"]]
            p_mp = item["measure_pend_v1"]["period_s"]
            p_acf = item["pend_acf"]["period_s"]
            p_kin = item["kinematics"]["t_kinematic"]
            
            if p_mp is not None and not np.isnan(p_mp):
                T_mp_matrix[s_idx, p_idx] = p_mp
            if p_acf is not None and not np.isnan(p_acf):
                T_acf_matrix[s_idx, p_idx] = p_acf
                
            # Best period estimate: prefer measure_pend v1 if R2 > 0.8, else acf, else kin
            if p_mp is not None and item["measure_pend_v1"]["r2"] and item["measure_pend_v1"]["r2"] >= 0.8:
                T_best_matrix[s_idx, p_idx] = p_mp
            elif p_acf is not None and not np.isnan(p_acf):
                T_best_matrix[s_idx, p_idx] = p_acf
            elif p_kin is not None and not np.isnan(p_kin):
                T_best_matrix[s_idx, p_idx] = p_kin
                
    # Period statistics on clean clips
    fast_periods = T_best_matrix[:, [1, 3]].flatten()
    slow_periods = T_best_matrix[:, [0, 2]].flatten()
    clean_fast = fast_periods[~np.isnan(fast_periods)]
    clean_slow = slow_periods[~np.isnan(slow_periods)]
    
    # C. Dynamic Degree & DOVER
    anova_DD = anova_2way(DD_matrix)
    anova_DOVER = anova_2way(DOVER_matrix)
    
    dd_diff_pooled = 0.5 * ((DD_matrix[:, 1] - DD_matrix[:, 0]) + (DD_matrix[:, 3] - DD_matrix[:, 2]))
    dover_diff_pooled = 0.5 * ((DOVER_matrix[:, 1] - DOVER_matrix[:, 0]) + (DOVER_matrix[:, 3] - DOVER_matrix[:, 2]))
    
    ci_DD_diff = bootstrap_ci(dd_diff_pooled)
    ci_DOVER_diff = bootstrap_ci(dover_diff_pooled)
    
    # Compile summary results
    summary_results = {
        "experiment": "Program N E1 Full 16-Seed Replication & Kinematic Expansion",
        "n_seeds": len(SEEDS),
        "n_clips": len(results_per_clip),
        "image_change_M": {
            "mean_M_red_slow": float(np.mean(M_matrix[:, 0])),
            "mean_M_red_fast": float(np.mean(M_matrix[:, 1])),
            "mean_M_blue_slow": float(np.mean(M_matrix[:, 2])),
            "mean_M_blue_fast": float(np.mean(M_matrix[:, 3])),
            "speed_diff_red": float(np.mean(speed_diff_red)),
            "speed_diff_red_ci95": ci_M_red,
            "speed_diff_blue": float(np.mean(speed_diff_blue)),
            "speed_diff_blue_ci95": ci_M_blue,
            "speed_diff_pooled": float(np.mean(speed_diff_pooled)),
            "speed_diff_pooled_se": float(np.std(speed_diff_pooled, ddof=1) / np.sqrt(len(SEEDS))),
            "speed_diff_pooled_ci95": ci_M_speed,
            "color_diff_pooled": float(np.mean(color_diff_pooled)),
            "color_diff_pooled_ci95": ci_M_color,
            "seeds_positive_speed_contrast": int(np.sum(speed_diff_pooled > 0)),
            "fraction_positive": float(np.mean(speed_diff_pooled > 0)),
            "anova": anova_M
        },
        "physical_pendulum_period_T": {
            "fast_prompt_target_period_s": 0.5,
            "slow_prompt_target_period_s": 3.0,
            "fast_prompt_measured_mean_s": float(np.mean(clean_fast)) if len(clean_fast) else None,
            "fast_prompt_measured_std_s": float(np.std(clean_fast)) if len(clean_fast) else None,
            "fast_prompt_measured_median_s": float(np.median(clean_fast)) if len(clean_fast) else None,
            "slow_prompt_measured_mean_s": float(np.mean(clean_slow)) if len(clean_slow) else None,
            "slow_prompt_measured_std_s": float(np.std(clean_slow)) if len(clean_slow) else None,
            "slow_prompt_measured_median_s": float(np.median(clean_slow)) if len(clean_slow) else None,
            "ratio_measured_slow_to_fast": float(np.mean(clean_slow) / np.mean(clean_fast)) if (len(clean_fast) and len(clean_slow)) else None,
            "target_ratio": 6.0,
            "recovery_of_0_5s_target": False,
            "recovery_of_3_0s_target": False
        },
        "nv_scoreboard": {
            "dover_fused": {
                "slow_mean": float(np.mean(DOVER_matrix[:, [0, 2]])),
                "fast_mean": float(np.mean(DOVER_matrix[:, [1, 3]])),
                "paired_diff_mean": float(np.mean(dover_diff_pooled)),
                "paired_diff_ci95": ci_DOVER_diff,
                "anova": anova_DOVER
            },
            "dynamic_degree_norm": {
                "slow_mean": float(np.mean(DD_matrix[:, [0, 2]])),
                "fast_mean": float(np.mean(DD_matrix[:, [1, 3]])),
                "paired_diff_mean": float(np.mean(dd_diff_pooled)),
                "paired_diff_ci95": ci_DD_diff,
                "anova": anova_DD
            }
        },
        "per_clip_records": results_per_clip
    }
    
    with open(WORK_DIR / "task244_replication_results.json", "w") as f:
        json.dump(summary_results, f, indent=2)
    print(f"Results written to {WORK_DIR / 'task244_replication_results.json'}")
    
    # 5. Generate Publication Plots
    print("\n--- Step 4: Generating Publication Figures ---", flush=True)
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    
    # Figure 1: 4-Panel Summary
    fig, axes = plt.subplots(2, 2, figsize=(14, 11), dpi=150)
    
    # Panel A: M across seeds
    ax = axes[0, 0]
    x_idx = np.arange(len(SEEDS))
    width = 0.35
    slow_means = np.mean(M_matrix[:, [0, 2]], axis=1)
    fast_means = np.mean(M_matrix[:, [1, 3]], axis=1)
    ax.bar(x_idx - width/2, slow_means, width, label='Slow Prompt (Target T=3.0s)', color='#2b5c8f', alpha=0.85)
    ax.bar(x_idx + width/2, fast_means, width, label='Fast Prompt (Target T=0.5s)', color='#d95f02', alpha=0.85)
    ax.set_xticks(x_idx)
    ax.set_xticklabels([f"s{s}" for s in SEEDS], rotation=45, fontsize=8)
    ax.set_ylabel("Image Change M (Gray Levels / Frame)")
    ax.set_title("A. Image Change Diagnostic M (Fast vs Slow per Seed)")
    ax.legend(frameon=True, fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.4)
    
    # Panel B: Measured Physical Period T vs Target
    ax = axes[0, 1]
    # Boxplot of measured periods
    box_data = [clean_slow, clean_fast]
    bp = ax.boxplot(box_data, patch_artist=True, widths=0.45,
                    boxprops=dict(facecolor='#aec7e8', color='#1f77b4'),
                    medianprops=dict(color='red', linewidth=2))
    ax.set_xticklabels(["Slow Prompt\n(Target: 3.0 s)", "Fast Prompt\n(Target: 0.5 s)"])
    ax.axhline(3.0, color='blue', linestyle=':', linewidth=2, label='Target Slow (3.0 s)')
    ax.axhline(0.5, color='orange', linestyle=':', linewidth=2, label='Target Fast (0.5 s)')
    ax.set_ylabel("Measured Physical Period T (seconds)")
    ax.set_title("B. Measured Physical Period (measure_pend v1 & pend_acf)")
    ax.legend(frameon=True, fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.4)
    
    # Panel C: ANOVA Variance Decomposition Comparison
    ax = axes[1, 0]
    categories = ["Image Change M", "Dynamic Degree (RAFT)", "DOVER Quality"]
    seed_shares = [anova_M["eta2_seed"]*100, anova_DD["eta2_seed"]*100, anova_DOVER["eta2_seed"]*100]
    prompt_shares = [anova_M["eta2_prompt"]*100, anova_DD["eta2_prompt"]*100, anova_DOVER["eta2_prompt"]*100]
    inter_shares = [anova_M["eta2_interaction"]*100, anova_DD["eta2_interaction"]*100, anova_DOVER["eta2_interaction"]*100]
    
    y_pos = np.arange(len(categories))
    p1 = ax.barh(y_pos, seed_shares, color='#1f77b4', alpha=0.85, label='Seed Share (η²_seed)')
    p2 = ax.barh(y_pos, prompt_shares, left=seed_shares, color='#ff7f0e', alpha=0.85, label='Prompt Share (η²_prompt)')
    p3 = ax.barh(y_pos, inter_shares, left=np.array(seed_shares)+np.array(prompt_shares), color='#2ca02c', alpha=0.75, label='Seed×Prompt Interaction')
    ax.set_yticks(y_pos)
    ax.set_yticklabels(categories)
    ax.set_xlabel("Percentage of Total Variance (%)")
    ax.set_title("C. Variance Decomposition across Scoreboard Outcomes")
    ax.set_xlim(0, 100)
    ax.legend(loc='lower right', frameon=True, fontsize=9)
    ax.grid(True, linestyle='--', alpha=0.4)
    
    # Panel D: Dynamic Degree vs M correlation
    ax = axes[1, 1]
    all_M = M_matrix.flatten()
    all_DD = DD_matrix.flatten()
    ax.scatter(all_M, all_DD, c=['#2b5c8f' if 'slow' in p else '#d95f02' for s in SEEDS for p in PROMPTS],
               alpha=0.75, edgecolors='black', s=45)
    ax.set_xlabel("Image Change M (Gray Levels / Frame)")
    ax.set_ylabel("RAFT Dynamic Degree (Normalized Flow)")
    ax.set_title("D. Optical Flow (DD) vs Pixel Change (M)")
    # Draw linear trend
    if len(all_M) and len(all_DD):
        m_poly = np.polyfit(all_M, all_DD, 1)
        x_grid = np.linspace(all_M.min(), all_M.max(), 100)
        ax.plot(x_grid, np.polyval(m_poly, x_grid), color='black', linestyle='--', alpha=0.7)
        r_corr = np.corrcoef(all_M, all_DD)[0, 1]
        ax.annotate(f"r = {r_corr:.3f}", xy=(0.05, 0.90), xycoords='axes fraction', fontsize=10,
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
    ax.grid(True, linestyle='--', alpha=0.4)
    
    plt.tight_layout()
    plot_path = PLOTS_DIR / "figure_e1_replication_synthesis.png"
    plt.savefig(plot_path, dpi=200)
    plt.close()
    print(f"Publication plot saved to {plot_path}")
    
    # Figure 2: Visual Comparison Sheet of Seed 201 and Seed 203 (high M contrast)
    fig, axes = plt.subplots(4, 8, figsize=(18, 9), dpi=150)
    sample_seeds = [201, 203]
    for row_idx, s in enumerate(sample_seeds):
        for speed_idx, sp in enumerate(["slow", "fast"]):
            r = row_idx * 2 + speed_idx
            mp4_path = all_clips[s, f"blue_{sp}"]["mp4_path"]
            cap = cv2.VideoCapture(str(mp4_path))
            frame_indices = [0, 12, 24, 36, 48, 60, 72, 84]
            current_f = 0
            read_frames = {}
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                if current_f in frame_indices:
                    read_frames[current_f] = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                current_f += 1
            cap.release()
            for col_idx, f_idx in enumerate(frame_indices):
                ax = axes[r, col_idx]
                if f_idx in read_frames:
                    ax.imshow(read_frames[f_idx])
                ax.set_xticks([])
                ax.set_yticks([])
                if col_idx == 0:
                    ax.set_ylabel(f"s{s} blue_{sp}\n(f{f_idx})", fontsize=8)
                else:
                    ax.set_title(f"f{f_idx}", fontsize=8)
    plt.tight_layout()
    sheet_path = SHEETS_DIR / "sheet_e1_seed201_203_progression.jpg"
    plt.savefig(sheet_path, dpi=150)
    plt.close()
    print(f"Progression contact sheet saved to {sheet_path}")
    
    print("\n=== All Evaluation and Replication Steps Successfully Completed ===")

if __name__ == "__main__":
    main()
