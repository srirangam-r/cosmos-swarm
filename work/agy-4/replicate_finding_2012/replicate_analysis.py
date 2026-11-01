import json
import math
import numpy as np
import scipy.stats as stats
import os

def load_json(path):
    with open(path) as f:
        return json.load(f)

def get_clip_basename(path):
    return os.path.basename(path)

def paired_stats(deltas, conf=0.95):
    n = len(deltas)
    mean = np.mean(deltas)
    sd = np.std(deltas, ddof=1)
    se = sd / math.sqrt(n)
    df = n - 1
    t_crit_2sided = stats.t.ppf((1 + conf) / 2, df)
    t_crit_1sided = stats.t.ppf(conf, df)
    ci_2sided = (mean - t_crit_2sided * se, mean + t_crit_2sided * se)
    lb_1sided = mean - t_crit_1sided * se
    ub_1sided = mean + t_crit_1sided * se
    return {
        "n": n,
        "df": df,
        "mean": float(mean),
        "sd": float(sd),
        "se": float(se),
        "ci_95": [float(ci_2sided[0]), float(ci_2sided[1])],
        "lb_95_1sided": float(lb_1sided),
        "ub_95_1sided": float(ub_1sided),
        "values": [float(x) for x in deltas]
    }

def run_replication_audit(agy4_scores_path, rog_scores_path, agy3_base_path, agy3_recipe_path, out_json_path):
    agy4 = load_json(agy4_scores_path)
    rog = load_json(rog_scores_path)
    agy3_base = load_json(agy3_base_path)
    agy3_recipe = load_json(agy3_recipe_path)

    # Normalize keys by basename
    agy4_by_bn = {get_clip_basename(k): v for k, v in agy4.items()}
    rog_by_bn = {get_clip_basename(k): v for k, v in rog.items()}
    agy3_base_by_bn = {get_clip_basename(k): v for k, v in agy3_base.items()}
    agy3_recipe_by_bn = {get_clip_basename(k): v for k, v in agy3_recipe.items()}

    pairs = []
    for b in [1, 2]:
        for s in [1, 2, 3, 4]:
            ctrl_name = f"box_ctrl_b{b}_noneg_s{s}.mp4"
            mid_name = f"box_mid_b{b}_noneg_s{s}.mp4"
            pairs.append({
                "ball": b,
                "seed": s,
                "ctrl": ctrl_name,
                "mid": mid_name
            })

    results = {
        "pairs_analysis": {},
        "seed_clusters_analysis": {},
        "replicate_noise": {},
        "comparison_with_rog": {},
        "comparison_with_agy3": {},
        "dynamic_degree": {}
    }

    # 1. Independent Agy-4 3-rep Analysis
    metrics = ["dover_fused", "dover_technical", "dover_aesthetic"]
    for m in metrics:
        deltas = []
        cluster_deltas = {s: [] for s in [1, 2, 3, 4]}
        for p in pairs:
            c_val = agy4_by_bn[p["ctrl"]][m]
            m_val = agy4_by_bn[p["mid"]][m]
            delta = m_val - c_val
            deltas.append(delta)
            cluster_deltas[p["seed"]].append(delta)

        # 8-pair paired t
        results["pairs_analysis"][m] = paired_stats(deltas)

        # 4-seed cluster paired t (average over balls for each seed)
        cluster_means = [np.mean(cluster_deltas[s]) for s in [1, 2, 3, 4]]
        results["seed_clusters_analysis"][m] = paired_stats(cluster_means)

    # 2. Within-clip replicate noise in Agy-4 run
    for m in metrics:
        sd_key = f"{m}_sd"
        sds = [v[sd_key] for v in agy4_by_bn.values() if sd_key in v]
        results["replicate_noise"][m] = {
            "mean_sd": float(np.mean(sds)),
            "max_sd": float(np.max(sds)),
            "min_sd": float(np.min(sds)),
            "values": [float(x) for x in sds]
        }

    # 3. Agreement between Agy-4 (3 reps) and Rog-cc (3 reps)
    for m in metrics:
        diffs = []
        agy4_vals = []
        rog_vals = []
        for bn in agy4_by_bn:
            if bn in rog_by_bn:
                v1 = agy4_by_bn[bn][m]
                v2 = rog_by_bn[bn][m]
                diffs.append(v1 - v2)
                agy4_vals.append(v1)
                rog_vals.append(v2)
        r = float(np.corrcoef(agy4_vals, rog_vals)[0, 1])
        results["comparison_with_rog"][m] = {
            "mean_diff": float(np.mean(diffs)),
            "sd_diff": float(np.std(diffs, ddof=1)),
            "corr_r": r,
            "max_abs_diff": float(np.max(np.abs(diffs)))
        }

    # 4. Agreement between Rog-cc (3 reps) and Agy-3 (1 rep)
    for m in metrics:
        diffs = []
        rog_vals = []
        agy3_vals = []
        for bn in rog_by_bn:
            v_rog = rog_by_bn[bn][m]
            v_agy3 = agy3_base_by_bn[bn][m] if bn in agy3_base_by_bn else agy3_recipe_by_bn[bn][m]
            diffs.append(v_rog - v_agy3)
            rog_vals.append(v_rog)
            agy3_vals.append(v_agy3)
        r = float(np.corrcoef(rog_vals, agy3_vals)[0, 1])
        results["comparison_with_agy3"][m] = {
            "mean_diff": float(np.mean(diffs)),
            "sd_diff": float(np.std(diffs, ddof=1)),
            "corr_r": r,
            "max_abs_diff": float(np.max(np.abs(diffs)))
        }

    # 5. Dynamic Degree replication (from rog_by_bn / agy3)
    ctrl_dd_bin = [rog_by_bn[p["ctrl"]]["dd_binary"] for p in pairs]
    mid_dd_bin = [rog_by_bn[p["mid"]]["dd_binary"] for p in pairs]
    delta_dd_bin = [m - c for m, c in zip(mid_dd_bin, ctrl_dd_bin)]

    ctrl_dd_norm = [rog_by_bn[p["ctrl"]]["dd_norm"] for p in pairs]
    mid_dd_norm = [rog_by_bn[p["mid"]]["dd_norm"] for p in pairs]
    delta_dd_norm = [m - c for m, c in zip(mid_dd_norm, ctrl_dd_norm)]

    # Real DD reference = 0.255, real binary = 0.0
    dist_ctrl_bin = [abs(c - 0.0) for c in ctrl_dd_bin]
    dist_mid_bin = [abs(m - 0.0) for m in mid_dd_bin]
    delta_dist_bin = [m - c for m, c in zip(dist_mid_bin, dist_ctrl_bin)]

    results["dynamic_degree"] = {
        "ctrl_binary_mean": float(np.mean(ctrl_dd_bin)),
        "mid_binary_mean": float(np.mean(mid_dd_bin)),
        "delta_binary": paired_stats(delta_dd_bin),
        "ctrl_norm_mean": float(np.mean(ctrl_dd_norm)),
        "mid_norm_mean": float(np.mean(mid_dd_norm)),
        "delta_norm": paired_stats(delta_dd_norm),
        "delta_distance_to_real_binary": paired_stats(delta_dist_bin)
    }

    with open(out_json_path, "w") as f:
        json.dump(results, f, indent=2)

    print("Replication analysis complete!")
    print("\n--- AGY-4 3-DRAW DOVER DELTAS (8 PAIRS) ---")
    for m in metrics:
        s = results["pairs_analysis"][m]
        print(f"{m}: mean={s['mean']:+.6f} +/- {s['se']:.6f}, 95% CI [{s['ci_95'][0]:+.6f}, {s['ci_95'][1]:+.6f}], 1-sided LB {s['lb_95_1sided']:+.6f}")

    print("\n--- AGY-4 4-SEED CLUSTERS (4 CLUSTERS, df=3) ---")
    for m in metrics:
        s = results["seed_clusters_analysis"][m]
        print(f"{m}: mean={s['mean']:+.6f} +/- {s['se']:.6f}, 1-sided LB {s['lb_95_1sided']:+.6f}")

    print("\n--- REPLICATE DRAW NOISE (WITHIN-CLIP SD) ---")
    for m in metrics:
        s = results["replicate_noise"][m]
        print(f"{m}: mean_sd={s['mean_sd']:.6f}, max_sd={s['max_sd']:.6f}")

    print("\n--- COMPARISON AGY-4 (3 draws) vs ROG-CC (3 draws) ---")
    for m in metrics:
        s = results["comparison_with_rog"][m]
        print(f"{m}: mean_diff={s['mean_diff']:+.6f}, SD={s['sd_diff']:.6f}, corr_r={s['corr_r']:.4f}")

    print("\n--- DYNAMIC DEGREE RESULTS ---")
    t_stat = abs(results['dynamic_degree']['delta_binary']['mean'] / results['dynamic_degree']['delta_binary']['se'])
    p_val = 2 * float(stats.t.sf(t_stat, 7))
    results["dynamic_degree"]["delta_binary_pval"] = p_val
    print(f"Binary DD: Base={results['dynamic_degree']['ctrl_binary_mean']:.3f} -> Recipe={results['dynamic_degree']['mid_binary_mean']:.3f}, Delta={results['dynamic_degree']['delta_binary']['mean']:+.3f} +/- {results['dynamic_degree']['delta_binary']['se']:.3f} (p={p_val:.4f})")
    print(f"DD Norm: Base={results['dynamic_degree']['ctrl_norm_mean']:.3f} -> Recipe={results['dynamic_degree']['mid_norm_mean']:.3f}, Delta={results['dynamic_degree']['delta_norm']['mean']:+.3f} +/- {results['dynamic_degree']['delta_norm']['se']:.3f}")
    print(f"|DD - real|: Delta={results['dynamic_degree']['delta_distance_to_real_binary']['mean']:+.3f} +/- {results['dynamic_degree']['delta_distance_to_real_binary']['se']:.3f}, 1-sided UB={results['dynamic_degree']['delta_distance_to_real_binary']['ub_95_1sided']:+.3f}")

if __name__ == "__main__":
    import sys
    agy4_path = sys.argv[1] if len(sys.argv) > 1 else "/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/replicate_finding_2012/nv16_dover3_agy4.json"
    rog_path = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/rog-cc/d1_judge/nv16.json"
    agy3_base = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/rog-cc/d1_judge/nv16cmp/scores_baseline_held.json"
    agy3_recipe = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/rog-cc/d1_judge/nv16cmp/scores_recipe_midfall.json"
    out_path = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/replicate_finding_2012/replication_2012_results.json"
    run_replication_audit(agy4_path, rog_path, agy3_base, agy3_recipe, out_path)
