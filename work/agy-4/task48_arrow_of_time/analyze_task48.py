#!/usr/bin/env python3
"""
Statistical and kinematic analysis of Task 48:
Does Nano's rectified-flow denoising loss prefer forward over time-reversed real decaying-bounce clips (arrow-of-time probe)?

Compares:
1. Arm A: Real GAUGE decaying drops (damped, e ≈ 0.69)
2. Arm B: Cosmos Base F undamped drops (perpetual oscillation, e ≈ 1.00)
3. Arm C: Cosmos Prompt-Timed Settling drops (QT / RECT)
"""
import glob
import json
import os
from pathlib import Path
import numpy as np
from scipy import stats

def load_probe_results(out_dir):
    files = glob.glob(os.path.join(out_dir, "probe_*.json"))
    results = {}
    for f in sorted(files):
        stem = Path(f).stem
        with open(f) as fp:
            results[stem] = json.load(fp)
    return results

def analyze_probes(results):
    categories = {
        "real_damped": [
            "probe_real_ball1", "probe_real_ball2", "probe_real_ball3", "probe_real_ball4",
            "probe_real_midfall_ball1", "probe_real_midfall_ball2"
        ],
        "cosmos_undamped": [
            "probe_cosmos_baseF_b1_s1", "probe_cosmos_baseF_b1_s2", "probe_cosmos_baseF_b1_s3",
            "probe_cosmos_rec_b1_s3"
        ],
        "cosmos_settling": [
            "probe_cosmos_timedQT_b1_s3", "probe_cosmos_rect_b1_s3"
        ]
    }

    sigmas = ["0.1", "0.3", "0.5", "0.7", "0.9"]
    summary_data = {}

    for cat, keys in categories.items():
        cat_deltas = []
        cat_freeze_deltas = []
        fwd_losses = []
        rev_losses = []
        freeze_losses = []
        by_sigma_delta = {s: [] for s in sigmas}
        per_frame_deltas = []

        for k in keys:
            if k not in results:
                continue
            res = results[k]
            paired = res.get("paired", {})
            summ = res.get("summary", {})

            # Mean paired delta: reverse minus forward
            rev_fwd = paired.get("reverse_minus_forward", {})
            d = rev_fwd.get("mean_delta")
            if d is not None:
                cat_deltas.append(d)

            # Freeze minus forward
            frz_fwd = paired.get("freeze_first_minus_forward", {})
            df = frz_fwd.get("mean_delta")
            if df is not None:
                cat_freeze_deltas.append(df)

            # Raw losses
            fwd = summ.get("forward", {}).get("by_sigma", {})
            rev = summ.get("reverse", {}).get("by_sigma", {})
            frz = summ.get("freeze_first", {}).get("by_sigma", {})

            fwd_losses.append(np.mean([fwd[s] for s in sigmas if s in fwd]))
            rev_losses.append(np.mean([rev[s] for s in sigmas if s in rev]))
            freeze_losses.append(np.mean([frz[s] for s in sigmas if s in frz]))

            for s in sigmas:
                if s in fwd and s in rev:
                    by_sigma_delta[s].append(rev[s] - fwd[s])

            # Per frame
            pfd = rev_fwd.get("mean_delta_per_frame")
            if pfd is not None:
                per_frame_deltas.append([x for x in pfd if x is not None])

        n = len(cat_deltas)
        if n > 0:
            mean_d = float(np.mean(cat_deltas))
            se_d = float(stats.sem(cat_deltas)) if n > 1 else 0.0
            t_val, p_val = (stats.ttest_1samp(cat_deltas, 0.0)) if n > 1 else (0.0, 1.0)
            ci90 = [mean_d - stats.t.ppf(0.95, df=n-1)*se_d, mean_d + stats.t.ppf(0.95, df=n-1)*se_d] if n > 1 else [mean_d, mean_d]
            ci95 = [mean_d - stats.t.ppf(0.975, df=n-1)*se_d, mean_d + stats.t.ppf(0.975, df=n-1)*se_d] if n > 1 else [mean_d, mean_d]

            summary_data[cat] = {
                "n": n,
                "mean_delta_rev_minus_fwd": mean_d,
                "se_delta": se_d,
                "t_stat": float(t_val),
                "p_value": float(p_val),
                "ci90": [float(x) for x in ci90],
                "ci95": [float(x) for x in ci95],
                "fwd_mean_loss": float(np.mean(fwd_losses)),
                "rev_mean_loss": float(np.mean(rev_losses)),
                "freeze_mean_loss": float(np.mean(freeze_losses)),
                "freeze_minus_fwd_delta": float(np.mean(cat_freeze_deltas)),
                "by_sigma_delta": {s: float(np.mean(v)) for s, v in by_sigma_delta.items() if v},
                "per_clip_deltas": {k: results[k].get("paired", {}).get("reverse_minus_forward", {}).get("mean_delta")
                                    for k in keys if k in results}
            }

    # Arm contrast: Real vs Cosmos Base
    if "real_damped" in summary_data and "cosmos_undamped" in summary_data:
        r_d = [summary_data["real_damped"]["per_clip_deltas"][k] for k in categories["real_damped"] if k in summary_data["real_damped"]["per_clip_deltas"]]
        c_d = [summary_data["cosmos_undamped"]["per_clip_deltas"][k] for k in categories["cosmos_undamped"] if k in summary_data["cosmos_undamped"]["per_clip_deltas"]]
        t_twosamp, p_twosamp = stats.ttest_ind(r_d, c_d, equal_var=False)
        summary_data["contrast_real_vs_cosmos_undamped"] = {
            "diff_mean_delta": float(np.mean(r_d) - np.mean(c_d)),
            "t_stat": float(t_twosamp),
            "p_value": float(p_twosamp)
        }

    return summary_data

if __name__ == "__main__":
    out_dir = "/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task48_arrow_of_time/out"
    res = load_probe_results(out_dir)
    print(f"Loaded {len(res)} probe results from {out_dir}")
    analysis = analyze_probes(res)
    print(json.dumps(analysis, indent=2))
    with open("/home/nail/swarm-work/agy-4/cosmos-swarm/work/agy-4/task48_arrow_of_time/task48_analysis_results.json", "w") as fp:
        json.dump(analysis, fp, indent=2)
    print("Saved task48_analysis_results.json")
