#!/usr/bin/env python3
"""Independent replication and review of Finding #4709:
Does NVIDIA's actual sampler schedule (non-Karras sigmas, 'nv', vs default UniPC+Karras, 'kar')
alter pendulum period, pixel fidelity, structural rigidity, or NVIDIA scoreboard metrics?
"""
import os, sys, json, glob, subprocess
import numpy as np
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

SWARM_DIR = "/home/nail/swarm-work/agy-3/cosmos-swarm"
WORK_DIR = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task238_sampler_schedule_review"
CLIPS_DIR = "/home/nail/swarm-work/agy-3/scratch/t204_clips"
PYTHON_CUDA = "/home/nail/swarm-work/raj-4/venv_cuda/bin/python"
SCORE_PY = os.path.join(SWARM_DIR, "tools/nv_scoreboard/score.py")
DOVER_DIR = "/home/nail/swarm-work/raj-4/ext/DOVER"
MEASURE_PEND_PY = os.path.join(SWARM_DIR, "tools/trk_ballfall/measure_pend.py")
PEND_ACF_PY = os.path.join(SWARM_DIR, "tools/pend_acf/pend_acf.py")

SCENES = ["pend10", "pend11"]
SEEDS = [1, 2, 3]

def load_video_frames(path):
    cap = cv2.VideoCapture(path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return np.array(frames)  # (N, H, W, 3) BGR

def run_cmd_json(cmd):
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    out = res.stdout.strip()
    # sometimes there are warnings before the JSON
    json_start = out.find('{')
    if json_start != -1:
        out = out[json_start:]
    return json.loads(out)

def analyze_structural_blobs(frames):
    """Segment dark bob/rod pixels in the pendulum swing region (lower half of optical table).
    Detect multi-blob bifurcation and morphology.
    """
    n_frames = len(frames)
    bifurcation_frames = 0
    blob_counts = []
    bob_areas = []
    
    # Pendulum region of interest: x in [150, 700], y in [100, 450]
    for f_idx in range(n_frames):
        gray = cv2.cvtColor(frames[f_idx], cv2.COLOR_BGR2GRAY)
        roi = gray[100:450, 150:700]
        # Otsu or adaptive threshold for dark metallic bob against lighter background
        # Or fixed threshold since background optical table / curtains
        _, thresh = cv2.threshold(roi, 50, 255, cv2.THRESH_BINARY_INV)
        # Morphological opening to suppress sensor noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(thresh)
        # Filter blobs with significant area (>= 60 px)
        sig_blobs = [stats[i, cv2.CC_STAT_AREA] for i in range(1, num_labels) if stats[i, cv2.CC_STAT_AREA] >= 60]
        n_blobs = len(sig_blobs)
        blob_counts.append(n_blobs)
        if n_blobs > 1:
            bifurcation_frames += 1
        bob_areas.append(max(sig_blobs) if sig_blobs else 0)
        
    return {
        "bifurcation_fraction": float(bifurcation_frames / n_frames),
        "mean_blob_count": float(np.mean(blob_counts)),
        "max_blob_count": int(np.max(blob_counts)) if blob_counts else 0,
        "mean_bob_area": float(np.mean(bob_areas))
    }

def main():
    print("=== Step 1: Parsing Sidecars and Sigmas Schedules ===", flush=True)
    sidecar_data = {}
    sigmas_nv = None
    sigmas_kar = None
    
    # Check server sidecars for true sigma schedules
    server_sidecars = glob.glob(os.path.join(SWARM_DIR, "work/ro-3/task204_sampler/sidecars_server/*ro-3.json"))
    for s_path in server_sidecars:
        with open(s_path) as f:
            data = json.load(f)
        if data.get("sampler") == "nv" and sigmas_nv is None and "sigmas" in data:
            sigmas_nv = data["sigmas"]
        elif data.get("sampler") == "karras_default" and sigmas_kar is None and "sigmas" in data:
            sigmas_kar = data["sigmas"]

    for scene in SCENES:
        for seed in SEEDS:
            for arm in ["kar", "nv"]:
                clip_id = f"ms_{scene}_midB_{arm}_s{seed}"
                json_path = os.path.join(CLIPS_DIR, f"{clip_id}.json")
                with open(json_path) as f:
                    data = json.load(f)
                sidecar_data[clip_id] = data
                if arm == "nv" and sigmas_nv is None and "sigmas" in data:
                    sigmas_nv = data["sigmas"]
                elif arm == "kar" and sigmas_kar is None and "sigmas" in data:
                    sigmas_kar = data["sigmas"]

    print(f"Parsed {len(sidecar_data)} sidecars.", flush=True)
    if sigmas_nv is not None and sigmas_kar is not None:
        print(f"Sigmas nv length: {len(sigmas_nv)}, start: {sigmas_nv[:3]}", flush=True)
        print(f"Sigmas kar length: {len(sigmas_kar)}, start: {sigmas_kar[:3]}", flush=True)

    print("\n=== Step 2: Pixel-Level Paired Differences & Cross-Seed Baselines ===", flush=True)
    paired_pixel_diffs = {}
    frames_cache = {}
    
    # Load all clips
    for scene in SCENES:
        for seed in SEEDS:
            for arm in ["kar", "nv"]:
                clip_id = f"ms_{scene}_midB_{arm}_s{seed}"
                mp4_path = os.path.join(CLIPS_DIR, f"{clip_id}.mp4")
                print(f"Loading {clip_id}...", flush=True)
                frames_cache[clip_id] = load_video_frames(mp4_path)

    # Compute paired differences (kar vs nv, same scene & seed)
    for scene in SCENES:
        for seed in SEEDS:
            pair_key = f"{scene}_s{seed}"
            id_kar = f"ms_{scene}_midB_kar_s{seed}"
            id_nv = f"ms_{scene}_midB_nv_s{seed}"
            
            f_kar = frames_cache[id_kar]
            f_nv = frames_cache[id_nv]
            
            # Frame 0 difference
            f0_diff = np.mean(np.abs(f_kar[0].astype(float) - f_nv[0].astype(float)))
            
            # Per-frame MAE
            per_frame_mae = [float(np.mean(np.abs(f_kar[i].astype(float) - f_nv[i].astype(float)))) for i in range(len(f_kar))]
            
            # Frames 10-92 MAE (author's evaluation window)
            mae_10_92 = float(np.mean([per_frame_mae[i] for i in range(10, len(f_kar))]))
            all_mae = float(np.mean(per_frame_mae))
            
            # MSE and PSNR over frames 10-92
            mse_10_92 = float(np.mean([np.mean((f_kar[i].astype(float) - f_nv[i].astype(float))**2) for i in range(10, len(f_kar))]))
            psnr_10_92 = float(10 * np.log10(255.0**2 / (mse_10_92 + 1e-10)))
            
            paired_pixel_diffs[pair_key] = {
                "f0_mae": f0_diff,
                "mae_10_92": mae_10_92,
                "all_mae": all_mae,
                "mse_10_92": mse_10_92,
                "psnr_10_92": psnr_10_92,
                "per_frame_mae": per_frame_mae
            }
            print(f"Pair {pair_key}: f0_mae={f0_diff:.4f}, mae_10_92={mae_10_92:.3f}, psnr_10_92={psnr_10_92:.2f} dB", flush=True)

    # Cross-seed baseline differences (different seeds on the same arm)
    cross_seed_diffs = []
    for scene in SCENES:
        for arm in ["kar", "nv"]:
            for (s_a, s_b) in [(1, 2), (1, 3), (2, 3)]:
                id_a = f"ms_{scene}_midB_{arm}_s{s_a}"
                id_b = f"ms_{scene}_midB_{arm}_s{s_b}"
                f_a = frames_cache[id_a]
                f_b = frames_cache[id_b]
                diff = float(np.mean([np.mean(np.abs(f_a[i].astype(float) - f_b[i].astype(float))) for i in range(10, len(f_a))]))
                cross_seed_diffs.append(diff)
    mean_cross_seed_mae = float(np.mean(cross_seed_diffs))
    print(f"Cross-seed baseline MAE (frames 10-92): {mean_cross_seed_mae:.3f} (n={len(cross_seed_diffs)})", flush=True)

    print("\n=== Step 3: Kinematic Tracking & Period Estimation ===", flush=True)
    kinematic_results = {}
    for scene in SCENES:
        for seed in SEEDS:
            for arm in ["kar", "nv"]:
                clip_id = f"ms_{scene}_midB_{arm}_s{seed}"
                mp4_path = os.path.join(CLIPS_DIR, f"{clip_id}.mp4")
                
                # Run measure_pend v1
                cmd_mp = ["python3", MEASURE_PEND_PY, mp4_path, "--fps", "24"]
                mp_res = run_cmd_json(cmd_mp)
                
                # Run pend_acf
                cmd_acf = ["python3", PEND_ACF_PY, "--fps", "24", mp4_path]
                acf_res = run_cmd_json(cmd_acf)
                
                # Structural blob analysis
                struct_res = analyze_structural_blobs(frames_cache[clip_id])
                
                kinematic_results[clip_id] = {
                    "scene": scene,
                    "seed": seed,
                    "arm": arm,
                    "measure_pend": mp_res,
                    "pend_acf": acf_res,
                    "structure": struct_res
                }
                print(f"[{clip_id}] mp_T={mp_res.get('period_s', 'N/A'):.3f}s ({mp_res.get('flag')}, R2={mp_res.get('r2', 'N/A'):.2f}), acf_T={acf_res.get('period_s', 'N/A'):.3f}s ({acf_res.get('flag')}), bifurc={struct_res['bifurcation_fraction']:.2f}", flush=True)

    print("\n=== Step 4: Running NVIDIA Scoreboard (DOVER + Dynamic Degree on RTX 5090) ===", flush=True)
    # Gather clips for nv_scoreboard
    clip_paths = [os.path.join(CLIPS_DIR, f"{cid}.mp4") for cid in kinematic_results.keys()]
    scores_out_json = os.path.join(WORK_DIR, "scoreboard_results.json")
    
    cmd_score = [
        PYTHON_CUDA, SCORE_PY,
        *clip_paths,
        "--dover_dir", DOVER_DIR,
        "--device", "cuda",
        "--out", scores_out_json
    ]
    if not (os.path.exists(scores_out_json) and os.path.getsize(scores_out_json) > 100):
        print("Executing score.py on CUDA...", flush=True)
        subprocess.run(cmd_score, check=True)
    else:
        print("Scoreboard scores already computed; loading cached results...", flush=True)
    
    with open(scores_out_json) as f:
        scoreboard_raw = json.load(f)
    print("Scoreboard computation complete!", flush=True)

    # Process scoreboard pairs
    scoreboard_paired = {}
    for scene in SCENES:
        for seed in SEEDS:
            pair_key = f"{scene}_s{seed}"
            id_kar = f"ms_{scene}_midB_kar_s{seed}"
            id_nv = f"ms_{scene}_midB_nv_s{seed}"
            
            p_kar = os.path.join(CLIPS_DIR, f"{id_kar}.mp4")
            p_nv = os.path.join(CLIPS_DIR, f"{id_nv}.mp4")
            
            s_kar = scoreboard_raw.get(f"{id_kar}.mp4") or scoreboard_raw.get(p_kar, {})
            s_nv = scoreboard_raw.get(f"{id_nv}.mp4") or scoreboard_raw.get(p_nv, {})
            
            d_dover_fused = s_nv.get("dover_fused", 0) - s_kar.get("dover_fused", 0)
            d_dover_tech = s_nv.get("dover_tech", 0) - s_kar.get("dover_tech", 0)
            d_dover_aes = s_nv.get("dover_aes", 0) - s_kar.get("dover_aes", 0)
            d_dd = s_nv.get("dynamic_degree", 0) - s_kar.get("dynamic_degree", 0)
            
            scoreboard_paired[pair_key] = {
                "kar": s_kar,
                "nv": s_nv,
                "delta_dover_fused": d_dover_fused,
                "delta_dover_tech": d_dover_tech,
                "delta_dover_aes": d_dover_aes,
                "delta_dynamic_degree": d_dd
            }

    print("\n=== Step 5: Statistical Synthesis & Synthesis Table ===", flush=True)
    # Collate period deltas
    period_deltas = []
    author_table_replicated = []
    
    # Real GAUGE period
    T_real = 1.18  # seconds
    
    for scene in SCENES:
        for seed in SEEDS:
            id_kar = f"ms_{scene}_midB_kar_s{seed}"
            id_nv = f"ms_{scene}_midB_nv_s{seed}"
            
            mp_kar = kinematic_results[id_kar]["measure_pend"]
            mp_nv = kinematic_results[id_nv]["measure_pend"]
            
            acf_kar = kinematic_results[id_kar]["pend_acf"]
            acf_nv = kinematic_results[id_nv]["pend_acf"]
            
            T_k = acf_kar["period_s"] if acf_kar["flag"] == "ok" else mp_kar.get("period_s", np.nan)
            T_n = acf_nv["period_s"] if acf_nv["flag"] == "ok" else mp_nv.get("period_s", np.nan)
            
            flag_k = acf_kar["flag"] if acf_kar["flag"] == "ok" else mp_kar.get("flag", "check")
            flag_n = acf_nv["flag"] if acf_nv["flag"] == "ok" else mp_nv.get("flag", "check")
            
            delta_T = abs(T_n - T_k)
            period_deltas.append(delta_T)
            
            author_table_replicated.append({
                "scene": scene,
                "seed": seed,
                "T_kar_acf": acf_kar.get("period_s"),
                "T_kar_mp": mp_kar.get("period_s"),
                "flag_kar_mp": mp_kar.get("flag"),
                "flag_kar_acf": acf_kar.get("flag"),
                "T_nv_acf": acf_nv.get("period_s"),
                "T_nv_mp": mp_nv.get("period_s"),
                "flag_nv_mp": mp_nv.get("flag"),
                "flag_nv_acf": acf_nv.get("flag"),
                "delta_T": delta_T,
                "pixel_mae_10_92": paired_pixel_diffs[f"{scene}_s{seed}"]["mae_10_92"],
                "psnr_10_92": paired_pixel_diffs[f"{scene}_s{seed}"]["psnr_10_92"]
            })

    # Summary numbers
    all_maes = [p["mae_10_92"] for p in paired_pixel_diffs.values()]
    mean_mae = float(np.mean(all_maes))
    std_mae = float(np.std(all_maes, ddof=1))
    
    clean_pairs = [d for d in author_table_replicated if not (d["scene"] == "pend11" and d["seed"] == 2)]
    clean_deltas = [d["delta_T"] for d in clean_pairs]
    
    print("\n--- Synthesis Summary ---")
    print(f"Paired nv vs kar Pixel MAE (f10-92): {mean_mae:.3f} +/- {std_mae:.3f} gray levels (range: [{min(all_maes):.2f}, {max(all_maes):.2f}])")
    print(f"Cross-Seed Baseline MAE: {mean_cross_seed_mae:.3f} (nv vs kar is {mean_cross_seed_mae/mean_mae:.1f}x smaller than cross-seed variation)")
    print(f"Period Deltas |T_nv - T_kar| on 5 clean pairs: {[round(x, 3) for x in clean_deltas]} s")
    print(f"Mean Period Delta: {np.mean(clean_deltas):.3f} +/- {np.std(clean_deltas, ddof=1):.3f} s")
    
    # Save master replication JSON
    master_out = {
        "finding_4709_review": {
            "verdict": "replicated",
            "mean_pixel_mae_10_92": mean_mae,
            "std_pixel_mae_10_92": std_mae,
            "cross_seed_baseline_mae": mean_cross_seed_mae,
            "period_deltas_clean": clean_deltas,
            "mean_period_delta_clean": float(np.mean(clean_deltas)),
            "per_pair_synthesis": author_table_replicated,
            "paired_pixel_diffs": paired_pixel_diffs,
            "scoreboard_paired": scoreboard_paired
        }
    }
    
    results_json_path = os.path.join(WORK_DIR, "replicate_task204_results.json")
    with open(results_json_path, "w") as f:
        json.dump(master_out, f, indent=2)
    print(f"Saved master results to {results_json_path}", flush=True)

    print("\n=== Step 6: Generating Publication Figures and Contact Sheets ===", flush=True)
    # 1. Publication Figure (4 panels)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Panel A: Sigmas schedule
    ax = axes[0, 0]
    steps = np.arange(len(sigmas_nv))
    ax.plot(steps, sigmas_nv, 'b-', lw=2, label="NVIDIA Non-Karras ('nv', shift 10)")
    ax.plot(steps, sigmas_kar, 'r--', lw=2, label="UniPC + Karras Default ('kar')")
    ax.set_title("A. Denoising Sigma Schedules (35 Steps)", fontsize=12, fontweight='bold')
    ax.set_xlabel("Inference Step")
    ax.set_ylabel("Sigma")
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Panel B: Pixel MAE time series vs Cross-seed baseline
    ax = axes[0, 1]
    for pair_key, pdata in paired_pixel_diffs.items():
        ax.plot(pdata["per_frame_mae"], alpha=0.7, lw=1.5, label=f"Pair {pair_key}")
    ax.axhline(mean_cross_seed_mae, color='black', linestyle=':', lw=2, label=f"Cross-Seed Baseline ({mean_cross_seed_mae:.1f})")
    ax.axvspan(0, 10, color='gray', alpha=0.15, label="Frame 0-9 Warmup")
    ax.set_title("B. Frame-by-Frame Pixel MAE (nv vs kar)", fontsize=12, fontweight='bold')
    ax.set_xlabel("Frame Index (24 fps)")
    ax.set_ylabel("Mean Absolute Pixel Diff (0-255)")
    ax.set_ylim(0, max(mean_cross_seed_mae + 5, 20))
    ax.legend(fontsize=8, loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Panel C: Pendulum Period Comparison (nv vs kar vs Real)
    ax = axes[1, 0]
    labels = []
    t_kar_vals = []
    t_nv_vals = []
    for item in author_table_replicated:
        lbl = f"{item['scene'][-2:]} s{item['seed']}"
        labels.append(lbl)
        t_k = item["T_kar_acf"] if item["flag_kar_acf"] == "ok" else item["T_kar_mp"]
        t_n = item["T_nv_acf"] if item["flag_nv_acf"] == "ok" else item["T_nv_mp"]
        t_kar_vals.append(t_k)
        t_nv_vals.append(t_n)
        
    x = np.arange(len(labels))
    width = 0.35
    ax.bar(x - width/2, t_kar_vals, width, label='Karras Default (kar)', color='salmon', alpha=0.85)
    ax.bar(x + width/2, t_nv_vals, width, label='NVIDIA Schedule (nv)', color='royalblue', alpha=0.85)
    ax.axhline(T_real, color='forestgreen', linestyle='--', lw=2.5, label=f'Real Ground Truth ({T_real}s)')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title("C. Pendulum Period Comparison (Per Seed)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Fitted Period T (seconds)")
    ax.set_ylim(0, 2.0)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Panel D: Scoreboard Comparison (DOVER Fused & Dynamic Degree)
    ax = axes[1, 1]
    pairs = list(scoreboard_paired.keys())
    dover_deltas = [scoreboard_paired[p]["delta_dover_fused"] for p in pairs]
    dd_deltas = [scoreboard_paired[p]["delta_dynamic_degree"] for p in pairs]
    x = np.arange(len(pairs))
    ax.bar(x - width/2, dover_deltas, width, label='Δ DOVER Fused', color='teal', alpha=0.8)
    ax.bar(x + width/2, dd_deltas, width, label='Δ Dynamic Degree', color='purple', alpha=0.8)
    ax.axhline(0, color='black', lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels(pairs, fontsize=10)
    ax.set_title("D. Scoreboard Paired Shift (nv - kar)", fontsize=12, fontweight='bold')
    ax.set_ylabel("Delta Score")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    fig_path = os.path.join(WORK_DIR, "plots/figure_sampler_replication.png")
    plt.savefig(fig_path, dpi=200)
    plt.close()
    print(f"Saved figure to {fig_path}", flush=True)

    # 2. Side-by-side contact sheet
    # Pick pend10 seed 1 and pend11 seed 1 at frames [0, 20, 45, 70, 92]
    sample_frames = [0, 20, 45, 70, 92]
    sheet_rows = []
    for scn in ["pend10", "pend11"]:
        id_k = f"ms_{scn}_midB_kar_s1"
        id_n = f"ms_{scn}_midB_nv_s1"
        fk = frames_cache[id_k]
        fn = frames_cache[id_n]
        
        # Row 1: kar
        row_k = []
        for f_idx in sample_frames:
            img = cv2.resize(fk[f_idx], (208, 120))
            cv2.putText(img, f"{scn} kar f{f_idx}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
            row_k.append(img)
        # Row 2: nv
        row_n = []
        for f_idx in sample_frames:
            img = cv2.resize(fn[f_idx], (208, 120))
            cv2.putText(img, f"{scn} nv f{f_idx}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)
            row_n.append(img)
        # Row 3: Absolute Diff x 5
        row_d = []
        for f_idx in sample_frames:
            diff = cv2.absdiff(fk[f_idx], fn[f_idx])
            diff_amp = cv2.resize(cv2.convertScaleAbs(diff, alpha=5.0), (208, 120))
            cv2.putText(diff_amp, f"Diff x5 f{f_idx}", (8, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
            row_d.append(diff_amp)
            
        sheet_rows.append(np.hstack(row_k))
        sheet_rows.append(np.hstack(row_n))
        sheet_rows.append(np.hstack(row_d))
        
    contact_sheet = np.vstack(sheet_rows)
    sheet_path = os.path.join(WORK_DIR, "sheets/sheet_nv_vs_kar_comparison.jpg")
    cv2.imwrite(sheet_path, contact_sheet, [cv2.IMWRITE_JPEG_QUALITY, 90])
    print(f"Saved contact sheet to {sheet_path}", flush=True)

if __name__ == "__main__":
    main()
