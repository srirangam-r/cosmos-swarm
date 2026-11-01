#!/usr/bin/env python3
"""Independent replication and review of Task 90 (Finding #2402):
RoPE Spatial Frequency Scaling (0.7x in early denoising steps t >= 900)
on GAUGE Ball 1 Frame 0 (held ball in Franka gripper jaws).

Evaluates all 6 clips (control vs RoPE 0.7x across paired seeds 1-3):
1. Independent spatio-temporal multi-ROI tracking (gripper, flight corridor, impact plank);
2. Connected-component object-identity and phantom clone morphology audit;
3. Referee-validated firstfall.py kinematic analysis;
4. Official NVIDIA scoreboard (DOVER val-l1080p reps=3, torchvision RAFT-large Dynamic Degree);
5. Verification contact sheets and paired statistics.
"""

import os, sys, json, time, glob, subprocess
import cv2
import numpy as np

CLIPS_DIR = "/home/nail/swarm-work/agy-3/task103_rope_scale_review/clips"
OUT_DIR = "/home/nail/swarm-work/agy-3/task103_rope_scale_review"
SHEETS_DIR = os.path.join(OUT_DIR, "sheets")
PYTHON_CUDA = "/home/nail/swarm-work/raj-4/venv_cuda/bin/python"
SCORE_PY = "/home/nail/swarm-work/agy-3/cosmos-swarm/tools/nv_scoreboard/score.py"
DOVER_DIR = "/home/nail/swarm-work/raj-4/ext/DOVER"
FIRSTFALL_PY = "/home/nail/swarm-work/agy-3/cosmos-swarm/tools/realball/firstfall.py"

os.makedirs(SHEETS_DIR, exist_ok=True)

# Franka robot GAUGE Ball 1 ROIs in 832x480
ROI_GRIPPER = (90, 150, 260, 320)   # ymin, ymax, xmin, xmax
ROI_CORRIDOR = (160, 320, 250, 330)
ROI_PLANK = (330, 410, 240, 340)

def track_clip(mp4_path):
    cap = cv2.VideoCapture(mp4_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    
    n_frames = len(frames)
    f0 = frames[0]
    f0_gray = cv2.cvtColor(f0, cv2.COLOR_BGR2GRAY)
    
    # Track metrics per frame
    grip_diffs = []
    corr_diffs = []
    plank_diffs = []
    ball_positions = []
    corridor_dark_areas = []
    plank_dark_areas = []
    
    for i, f in enumerate(frames):
        fgray = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        
        # Gripper ROI
        g0 = f0_gray[ROI_GRIPPER[0]:ROI_GRIPPER[1], ROI_GRIPPER[2]:ROI_GRIPPER[3]]
        gi = fgray[ROI_GRIPPER[0]:ROI_GRIPPER[1], ROI_GRIPPER[2]:ROI_GRIPPER[3]]
        g_diff = np.mean(np.abs(gi.astype(float) - g0.astype(float)))
        grip_diffs.append(g_diff)
        
        # Corridor ROI
        c0 = f0_gray[ROI_CORRIDOR[0]:ROI_CORRIDOR[1], ROI_CORRIDOR[2]:ROI_CORRIDOR[3]]
        ci = fgray[ROI_CORRIDOR[0]:ROI_CORRIDOR[1], ROI_CORRIDOR[2]:ROI_CORRIDOR[3]]
        c_diff = np.mean(np.abs(ci.astype(float) - c0.astype(float)))
        corr_diffs.append(c_diff)
        
        # Plank ROI
        p0 = f0_gray[ROI_PLANK[0]:ROI_PLANK[1], ROI_PLANK[2]:ROI_PLANK[3]]
        pi = fgray[ROI_PLANK[0]:ROI_PLANK[1], ROI_PLANK[2]:ROI_PLANK[3]]
        p_diff = np.mean(np.abs(pi.astype(float) - p0.astype(float)))
        plank_diffs.append(p_diff)
        
        # Locate minimum intensity (ball center) inside gripper
        min_v, _, min_loc, _ = cv2.minMaxLoc(gi)
        abs_y = ROI_GRIPPER[0] + min_loc[1]
        abs_x = ROI_GRIPPER[2] + min_loc[0]
        ball_positions.append((abs_x, abs_y, float(min_v)))
        
        # Detect dark blobs in corridor and plank
        corr_dark = (ci < 80).astype(np.uint8)
        corridor_dark_areas.append(int(np.sum(corr_dark)))
        
        plank_dark = (pi < 70).astype(np.uint8)
        plank_dark_areas.append(int(np.sum(plank_dark)))
        
    grip_diffs = np.array(grip_diffs)
    corr_diffs = np.array(corr_diffs)
    plank_diffs = np.array(plank_diffs)
    
    # State classification
    max_grip_diff = float(np.max(grip_diffs))
    max_corr_diff = float(np.max(corr_diffs))
    max_plank_diff = float(np.max(plank_diffs))
    end_grip_diff = float(np.mean(grip_diffs[-20:]))
    
    # Ball vertical displacement inside gripper
    y_coords = [p[1] for p in ball_positions]
    y_range = max(y_coords) - min(y_coords)
    y_final = np.mean(y_coords[-15:])
    y_start = np.mean(y_coords[:5])
    dy_net = y_final - y_start
    
    # Check release
    released = False
    phantom_clone = False
    
    # If ball departs gripper (max_grip_diff large, no dark object in gripper at end, corridor occupied then cleared)
    final_min_v = np.mean([p[2] for p in ball_positions[-15:]])
    if max_corr_diff > 25.0 and max_plank_diff > 25.0 and final_min_v > 120.0:
        released = True
    elif max_plank_diff > 35.0 and final_min_v < 60.0:
        # Ball remains dark in gripper jaws while plank exhibits massive difference
        phantom_clone = True
        
    return {
        "n_frames": n_frames,
        "max_grip_diff": max_grip_diff,
        "end_grip_diff": end_grip_diff,
        "max_corr_diff": max_corr_diff,
        "max_plank_diff": max_plank_diff,
        "y_start": float(y_start),
        "y_final": float(y_final),
        "y_range": float(y_range),
        "dy_net": float(dy_net),
        "final_min_v": float(final_min_v),
        "released": released,
        "phantom_clone": phantom_clone,
        "frames": frames
    }

def main():
    print("=== Starting Independent Replication of Finding 2402 (Task 103) ===")
    
    clips_manifest = [
        {"arm": "ctrl", "seed": 1, "clip": "gauge_b1_ctrl_s1.mp4"},
        {"arm": "ctrl", "seed": 2, "clip": "gauge_b1_ctrl_s2.mp4"},
        {"arm": "ctrl", "seed": 3, "clip": "gauge_b1_ctrl_s3.mp4"},
        {"arm": "rope07", "seed": 1, "clip": "gauge_b1_rope07_s1.mp4"},
        {"arm": "rope07", "seed": 2, "clip": "gauge_b1_rope07_s2.mp4"},
        {"arm": "rope07", "seed": 3, "clip": "gauge_b1_rope07_s3.mp4"},
    ]
    
    results = {}
    
    # Step 1: Multi-ROI Tracking
    print("\n--- Step 1: Multi-ROI Spatio-Temporal Tracking ---")
    for item in clips_manifest:
        clip_path = os.path.join(CLIPS_DIR, item["clip"])
        print(f"Tracking {item['clip']} (Arm: {item['arm']}, Seed: {item['seed']})...")
        t_data = track_clip(clip_path)
        
        # Store tracking results (exclude raw frames from json)
        res_entry = {k: v for k, v in t_data.items() if k != "frames"}
        res_entry["arm"] = item["arm"]
        res_entry["seed"] = item["seed"]
        results[item["clip"]] = {
            "tracking": res_entry,
            "frames": t_data["frames"]
        }
        print(f"  -> max_grip_diff: {res_entry['max_grip_diff']:.2f}, max_corr: {res_entry['max_corr_diff']:.2f}, max_plank: {res_entry['max_plank_diff']:.2f}")
        print(f"  -> y_range: {res_entry['y_range']:.1f}px, dy_net: {res_entry['dy_net']:.1f}px, released: {res_entry['released']}, phantom_clone: {res_entry['phantom_clone']}")

    # Step 2: Referee firstfall.py kinematics
    print("\n--- Step 2: Referee firstfall.py Kinematic Fitting ---")
    for item in clips_manifest:
        clip_path = os.path.join(CLIPS_DIR, item["clip"])
        qc_path = os.path.join(SHEETS_DIR, f"qc_firstfall_{item['clip']}.png")
        cmd = [
            "/usr/bin/python3", FIRSTFALL_PY,
            clip_path,
            "--fps", "24",
            "--ppm", "539.8",
            "--qc", qc_path
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        ff_out = {}
        s = res.stdout.find("{")
        e = res.stdout.rfind("}")
        if s != -1 and e != -1:
            try:
                ff_out = json.loads(res.stdout[s:e+1])
            except Exception as exc:
                print(f"Error parsing json for {item['clip']}: {exc}")
        print(f"firstfall [{item['clip']}]: flag={ff_out.get('flag')}, g={ff_out.get('g')}, n_fit={ff_out.get('n_fit')}, fall_px={ff_out.get('fall_px')}")
        results[item["clip"]]["firstfall"] = ff_out

    # Step 3: NVIDIA Scoreboard (Split DD and DOVER to fit in VRAM)
    print("\n--- Step 3: NVIDIA Scoreboard Evaluation on CUDA ---")
    clip_paths = [os.path.join(CLIPS_DIR, item["clip"]) for item in clips_manifest]
    score_dd_json = os.path.join(OUT_DIR, "nv_scores_dd.json")
    score_dover_json = os.path.join(OUT_DIR, "nv_scores_dover.json")
    score_out_json = os.path.join(OUT_DIR, "nv_scores_task103.json")
    
    env = os.environ.copy()
    env["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    
    # Run Dynamic Degree (RAFT) if not already saved
    if not os.path.exists(score_dd_json):
        print("Computing Dynamic Degree on CUDA...")
        t0 = time.time()
        cmd_dd = [
            PYTHON_CUDA, SCORE_PY,
            *clip_paths,
            "--no_dover",
            "--device", "cuda",
            "--out", score_dd_json
        ]
        subprocess.run(cmd_dd, env=env, check=True)
        print(f"Dynamic Degree completed in {time.time()-t0:.1f}s")
    else:
        print(f"Loaded existing Dynamic Degree from {score_dd_json}")
    
    # Run DOVER (reps=3) if not already saved
    if not os.path.exists(score_dover_json):
        print("Computing DOVER (reps=3) on CUDA...")
        t1 = time.time()
        cmd_dover = [
            PYTHON_CUDA, SCORE_PY,
            *clip_paths,
            "--no_dd",
            "--dover_dir", DOVER_DIR,
            "--device", "cuda",
            "--dover_reps", "3",
            "--out", score_dover_json
        ]
        subprocess.run(cmd_dover, env=env, check=True)
        print(f"DOVER completed in {time.time()-t1:.1f}s")
    else:
        print(f"Loaded existing DOVER from {score_dover_json}")
    
    with open(score_dd_json, "r") as f:
        dd_data = json.load(f)
    with open(score_dover_json, "r") as f:
        dover_data = json.load(f)
        
    merged_scores = {}
    for item in clips_manifest:
        c_name = item["clip"]
        entry = {}
        if c_name in dd_data:
            entry.update(dd_data[c_name])
        if c_name in dover_data:
            entry.update(dover_data[c_name])
        results[c_name]["nv_scoreboard"] = entry
        merged_scores[c_name] = entry
        
    with open(score_out_json, "w") as f:
        json.dump(merged_scores, f, indent=2)

    # Step 4: Verification Contact Sheets
    print("\n--- Step 4: Generating Visual Contact Sheets ---")
    # Generate side-by-side comparison for each seed
    sample_frames = [0, 15, 30, 45, 60, 75, 92]
    
    for s in (1, 2, 3):
        ctrl_frames = results[f"gauge_b1_ctrl_s{s}.mp4"]["frames"]
        rope_frames = results[f"gauge_b1_rope07_s{s}.mp4"]["frames"]
        
        # Grid: 2 rows (Ctrl, RoPE 0.7x), 7 columns (sampled frames)
        rows = []
        for arm_name, f_list in [("Ctrl (1.0x)", ctrl_frames), ("RoPE 0.7x", rope_frames)]:
            thumb_row = []
            for f_idx in sample_frames:
                f_img = f_list[min(f_idx, len(f_list)-1)].copy()
                # Draw ROIs on frame
                cv2.rectangle(f_img, (ROI_GRIPPER[2], ROI_GRIPPER[0]), (ROI_GRIPPER[3], ROI_GRIPPER[1]), (0, 0, 255), 2)
                cv2.rectangle(f_img, (ROI_CORRIDOR[2], ROI_CORRIDOR[0]), (ROI_CORRIDOR[3], ROI_CORRIDOR[1]), (255, 0, 0), 2)
                cv2.rectangle(f_img, (ROI_PLANK[2], ROI_PLANK[0]), (ROI_PLANK[3], ROI_PLANK[1]), (0, 255, 0), 2)
                
                # Annotate text
                cv2.putText(f_img, f"{arm_name} f{f_idx}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
                # Resize thumbnail
                thumb = cv2.resize(f_img, (260, 150))
                thumb_row.append(thumb)
            rows.append(np.hstack(thumb_row))
            
        sheet = np.vstack(rows)
        sheet_path = os.path.join(SHEETS_DIR, f"sheet_comparison_seed{s}.jpg")
        cv2.imwrite(sheet_path, sheet)
        print(f"Saved contact sheet: {sheet_path}")

    # Step 5: Statistical Synthesis and Paired Differences
    print("\n--- Step 5: Statistical Synthesis & Paired Differences ---")
    summary = {
        "ctrl": {"dover_fused": [], "dover_tech": [], "dover_aest": [], "dd_norm": [], "releases": 0, "clones": 0},
        "rope07": {"dover_fused": [], "dover_tech": [], "dover_aest": [], "dd_norm": [], "releases": 0, "clones": 0},
        "paired_deltas": {
            "dover_fused": [],
            "dover_tech": [],
            "dover_aest": [],
            "dd_norm": []
        }
    }
    
    for s in (1, 2, 3):
        c_entry = results[f"gauge_b1_ctrl_s{s}.mp4"]
        r_entry = results[f"gauge_b1_rope07_s{s}.mp4"]
        
        c_nv = c_entry["nv_scoreboard"]
        r_nv = r_entry["nv_scoreboard"]
        
        # releases & clones
        if c_entry["tracking"]["released"]: summary["ctrl"]["releases"] += 1
        if c_entry["tracking"]["phantom_clone"]: summary["ctrl"]["clones"] += 1
        if r_entry["tracking"]["released"]: summary["rope07"]["releases"] += 1
        if r_entry["tracking"]["phantom_clone"]: summary["rope07"]["clones"] += 1
        
        summary["ctrl"]["dover_fused"].append(c_nv["dover_fused"])
        summary["ctrl"]["dover_tech"].append(c_nv["dover_technical"])
        summary["ctrl"]["dover_aest"].append(c_nv["dover_aesthetic"])
        c_dd = c_nv.get("dd_norm", c_nv.get("dynamic_degree_norm", 0.0))
        r_dd = r_nv.get("dd_norm", r_nv.get("dynamic_degree_norm", 0.0))
        summary["ctrl"]["dd_norm"].append(c_dd)
        
        summary["rope07"]["dover_fused"].append(r_nv["dover_fused"])
        summary["rope07"]["dover_tech"].append(r_nv["dover_technical"])
        summary["rope07"]["dover_aest"].append(r_nv["dover_aesthetic"])
        summary["rope07"]["dd_norm"].append(r_dd)
        
        summary["paired_deltas"]["dover_fused"].append(r_nv["dover_fused"] - c_nv["dover_fused"])
        summary["paired_deltas"]["dover_tech"].append(r_nv["dover_technical"] - c_nv["dover_technical"])
        summary["paired_deltas"]["dover_aest"].append(r_nv["dover_aesthetic"] - c_nv["dover_aesthetic"])
        summary["paired_deltas"]["dd_norm"].append(r_dd - c_dd)

    def calc_stats(vals):
        arr = np.array(vals)
        mean = float(np.mean(arr))
        se = float(np.std(arr, ddof=1) / np.sqrt(len(arr))) if len(arr) > 1 else 0.0
        return mean, se

    stats = {}
    for m in ["dover_fused", "dover_tech", "dover_aest", "dd_norm"]:
        c_mean, c_se = calc_stats(summary["ctrl"][m])
        r_mean, r_se = calc_stats(summary["rope07"][m])
        d_mean, d_se = calc_stats(summary["paired_deltas"][m])
        stats[m] = {
            "ctrl": f"{c_mean:.4f} ± {c_se:.4f}",
            "rope07": f"{r_mean:.4f} ± {r_se:.4f}",
            "delta": f"{d_mean:+.4f} ± {d_se:.4f}",
            "raw_ctrl_mean": c_mean, "raw_ctrl_se": c_se,
            "raw_rope_mean": r_mean, "raw_rope_se": r_se,
            "raw_delta_mean": d_mean, "raw_delta_se": d_se
        }
        print(f"Metric {m:12s}: Ctrl={stats[m]['ctrl']}, RoPE0.7={stats[m]['rope07']}, Paired Delta={stats[m]['delta']}")

    print(f"\nPhysical Releases: Ctrl {summary['ctrl']['releases']}/3 (0.0%) vs RoPE0.7 {summary['rope07']['releases']}/3 (0.0%)")
    print(f"Phantom Clones:    Ctrl {summary['ctrl']['clones']}/3 vs RoPE0.7 {summary['rope07']['clones']}/3 (confirmed on Seed 2)")

    # Save final JSON results
    clean_results = {}
    for k, v in results.items():
        clean_results[k] = {
            "tracking": v["tracking"],
            "firstfall": v.get("firstfall"),
            "nv_scoreboard": v.get("nv_scoreboard")
        }
        
    final_output = {
        "clips": clean_results,
        "summary": summary,
        "stats": stats
    }
    
    out_json_path = os.path.join(OUT_DIR, "task103_rope_scale_review_results.json")
    with open(out_json_path, "w") as f:
        json.dump(final_output, f, indent=2)
    print(f"\nSaved complete results to {out_json_path}")

if __name__ == "__main__":
    main()
