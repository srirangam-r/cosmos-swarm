"""Task 319 (dk2): NVIDIA-scoreboard paired analysis of the 42 task-276 clips.

Inputs: scores_gen.json, scores_real.json (tools/nv_scoreboard/score.py output).
Design: 6 held-out GAUGE pendulum scenes x seeds 1-3, arms plain / nphys (+ nphys_x17 seed 1).
Per scene, average the 3 seeds per arm, then take the delta nphys - plain. Scenes weigh equally.
Uncertainty: exact enumeration of all 6^6 scene-bootstrap resamples (percentile 95%), plus a t-interval.
Seed-noise baseline: pooled within-scene SD over seeds (plain), and the SD of the seed-mean (SD/sqrt3).
Same-seed paired deltas (scene, seed) are also given.
MF: written as a manifest for tools/nv_scoreboard/motion_fidelity.py (dd_binary only, official form).
dd_norm is a continuous optical-flow PROXY, not NVIDIA's dynamic degree.
"""
import json, sys, itertools, re, math
from pathlib import Path
import numpy as np

here = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
gen = json.load(open(here / "scores_gen.json"))
real = json.load(open(here / "scores_real.json"))
METRICS = ["dover_fused", "dover_technical", "dover_aesthetic", "dd_binary", "dd_norm", "dd_frac"]

rows = {}
for k, v in gen.items():
    m = re.match(r"t276_(real_\d+)_(plain|nphys|nphys_x17)_s(\d)\.mp4$", Path(k).name)
    if not m:
        continue
    rows[(m.group(1), m.group(2), int(m.group(3)))] = v
scenes = sorted({s for s, _, _ in rows})
assert len(scenes) == 6, scenes
assert len(rows) == 42, len(rows)
realrow = {re.search(r"real_\d+", Path(k).name).group(0): v for k, v in real.items()}

T = 2.570581835636  # t_{0.975, df=5}


def boot_exact(d):
    d = np.asarray(d, float)
    n = len(d)
    idx = np.array(list(itertools.product(range(n), repeat=n)))
    means = d[idx].mean(1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


out = {"scenes": scenes, "per_clip": {}, "metrics": {}}
for (s, a, sd), v in sorted(rows.items()):
    out["per_clip"][f"{s}_{a}_s{sd}"] = {m: v[m] for m in METRICS} | {"dover_fused_sd": v["dover_fused_sd"]}
for s in scenes:
    out["per_clip"][f"{s}_REAL"] = {m: realrow[s][m] for m in METRICS}

for m in METRICS:
    arm = {a: np.array([[rows[(s, a, sd)][m] for sd in (1, 2, 3)] for s in scenes]) for a in ("plain", "nphys")}
    x17 = np.array([rows[(s, "nphys_x17", 1)][m] for s in scenes])
    rl = np.array([realrow[s][m] for s in scenes])
    dscene = arm["nphys"].mean(1) - arm["plain"].mean(1)
    dpair = (arm["nphys"] - arm["plain"]).ravel()
    seed_sd = float(np.sqrt(np.mean(arm["plain"].var(1, ddof=1))))
    seed_sd_n = float(np.sqrt(np.mean(arm["nphys"].var(1, ddof=1))))
    se = dscene.std(ddof=1) / math.sqrt(6)
    res = {
        "plain_mean": float(arm["plain"].mean()), "nphys_mean": float(arm["nphys"].mean()),
        "x17_seed1_mean": float(x17.mean()), "real_mean": float(rl.mean()),
        "plain_seed1_mean": float(arm["plain"][:, 0].mean()), "nphys_seed1_mean": float(arm["nphys"][:, 0].mean()),
        "delta_scene_mean": float(dscene.mean()), "delta_per_scene": dscene.round(5).tolist(),
        "delta_boot95_exact": boot_exact(dscene),
        "delta_t95": [float(dscene.mean() - T * se), float(dscene.mean() + T * se)],
        "delta_scenes_negative": int((dscene < 0).sum()),
        "delta_pairs_negative": int((dpair < 0).sum()), "n_pairs": int(dpair.size),
        "seed_sd_plain_pooled": seed_sd, "seed_sd_nphys_pooled": seed_sd_n,
        "seed_noise_sd_of_3seed_mean": seed_sd / math.sqrt(3),
        "x17_minus_nphys_seed1": float((x17 - arm["nphys"][:, 0]).mean()),
    }
    if m.startswith("dd"):
        res["gap_to_real_plain"] = float(np.abs(arm["plain"] - rl[:, None]).mean())
        res["gap_to_real_nphys"] = float(np.abs(arm["nphys"] - rl[:, None]).mean())
    out["metrics"][m] = res

# Official-form MF manifest (dd_binary). Reference = the 6 matched real scene clips (25 fps container, see caveat).
gen_rel = "scores_gen.json"
name2key = {Path(k).name: k for k in gen}
for arm in ("plain", "nphys"):
    man = {"bands": [{"id": "24fps_pend_heldout", "reference": [
        {"file": "scores_real.json", "key": k} for k in sorted(real)],
        "prompts": [{"id": f"{s}_{arm}", "clips": [
            {"file": gen_rel, "key": name2key[f"t276_{s}_{arm}_s{sd}.mp4"], "seed": sd} for sd in (1, 2, 3)]}
            for s in scenes]}]}
    json.dump(man, open(here / f"mf_manifest_{arm}.json", "w"), indent=1)

json.dump(out, open(here / "t319_results.json", "w"), indent=1)

lines = ["| metric | real | plain | nphys | x17 (s1) | nphys-plain (scene mean) | exact boot 95% | t 95% | scenes<0 | pairs<0 | seed SD (plain) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
for m in METRICS:
    r = out["metrics"][m]
    lines.append(f"| {m} | {r['real_mean']:.4f} | {r['plain_mean']:.4f} | {r['nphys_mean']:.4f} | {r['x17_seed1_mean']:.4f} | "
                 f"{r['delta_scene_mean']:+.4f} | [{r['delta_boot95_exact'][0]:+.4f}, {r['delta_boot95_exact'][1]:+.4f}] | "
                 f"[{r['delta_t95'][0]:+.4f}, {r['delta_t95'][1]:+.4f}] | {r['delta_scenes_negative']}/6 | "
                 f"{r['delta_pairs_negative']}/18 | {r['seed_sd_plain_pooled']:.4f} |")
open(here / "t319_table.md", "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
for m in ("dd_binary", "dd_norm"):
    r = out["metrics"][m]
    print(m, "mean |gen-real| plain", round(r["gap_to_real_plain"], 4), "nphys", round(r["gap_to_real_nphys"], 4))
