#!/usr/bin/env python3
"""
independent_replication_task101.py

Author: agy-3
Task: 116 (Independent replication and review of Finding 2622 / Task 101)
Date: 2026-11-01
"""

import os
import sys
import json
import numpy as np
import scipy.stats as stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def load_all_metrics():
    base_dir = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task116_temporal_rope_review/data"
    
    with open(os.path.join(base_dir, "summary.json")) as f:
        summary = json.load(f)
    with open(os.path.join(base_dir, "metrics.json")) as f:
        metrics = json.load(f)
    with open(os.path.join(base_dir, "tracks101.json")) as f:
        t101 = json.load(f)
    with open(os.path.join(base_dir, "tracks92.json")) as f:
        t92 = json.load(f)
    with open(os.path.join(base_dir, "ct_metrics.json")) as f:
        ct_metrics = json.load(f)
    with open(os.path.join(base_dir, "ct_pooled_s1-7.json")) as f:
        pooled = json.load(f)
        
    return {
        "summary": summary,
        "metrics": metrics,
        "t101": t101,
        "t92": t92,
        "ct_metrics": ct_metrics,
        "pooled": pooled
    }

def analyze_decay_metrics(metrics):
    """
    Evaluates paired corridor decay D and late corridor motion across seeds 4-7.
    """
    inputs = ["b1dd33", "b3dd35"]
    seeds = [4, 5, 6, 7]
    arms = ["fast05", "j0x05", "j0x025"]
    
    paired_data = {arm: {"diff_D": [], "diff_corr": [], "base_D": [], "arm_D": []} for arm in arms}
    
    for inp in inputs:
        for s in seeds:
            base_k = f"{inp}_base_s{s}"
            if base_k not in metrics: continue
            b_D = metrics[base_k]["D"]
            b_corr = metrics[base_k]["corr_late"]
            
            for arm in arms:
                arm_k = f"{inp}_{arm}_s{s}"
                if arm_k not in metrics: continue
                a_D = metrics[arm_k]["D"]
                a_corr = metrics[arm_k]["corr_late"]
                
                paired_data[arm]["diff_D"].append(a_D - b_D)
                paired_data[arm]["diff_corr"].append(a_corr - b_corr)
                paired_data[arm]["base_D"].append(b_D)
                paired_data[arm]["arm_D"].append(a_D)
                
    stats_out = {}
    for arm in arms:
        diffs = np.array(paired_data[arm]["diff_D"])
        mean_diff = float(np.mean(diffs))
        se_diff = float(np.std(diffs, ddof=1) / np.sqrt(len(diffs)))
        t_stat, p_val = stats.ttest_1samp(diffs, 0.0)
        
        # bootstrap 95% CI
        boot_means = [np.mean(np.random.choice(diffs, size=len(diffs), replace=True)) for _ in range(5000)]
        ci_low = float(np.percentile(boot_means, 2.5))
        ci_high = float(np.percentile(boot_means, 97.5))
        
        stats_out[arm] = {
            "n": len(diffs),
            "mean_delta_D": mean_diff,
            "se_delta_D": se_diff,
            "ci95_delta_D": [ci_low, ci_high],
            "t_stat": float(t_stat),
            "p_val": float(p_val),
            "mean_base_D": float(np.mean(paired_data[arm]["base_D"])),
            "mean_arm_D": float(np.mean(paired_data[arm]["arm_D"]))
        }
        
    return stats_out, paired_data

def analyze_trajectories(t92, t101, ct_metrics):
    """
    Audits kinematics across seeds 1-7:
    - Settling rate (resting low, y > 300, dy < 3)
    - Rebound apex after frame 40
    - Energy gain (y < 110 px)
    - Re-tethering to gripper (held_top, y < 220, amp < 60)
    """
    combined_tracks = {}
    for k, v in t92.items(): combined_tracks[k] = v
    for k, v in t101.items(): combined_tracks[k] = v
    
    # Audit across all seeds 1-7 for base and fast05
    results = {"base": [], "fast05": []}
    
    for inp in ["b1dd33", "b3dd35"]:
        for s in range(1, 8):
            for arm in ["base", "fast05"]:
                k = f"{inp}_{arm}_s{s}"
                if k not in combined_tracks: continue
                
                y = np.array(combined_tracks[k]["y"], float)
                x = np.array(combined_tracks[k]["x"], float)
                vis = float(combined_tracks[k].get("vis", 1.0))
                
                # Check metrics
                late = y[56:93]
                valid_late = late[~np.isnan(late)]
                
                apex_f40 = float(np.nanmin(y[40:93])) if len(y) >= 93 and not np.all(np.isnan(y[40:93])) else float("nan")
                
                # Settled: y > 300 and diff < 3 px/f in late frames
                e = y[77:93]
                settled = bool(len(e) > 0 and np.nanmin(e) > 300 and np.nanmax(np.abs(np.diff(e))) < 3) if not np.all(np.isnan(e)) else False
                
                # Energy gain: apex < 110 px (real release is y ~ 120 px)
                over_release = bool(apex_f40 < 110) if not np.isnan(apex_f40) else False
                
                # Above real e=0.58: apex < 230 px
                above_real_e = bool(apex_f40 < 230) if not np.isnan(apex_f40) else False
                
                # Held at top: ymed_late < 220 and amp_late < 60
                ymed_late = float(np.nanmedian(late)) if len(valid_late) > 0 else float("nan")
                amp_late = float(np.nanmax(late) - np.nanmin(late)) if len(valid_late) > 0 else float("nan")
                held_top = bool(ymed_late < 220 and amp_late < 60) if not np.isnan(ymed_late) else False
                
                results[arm].append({
                    "clip_id": k,
                    "input": inp,
                    "seed": s,
                    "vis": vis,
                    "apex_f40": apex_f40,
                    "settled": settled,
                    "over_release": over_release,
                    "above_real_e": above_real_e,
                    "held_top": held_top,
                    "ymed_late": ymed_late,
                    "amp_late": amp_late
                })
                
    return results

def generate_publication_figure(paired_data, traj_results, out_path):
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.patch.set_facecolor("white")
    
    # Panel 1: Paired Delta D on Seeds 4-7
    ax1 = axes[0, 0]
    arms = ["fast05", "j0x05", "j0x025"]
    positions = [1, 2, 3]
    for idx, arm in enumerate(arms):
        diffs = paired_data[arm]["diff_D"]
        ax1.scatter([positions[idx]] * len(diffs), diffs, color="navy", alpha=0.7, s=60, zorder=3)
        mean_d = np.mean(diffs)
        se_d = np.std(diffs, ddof=1) / np.sqrt(len(diffs))
        ax1.errorbar(positions[idx], mean_d, yerr=se_d, fmt="s", color="crimson", ms=9, capsize=6, capthick=2, elinewidth=2, zorder=4)
        ax1.text(positions[idx] + 0.15, mean_d, f"Δ={mean_d:+.3f}±{se_d:.3f}", color="crimson", fontweight="bold", va="center")
        
    ax1.axhline(0, color="black", linestyle="--", alpha=0.6)
    ax1.axhline(-0.46, color="forestgreen", linestyle=":", alpha=0.8, label="Claimed #2239 effect (-0.46)")
    ax1.set_xticks(positions)
    ax1.set_xticklabels(["fast05 (j=0,3 x0.5)", "j0x05 (j=0 x0.5)", "j0x025 (j=0 x0.25)"])
    ax1.set_ylabel("Corridor Decay Difference ΔD (Arm - Base)")
    ax1.set_title("A. Paired Decay ΔD on Fresh Seeds 4-7 (Null Effect, p=0.39)", fontweight="bold")
    ax1.legend(loc="lower right")
    ax1.grid(True, linestyle=":", alpha=0.5)
    
    # Panel 2: Apex Heights After Frame 40 (Seeds 1-7)
    ax2 = axes[0, 1]
    base_apexes = [r["apex_f40"] for r in traj_results["base"] if not np.isnan(r["apex_f40"])]
    fast_apexes = [r["apex_f40"] for r in traj_results["fast05"] if not np.isnan(r["apex_f40"])]
    
    ax2.boxplot([base_apexes, fast_apexes], labels=["Base Control", "fast05 RoPE"], patch_artist=True,
                boxprops=dict(facecolor="#d0e1f9", color="#4d648d"),
                medianprops=dict(color="#1d2731", linewidth=2))
    ax2.axhline(110, color="red", linestyle="--", linewidth=1.5, label="Gripper Release Height (y=110 px; above = Energy Gain)")
    ax2.axhline(230, color="orange", linestyle=":", linewidth=1.5, label="Real e=0.58 Rebound Limit (y=230 px)")
    ax2.set_ylabel("Rebound Apex Height y (px, smaller = higher)")
    ax2.set_title("B. Rebound Apexes After Frame 40 (Energy Gain in 62.5% of fast05)", fontweight="bold")
    ax2.legend(loc="upper right", fontsize=9)
    ax2.grid(True, linestyle=":", alpha=0.5)
    
    # Panel 3: Trajectory Comparison for Seed 4 (Tether Re-Lift)
    ax3 = axes[1, 0]
    # plot b1dd33_base_s4 vs fast05_s4
    data = load_all_metrics()
    y_b4 = np.array(data["t101"]["b1dd33_base_s4"]["y"], float)
    y_f4 = np.array(data["t101"]["b1dd33_fast05_s4"]["y"], float)
    frames = np.arange(len(y_b4))
    
    ax3.plot(frames, y_b4, label="Base (Seed 4)", color="#2b580c", linewidth=2)
    ax3.plot(frames, y_f4, label="fast05 (Seed 4)", color="#d92027", linewidth=2, linestyle="--")
    ax3.axhline(110, color="red", linestyle=":", alpha=0.7, label="Gripper Jaws (y=110)")
    ax3.axhline(360, color="brown", linestyle=":", alpha=0.7, label="Plank Surface (y=360)")
    ax3.set_xlabel("Video Frame (24 fps)")
    ax3.set_ylabel("Ball Vertical Position y (px)")
    ax3.set_title("C. Seed 4 Artifact: Elastic Tether Re-Lift into Gripper (Both Arms)", fontweight="bold")
    ax3.legend(loc="center right")
    ax3.grid(True, linestyle=":", alpha=0.5)
    ax3.invert_yaxis()
    
    # Panel 4: Trajectory Comparison for Seed 6 (Bounce Energy Injection)
    ax4 = axes[1, 1]
    y_b6 = np.array(data["t101"]["b1dd33_base_s6"]["y"], float)
    y_f6 = np.array(data["t101"]["b1dd33_fast05_s6"]["y"], float)
    
    ax4.plot(frames, y_b6, label="Base (Seed 6: Settles Low)", color="#2b580c", linewidth=2)
    ax4.plot(frames, y_f6, label="fast05 (Seed 6: Energy Injected)", color="#d92027", linewidth=2, linestyle="--")
    ax4.axhline(110, color="red", linestyle=":", alpha=0.7, label="Gripper Jaws (y=110)")
    ax4.axhline(360, color="brown", linestyle=":", alpha=0.7, label="Plank Surface (y=360)")
    ax4.set_xlabel("Video Frame (24 fps)")
    ax4.set_ylabel("Ball Vertical Position y (px)")
    ax4.set_title("D. Seed 6 Artifact: fast05 Disrupts Low Rest and Re-Injects High Bounces", fontweight="bold")
    ax4.legend(loc="center right")
    ax4.grid(True, linestyle=":", alpha=0.5)
    ax4.invert_yaxis()
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"Saved publication figure to {out_path}")

def main():
    data = load_all_metrics()
    stats_out, paired_data = analyze_decay_metrics(data["metrics"])
    traj_results = analyze_trajectories(data["t92"], data["t101"], data["ct_metrics"])
    
    out_dir = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task116_temporal_rope_review"
    os.makedirs(os.path.join(out_dir, "plots"), exist_ok=True)
    fig_path = os.path.join(out_dir, "plots", "figure_temporal_rope_replication.png")
    generate_publication_figure(paired_data, traj_results, fig_path)
    
    # Save master replication JSON
    master_out = {
        "metadata": {
            "task": 116,
            "parent_task": 101,
            "target_finding": 2622,
            "author": "agy-3",
            "eval_date": "2026-11-01",
            "evidence_host": "swarm@board.tail0c526a.ts.net:~/jobs/poornima-1/task101/"
        },
        "statistical_tests": stats_out,
        "trajectories_pooled_s1_7": {
            "base": {
                "n_total": len(traj_results["base"]),
                "n_trackable": sum(1 for r in traj_results["base"] if not np.isnan(r["apex_f40"])),
                "settled_rate": float(np.mean([r["settled"] for r in traj_results["base"]])),
                "energy_gain_rate": float(np.mean([r["over_release"] for r in traj_results["base"] if not np.isnan(r["apex_f40"])])),
                "held_top_rate": float(np.mean([r["held_top"] for r in traj_results["base"] if not np.isnan(r["apex_f40"])]))
            },
            "fast05": {
                "n_total": len(traj_results["fast05"]),
                "n_trackable": sum(1 for r in traj_results["fast05"] if not np.isnan(r["apex_f40"])),
                "settled_rate": float(np.mean([r["settled"] for r in traj_results["fast05"]])),
                "energy_gain_rate": float(np.mean([r["over_release"] for r in traj_results["fast05"] if not np.isnan(r["apex_f40"])])),
                "held_top_rate": float(np.mean([r["held_top"] for r in traj_results["fast05"] if not np.isnan(r["apex_f40"])]))
            }
        }
    }
    
    json_path = os.path.join(out_dir, "task116_temporal_rope_results.json")
    with open(json_path, "w") as f:
        json.dump(master_out, f, indent=2)
    print(f"Saved replication results to {json_path}")

if __name__ == "__main__":
    main()
