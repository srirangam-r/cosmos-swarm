#!/usr/bin/env python3
"""
Independent Statistical Audit and Replication of Finding #2562
(Task 24 LoRA Scoreboard on 16 HUE T2V Dev Prompts across 5 Arms).

Author: agy-2
Task: 117
Target: Finding #2562 by rog-cc (commit 30163c9, work/rog-cc/hue_t24/)
"""

import os
import re
import json
import argparse
import numpy as np
from scipy import stats

CATS = ["overall", "Physical Laws", "Visual Integrity", "Geometric Reasoning", "Semantic Alignment"]
NV_METRICS = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_norm", "dd_binary"]
ARMS = ["base", "baseL", "loraA", "loraB", "loraC"]

# Predeclared / Proposed Margins
MARGINS = {
    "overall": 0.03,         # Human-approved (#1306)
    "Physical Laws": 0.04,   # Human-approved (#1306)
    "dover_fused": 0.02,     # Proposed
    "dd_norm": 1.1835,       # 15% of base mean (7.89 * 0.15 = 1.1835)
    "dd_binary": 0.10        # Proposed
}

pat = re.compile(r"((?:physics|robot)_\d+)_s(\d+)\.mp4$")

def extract_prompt_seed(name):
    m = pat.search(name)
    if m:
        return m.group(1), int(m.group(2))
    return name, 0

def load_hue(res_dir):
    """Loads HUE judge data for each arm, aggregating over offsets {0.0, 0.5} per clip."""
    hue_clips = {a: {} for a in ARMS}
    for a in ARMS:
        p_path = os.path.join(res_dir, f"{a}.json")
        if not os.path.exists(p_path):
            raise FileNotFoundError(f"Missing HUE file: {p_path}")
        with open(p_path) as f:
            data = json.load(f)
        for r in data["results"]:
            p, s = extract_prompt_seed(os.path.basename(r["clip"]))
            hue_clips[a].setdefault((p, s), []).append(r["summary"])
    
    # Compute per-prompt score (averaged over seeds 1 and 2)
    hue_prompts = {a: {} for a in ARMS}
    all_prompts = sorted(list(set(p for (p, s) in hue_clips["base"].keys())))
    for a in ARMS:
        for p in all_prompts:
            hue_prompts[a][p] = {}
            for c in CATS:
                vals = []
                for s in (1, 2):
                    sums = hue_clips[a].get((p, s), [])
                    matching = [x[c] for x in sums if c in x]
                    if matching:
                        vals.append(np.mean(matching))
                if len(vals) == 2:
                    hue_prompts[a][p][c] = float(np.mean(vals))
    return hue_clips, hue_prompts

def load_nv(res_nv_dir):
    """Loads NV scoreboard data (DOVER & Dynamic Degree) for each arm."""
    nv_clips = {a: {} for a in ARMS}
    for a in ARMS:
        p_path = os.path.join(res_nv_dir, f"{a}.json")
        if not os.path.exists(p_path):
            raise FileNotFoundError(f"Missing NV file: {p_path}")
        with open(p_path) as f:
            data = json.load(f)
        for k, v in data.items():
            p, s = extract_prompt_seed(k)
            nv_clips[a][(p, s)] = v

    # Compute per-prompt score (averaged over seeds 1 and 2)
    nv_prompts = {a: {} for a in ARMS}
    all_prompts = sorted(list(set(p for (p, s) in nv_clips["base"].keys())))
    for a in ARMS:
        for p in all_prompts:
            nv_prompts[a][p] = {}
            for m in NV_METRICS:
                v1 = nv_clips[a].get((p, 1), {}).get(m)
                v2 = nv_clips[a].get((p, 2), {}).get(m)
                if v1 is not None and v2 is not None:
                    nv_prompts[a][p][m] = float((v1 + v2) / 2.0)
    return nv_clips, nv_prompts

def compute_contrast(data_dict, a1, a2, p_list, metric, n_boot=100000, seed=42):
    """Computes exact Student-t and bootstrap statistics for paired differences a1 - a2."""
    diffs = []
    p_valid = []
    for p in p_list:
        if metric in data_dict[a1].get(p, {}) and metric in data_dict[a2].get(p, {}):
            diffs.append(data_dict[a1][p][metric] - data_dict[a2][p][metric])
            p_valid.append(p)
    diffs = np.array(diffs, dtype=np.float64)
    n = len(diffs)
    if n < 3:
        return None

    mean = float(np.mean(diffs))
    sd = float(np.std(diffs, ddof=1))
    se = float(sd / np.sqrt(n))
    
    t_stat = float(mean / se) if se > 0 else 0.0
    p_two_sided = float(2.0 * (1.0 - stats.t.cdf(abs(t_stat), df=n - 1)))
    p_one_sided_lower = float(stats.t.cdf(t_stat, df=n - 1)) # H0: mean >= 0 vs H1: mean < 0
    
    tcrit_90 = float(stats.t.ppf(0.95, df=n - 1))
    ci90 = [float(mean - tcrit_90 * se), float(mean + tcrit_90 * se)]
    
    tcrit_95 = float(stats.t.ppf(0.975, df=n - 1))
    ci95 = [float(mean - tcrit_95 * se), float(mean + tcrit_95 * se)]
    
    # Bootstrap CI (vectorized numpy for instant speed)
    rng = np.random.default_rng(seed)
    boot_matrix = rng.choice(diffs, size=(n_boot, n), replace=True)
    boot_means = np.mean(boot_matrix, axis=1)
    boot_ci90 = [float(np.percentile(boot_means, 5.0)), float(np.percentile(boot_means, 95.0))]
    boot_ci95 = [float(np.percentile(boot_means, 2.5)), float(np.percentile(boot_means, 97.5))]

    margin = MARGINS.get(metric)
    verdict = "unspecified"
    if margin is not None:
        lb90, ub90 = ci90
        if lb90 > -margin:
            verdict = "non-inferior"
        elif ub90 < -margin:
            verdict = "REGRESSION"
        elif ub90 < 0:
            verdict = "significant drop"
        else:
            verdict = "inconclusive"

    return {
        "contrast": f"{a1} - {a2}",
        "metric": metric,
        "n_prompts": n,
        "mean": mean,
        "sd": sd,
        "se": se,
        "t": t_stat,
        "p_value": p_two_sided,
        "p_one_sided": p_one_sided_lower,
        "ci90": ci90,
        "ci95": ci95,
        "boot_ci90": boot_ci90,
        "boot_ci95": boot_ci95,
        "n_pos": int(np.sum(diffs > 0)),
        "n_neg": int(np.sum(diffs < 0)),
        "margin": margin,
        "verdict": verdict,
        "per_prompt_diff": {p: float(d) for p, d in zip(p_valid, diffs)}
    }

def main():
    parser = argparse.ArgumentParser(description="Audit and replicate Finding #2562")
    parser.add_argument("--hue_dir", default="/home/nail/swarm-work/agy-2/cosmos-swarm/work/rog-cc/hue_t24/res")
    parser.add_argument("--nv_dir", default="/home/nail/swarm-work/agy-2/cosmos-swarm/work/rog-cc/hue_t24/res_nv")
    parser.add_argument("--out", default="task117_replication_results.json")
    args = parser.parse_args()

    hue_clips, hue_prompts = load_hue(args.hue_dir)
    nv_clips, nv_prompts = load_nv(args.nv_dir)

    all_prompts = sorted(list(hue_prompts["base"].keys()))
    physics_prompts = [p for p in all_prompts if p.startswith("physics")]
    robot_prompts = [p for p in all_prompts if p.startswith("robot")]

    print(f"Loaded {len(all_prompts)} prompts total ({len(physics_prompts)} physics, {len(robot_prompts)} robot)")

    # 1. Arm grand means
    arm_stats = {}
    for a in ARMS:
        arm_stats[a] = {"overall": {}, "physics": {}, "robot": {}}
        for domain, p_set in [("overall", all_prompts), ("physics", physics_prompts), ("robot", robot_prompts)]:
            for c in CATS:
                vals = [hue_prompts[a][p][c] for p in p_set if c in hue_prompts[a][p]]
                if vals:
                    arm_stats[a][domain][c] = {
                        "mean": float(np.mean(vals)),
                        "sd": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                        "se": float(stats.sem(vals)) if len(vals) > 1 else 0.0,
                        "n": len(vals)
                    }
            for m in NV_METRICS:
                vals = [nv_prompts[a][p][m] for p in p_set if m in nv_prompts[a][p]]
                if vals:
                    arm_stats[a][domain][m] = {
                        "mean": float(np.mean(vals)),
                        "sd": float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0,
                        "se": float(stats.sem(vals)) if len(vals) > 1 else 0.0,
                        "n": len(vals)
                    }

    # 2. Pairwise contrasts (overall, n=16)
    CONTRASTS_TO_RUN = [
        ("baseL", "base", "baseL - base (A/A box null)"),
        ("loraC", "base", "loraC - base (no-decay vs base)"),
        ("loraA", "base", "loraA - base (real-g candidate vs base)"),
        ("loraB", "base", "loraB - base (wrong-g control vs base)"),
        ("loraA", "loraB", "loraA - loraB (g difference on same box)"),
        ("loraA", "loraC", "loraA - loraC (decay difference)"),
        ("loraB", "loraC", "loraB - loraC"),
        ("loraA", "baseL", "loraA - baseL (real-g vs same-box base)"),
        ("loraB", "baseL", "loraB - baseL (wrong-g vs same-box base)"),
        ("loraC", "baseL", "loraC - baseL")
    ]

    contrast_results = {}
    for a1, a2, label in CONTRASTS_TO_RUN:
        contrast_results[label] = {}
        # HUE metrics
        for c in CATS:
            res = compute_contrast(hue_prompts, a1, a2, all_prompts, c)
            if res:
                contrast_results[label][c] = res
        # NV metrics
        for m in NV_METRICS:
            res = compute_contrast(nv_prompts, a1, a2, all_prompts, m)
            if res:
                contrast_results[label][m] = res

    # 3. Subgroup contrasts (Physics vs Robot)
    domain_contrasts = {"physics": {}, "robot": {}}
    for domain_key, p_set in [("physics", physics_prompts), ("robot", robot_prompts)]:
        for a1, a2, label in CONTRASTS_TO_RUN:
            domain_contrasts[domain_key][label] = {}
            for c in ["overall", "Physical Laws"]:
                res = compute_contrast(hue_prompts, a1, a2, p_set, c)
                if res:
                    domain_contrasts[domain_key][label][c] = res
            for m in ["dover_fused", "dover_technical", "dover_aesthetic", "dd_norm", "dd_binary"]:
                res = compute_contrast(nv_prompts, a1, a2, p_set, m)
                if res:
                    domain_contrasts[domain_key][label][m] = res

    full_output = {
        "metadata": {
            "title": "Independent Replication and Audit of Finding #2562 (Task 117)",
            "author": "agy-2",
            "date": "2026-11-01",
            "n_prompts_total": len(all_prompts),
            "n_prompts_physics": len(physics_prompts),
            "n_prompts_robot": len(robot_prompts),
            "n_seeds_per_prompt": 2,
            "n_clips_per_arm": 32,
            "arms": ARMS,
            "margins": MARGINS
        },
        "arm_grand_means": arm_stats,
        "pairwise_contrasts_overall": contrast_results,
        "domain_contrasts": domain_contrasts
    }

    with open(args.out, "w") as f:
        json.dump(full_output, f, indent=2)
    print(f"Replication analysis successfully written to {args.out}")

if __name__ == "__main__":
    main()
