#!/usr/bin/env python3
"""
Independent statistical and kinematic replication of Finding #2720 (Task 22, ro-1):
Recipe prompt timed-settle clause evaluation (RECT vs REC).
"""

import json
import os
import glob
import csv
import numpy as np
import scipy.stats as stats

REPO_ROOT = "/home/nail/swarm-work/agy-3/cosmos-swarm"
V7_DIR = os.path.join(REPO_ROOT, "work/ro-1/cause_v7")
OUT_DIR = os.path.join(REPO_ROOT, "work/agy-3/task120_recipe_settle_review")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "plots"), exist_ok=True)
os.makedirs(os.path.join(OUT_DIR, "sheets"), exist_ok=True)

# 1. Load late_nv_v78.json
with open(os.path.join(V7_DIR, "late_nv_v78.json")) as f:
    late_nv = json.load(f)

# 2. Load eye_codes.csv
eye_codes = []
with open(os.path.join(V7_DIR, "eye_codes.csv")) as f:
    r = csv.DictReader(f)
    for row in r:
        eye_codes.append(row)

# 3. Load all score.json files
scores = {}
for sf in glob.glob(os.path.join(V7_DIR, "scores/*.score.json")):
    with open(sf) as f:
        d = json.load(f)
        k = next(iter(d.keys()))
        b = k.replace(".mp4", "")
        scores[b] = d[k]

print(f"Loaded {len(late_nv)} entries from late_nv_v78.json")
print(f"Loaded {len(eye_codes)} rows from eye_codes.csv")
print(f"Loaded {len(scores)} score files")

# Pairs: 2 balls x 3 seeds = 6 pairs
pairs = []
for b in ("ball1", "ball2"):
    for s in (1, 2, 3):
        rec_name = f"v7_REC_{b}_fps24_93f_s{s}"
        rect_name = f"v7_RECT_{b}_fps24_93f_s{s}"
        pairs.append({
            "ball": b,
            "seed": s,
            "rec_name": rec_name,
            "rect_name": rect_name,
            "rec_late": late_nv[rec_name],
            "rect_late": late_nv[rect_name],
            "rec_score": scores[rec_name],
            "rect_score": scores[rect_name]
        })

print(f"Assembled {len(pairs)} matched pairs")

# Analysis metrics
keys_to_analyze = [
    ("last20", lambda x: x["rec_late"]["last20"], lambda x: x["rect_late"]["last20"]),
    ("late", lambda x: x["rec_late"]["late"], lambda x: x["rect_late"]["late"]),
    ("early", lambda x: x["rec_late"]["early"], lambda x: x["rect_late"]["early"]),
    ("dover_fused", lambda x: x["rec_score"]["dover_fused"], lambda x: x["rect_score"]["dover_fused"]),
    ("dover_technical", lambda x: x["rec_score"]["dover_technical"], lambda x: x["rect_score"]["dover_technical"]),
    ("dover_aesthetic", lambda x: x["rec_score"]["dover_aesthetic"], lambda x: x["rect_score"]["dover_aesthetic"]),
    ("dd_norm", lambda x: x["rec_score"]["dd_norm"], lambda x: x["rect_score"]["dd_norm"]),
    ("dd_binary", lambda x: x["rec_score"]["dd_binary"], lambda x: x["rect_score"]["dd_binary"]),
]

results = {}

print("\n" + "="*80)
print(f"{'Metric':<18} | {'REC Mean ± SE':<18} | {'RECT Mean ± SE':<18} | {'Paired Δ ± SE':<18} | {'p-value':<8} | {'90% CI':<16} | {'95% CI':<16}")
print("="*80)

for name, get_rec, get_rect in keys_to_analyze:
    rec_vals = np.array([get_rec(p) for p in pairs], dtype=float)
    rect_vals = np.array([get_rect(p) for p in pairs], dtype=float)
    deltas = rect_vals - rec_vals
    n = len(deltas)
    
    mean_rec = float(np.mean(rec_vals))
    se_rec = float(np.std(rec_vals, ddof=1) / np.sqrt(n))
    
    mean_rect = float(np.mean(rect_vals))
    se_rect = float(np.std(rect_vals, ddof=1) / np.sqrt(n))
    
    mean_delta = float(np.mean(deltas))
    se_delta = float(np.std(deltas, ddof=1) / np.sqrt(n))
    
    # Paired t-test
    if se_delta > 1e-9:
        t_stat, p_val = stats.ttest_rel(rect_vals, rec_vals)
        ci90 = stats.t.interval(0.90, df=n-1, loc=mean_delta, scale=se_delta)
        ci95 = stats.t.interval(0.95, df=n-1, loc=mean_delta, scale=se_delta)
    else:
        t_stat, p_val = 0.0, 1.0
        ci90 = (mean_delta, mean_delta)
        ci95 = (mean_delta, mean_delta)
        
    # Bootstrap CI
    rng = np.random.default_rng(42)
    boot_deltas = [np.mean(rng.choice(deltas, size=n, replace=True)) for _ in range(10000)]
    boot_ci90 = (float(np.percentile(boot_deltas, 5)), float(np.percentile(boot_deltas, 95)))
    boot_ci95 = (float(np.percentile(boot_deltas, 2.5)), float(np.percentile(boot_deltas, 97.5)))
    
    n_lower = int(np.sum(deltas < 0))
    n_higher = int(np.sum(deltas > 0))
    
    results[name] = {
        "rec_mean": mean_rec, "rec_se": se_rec, "rec_vals": rec_vals.tolist(),
        "rect_mean": mean_rect, "rect_se": se_rect, "rect_vals": rect_vals.tolist(),
        "delta_mean": mean_delta, "delta_se": se_delta, "deltas": deltas.tolist(),
        "t_stat": float(t_stat), "p_val": float(p_val),
        "ci90_t": [float(ci90[0]), float(ci90[1])],
        "ci95_t": [float(ci95[0]), float(ci95[1])],
        "ci90_boot": boot_ci90,
        "ci95_boot": boot_ci95,
        "n_lower": n_lower,
        "n_higher": n_higher,
        "n": n
    }
    
    ci90_str = f"[{ci90[0]:+.3f}, {ci90[1]:+.3f}]"
    ci95_str = f"[{ci95[0]:+.3f}, {ci95[1]:+.3f}]"
    print(f"{name:<18} | {mean_rec:.3f} ± {se_rec:.3f}      | {mean_rect:.3f} ± {se_rect:.3f}      | {mean_delta:+.3f} ± {se_delta:.3f} ({n_lower}/{n}) | {p_val:.4f}  | {ci90_str:<16} | {ci95_str:<16}")

print("="*80)

# Real video distance comparison for Dynamic Degree
# Real continuation DD for Ball 1 is 0.564 (established in Task 68 / Finding 1616 / Task 73)
real_dd_ball1 = 0.564
ball1_pairs = [p for p in pairs if p["ball"] == "ball1"]
rec_dd_b1 = np.array([p["rec_score"]["dd_norm"] for p in ball1_pairs])
rect_dd_b1 = np.array([p["rect_score"]["dd_norm"] for p in ball1_pairs])

dist_rec_b1 = np.abs(rec_dd_b1 - real_dd_ball1)
dist_rect_b1 = np.abs(rect_dd_b1 - real_dd_ball1)
print(f"\nBall 1 Dynamic Degree Distance to Real (|DD - {real_dd_ball1}|):")
for i, s in enumerate([1, 2, 3]):
    print(f"  Seed {s}: REC = {rec_dd_b1[i]:.3f} (dist {dist_rec_b1[i]:.3f}) -> RECT = {rect_dd_b1[i]:.3f} (dist {dist_rect_b1[i]:.3f}) [Δdist = {dist_rect_b1[i] - dist_rec_b1[i]:+.3f}]")
print(f"  Mean distance: REC = {np.mean(dist_rec_b1):.3f} -> RECT = {np.mean(dist_rect_b1):.3f} (reduction of {np.mean(dist_rec_b1) - np.mean(dist_rect_b1):+.3f})")

# Optical Flow Profiles from dd_maxrad across 30 pairs
rec_flow_profiles = np.stack([p["rec_score"]["dd_maxrad"] for p in pairs]) # (6, 30)
rect_flow_profiles = np.stack([p["rect_score"]["dd_maxrad"] for p in pairs]) # (6, 30)

mean_rec_flow = rec_flow_profiles.mean(axis=0)
mean_rect_flow = rect_flow_profiles.mean(axis=0)

# Early flow (pairs 0-14, ~frames 0-45) vs Late flow (pairs 15-29, ~frames 45-90)
early_rec_flow = rec_flow_profiles[:, :15].mean(axis=1)
late_rec_flow = rec_flow_profiles[:, 15:].mean(axis=1)

early_rect_flow = rect_flow_profiles[:, :15].mean(axis=1)
late_rect_flow = rect_flow_profiles[:, 15:].mean(axis=1)

print(f"\nOptical Flow Trajectory Analysis (RAFT displacement magnitude across 30 pairs):")
print(f"  REC Early Flow:  {early_rec_flow.mean():.3f} ± {early_rec_flow.std(ddof=1)/np.sqrt(6):.3f}")
print(f"  REC Late Flow:   {late_rec_flow.mean():.3f} ± {late_rec_flow.std(ddof=1)/np.sqrt(6):.3f}")
print(f"  REC Attenuation (Late / Early): {late_rec_flow.mean() / early_rec_flow.mean():.3f}")
print(f"  RECT Early Flow: {early_rect_flow.mean():.3f} ± {early_rect_flow.std(ddof=1)/np.sqrt(6):.3f}")
print(f"  RECT Late Flow:  {late_rect_flow.mean():.3f} ± {late_rect_flow.std(ddof=1)/np.sqrt(6):.3f}")
print(f"  RECT Attenuation (Late / Early): {late_rect_flow.mean() / early_rect_flow.mean():.3f}")

results["optical_flow"] = {
    "mean_rec_flow_profile": mean_rec_flow.tolist(),
    "mean_rect_flow_profile": mean_rect_flow.tolist(),
    "early_rec_flow": float(early_rec_flow.mean()),
    "late_rec_flow": float(late_rec_flow.mean()),
    "early_rect_flow": float(early_rect_flow.mean()),
    "late_rect_flow": float(late_rect_flow.mean()),
    "rec_attenuation": float(late_rec_flow.mean() / early_rec_flow.mean()),
    "rect_attenuation": float(late_rect_flow.mean() / early_rect_flow.mean())
}

# Eye code audit
rec_eye = [r for r in eye_codes if r["arm"] == "REC"]
rect_eye = [r for r in eye_codes if r["arm"] == "RECT"]

rec_settled = sum(1 for r in rec_eye if r["settles_by_f92"] == "Y")
rect_settled = sum(1 for r in rect_eye if r["settles_by_f92"] == "Y")

def is_artifact(note):
    n = note.lower()
    return "duplicate" in n or "artifact" in n or "debris" in n or "box" in n

rec_artifacts = sum(1 for r in rec_eye if is_artifact(r["notes"]))
rect_artifacts = sum(1 for r in rect_eye if is_artifact(r["notes"]))

print(f"\nVisual Eye Code Audit:")
print(f"  Settle Rate by f92: REC = {rec_settled}/{len(rec_eye)} ({rec_settled/len(rec_eye):.1%}) vs RECT = {rect_settled}/{len(rect_eye)} ({rect_settled/len(rect_eye):.1%})")
print(f"  Gross Artifacts:    REC = {rec_artifacts}/{len(rec_eye)} ({rec_artifacts/len(rec_eye):.1%}) vs RECT = {rect_artifacts}/{len(rect_eye)} ({rect_artifacts/len(rect_eye):.1%})")

results["eye_codes"] = {
    "rec_settled_rate": float(rec_settled / len(rec_eye)),
    "rect_settled_rate": float(rect_settled / len(rect_eye)),
    "rec_artifacts_count": int(rec_artifacts),
    "rect_artifacts_count": int(rect_artifacts),
    "details": eye_codes
}

# Save full results json
out_json_path = os.path.join(OUT_DIR, "task120_replication_results.json")
with open(out_json_path, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nSaved full results to {out_json_path}")
