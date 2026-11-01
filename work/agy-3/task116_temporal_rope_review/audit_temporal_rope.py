#!/usr/bin/env python3
"""
audit_temporal_rope.py

Independent multi-cue replication and review of Finding #2622 (Task 101, poornima-1):
Temporal RoPE fast05 multi-seed evaluation (s4-7 vs s1-3, settle rate, energy dissipation,
and tracker survivorship).
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def load_data():
    base_dir = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task116_temporal_rope_review/data"
    with open(os.path.join(base_dir, "summary.json")) as f:
        summary = json.load(f)
    with open(os.path.join(base_dir, "metrics.json")) as f:
        metrics = json.load(f)
    with open(os.path.join(base_dir, "tracks101.json")) as f:
        tracks101 = json.load(f)
    with open(os.path.join(base_dir, "tracks92.json")) as f:
        tracks92 = json.load(f)
    with open(os.path.join(base_dir, "ct_metrics.json")) as f:
        ct_metrics = json.load(f)
    with open(os.path.join(base_dir, "ct_pooled_s1-7.json")) as f:
        pooled = json.load(f)
        
    return {
        "summary": summary,
        "metrics": metrics,
        "tracks101": tracks101,
        "tracks92": tracks92,
        "ct_metrics": ct_metrics,
        "pooled": pooled
    }

def analyze_survivorship(tracks101, tracks92, ct_metrics):
    """
    Examines tracker survivorship across arms and seeds.
    In rog2's review #2628:
    'base is trackable in 9/14 and the j0x05 and j0x025 arms in 2/8 and 0/8.
     Any arm comparison on the identity track therefore rests on a survivor subset.'
    """
    results = {}
    for clip_id, m in ct_metrics.items():
        # parse clip_id: e.g. b1dd33_fast05_s4
        parts = clip_id.split("_")
        inp = parts[0]
        arm = parts[1]
        seed = int(parts[2].replace("s", ""))
        
        vis = m.get("vis", 0.0)
        vis_late = m.get("vis_late", 0.0)
        is_trackable = (vis >= 0.50)  # standard threshold
        is_high_conf = (vis >= 0.85)  # poornima-1 threshold
        
        if arm not in results:
            results[arm] = {
                "n_total": 0,
                "n_trackable_50": 0,
                "n_trackable_85": 0,
                "vis_scores": [],
                "by_seed": {},
                "states": []
            }
        results[arm]["n_total"] += 1
        if is_trackable:
            results[arm]["n_trackable_50"] += 1
        if is_high_conf:
            results[arm]["n_trackable_85"] += 1
        results[arm]["vis_scores"].append(vis)
        results[arm]["states"].append(m.get("late_state", "unknown"))
        
        if seed not in results[arm]["by_seed"]:
            results[arm]["by_seed"][seed] = []
        results[arm]["by_seed"][seed].append({
            "clip_id": clip_id,
            "vis": vis,
            "vis_late": vis_late,
            "state": m.get("late_state", "unknown"),
            "apex_after40": m.get("apex_after40", None),
            "over_release": m.get("over_release", False),
            "above_real_e": m.get("above_real_e", False),
            "settled_end": m.get("settled_end", False)
        })
        
    return results

def main():
    data = load_data()
    print("Loaded all data.")
    surv = analyze_survivorship(data["tracks101"], data["tracks92"], data["ct_metrics"])
    
    print("\n=== TRACKER SURVIVORSHIP AUDIT (Task 101, n=32 clips) ===")
    for arm, stats in sorted(surv.items()):
        mean_vis = np.mean(stats["vis_scores"])
        print(f"Arm {arm:8s}: total={stats['n_total']}, vis>=0.85: {stats['n_trackable_85']}/{stats['n_total']} ({stats['n_trackable_85']/stats['n_total']*100:.1f}%), vis>=0.50: {stats['n_trackable_50']}/{stats['n_total']} ({stats['n_trackable_50']/stats['n_total']*100:.1f}%), mean_vis={mean_vis:.3f}")
        for seed, items in sorted(stats["by_seed"].items()):
            vis_list = [f"{it['vis']:.2f}" for it in items]
            states = [it['state'] for it in items]
            print(f"  Seed {seed}: vis={vis_list}, states={states}")

if __name__ == "__main__":
    main()
