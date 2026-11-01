#!/usr/bin/env python3
"""Replication of rog1 #5243 (task 255) on independent clips: my t210 Bridge FD chunk-1 grid
(24 devset_bridge clips x arms base/R/N x seeds 0-3, q8 only, default CUDA noise, 30 steps, CFG 1, 256^2, 17 f @ 5 fps).
No new generation. Independent analysis code (this file); LPIPS-alex from tools/robot_pred/score.py (shared metric).

Quantities (all LPIPS-alex over predicted frames 1..16, unit = clip, mean +- SE over the 24 clips):
  L_real   : LPIPS(base_s, real), averaged over seeds 0-3       (rog1: 0.115 with correct actions)
  L_static : LPIPS(repeat real frame 0, real)                  (rog1: 0.130)
  margin   : L_static - L_real; n clips > 0                    (rog1: 0.015 +- 0.009, 17/24)
  D_seed   : LPIPS(base_si, base_sj), mean over the 6 seed pairs (rog1: 0.107); per frame f1/f4/f8/f16
             (rog1: 0.021/0.076/0.117/0.149). Also within R and N arms.
  ratio    : L_real / D_seed per clip (is the real future about as far as another seed?)
  D_prompt : LPIPS(base_s, N_s) and LPIPS(base_s, R_s), same seed = same noise on q8; ratio D_prompt / D_seed per clip
             (new: text-suffix effect vs seed effect in FD mode, the analogue of rog1's D_action / D_seed = 1.33).
CI: clip bootstrap (10k, seed 0) for means and median ratios.
Usage: rev5243.py <devset_bridge> <t210 clips dir> <t210 scores.json> <out.json>"""
import json, os, sys, itertools
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../tools/robot_pred"))
import score as S

devset, clips, scoresp, outp = sys.argv[1:5]
idx = json.load(open(os.path.join(devset, "index.json")))
cids = [c["id"] for c in idx["clips"]]
SEEDS = [0, 1, 2, 3]
FR = [1, 4, 8, 16]
real = {c: S.read(os.path.join(devset, c, "real.mp4"))[:17] for c in cids}

def clip(arm, cid, s):
    g = S.read(os.path.join(clips, f"t210_{arm}_{cid}_s{s}.mp4"))
    assert g.shape[0] == 17 and g.shape[1:3] == real[cid].shape[1:3], (arm, cid, s, g.shape)
    return g

per = {}
for cid in cids:
    g = {(a, s): clip(a, cid, s) for a in ("base", "R", "N") for s in SEEDS}
    r = real[cid]
    lreal_f = np.stack([S.lp(g[("base", s)][1:17], r[1:17]) for s in SEEDS])          # seeds x 16
    lstat_f = S.lp(np.repeat(r[:1], 16, 0), r[1:17])
    dseed = {}
    for a in ("base", "R", "N"):
        dseed[a] = np.stack([S.lp(g[(a, i)][1:17], g[(a, j)][1:17]) for i, j in itertools.combinations(SEEDS, 2)])  # 6 x 16
    dpN = np.stack([S.lp(g[("base", s)][1:17], g[("N", s)][1:17]) for s in SEEDS])
    dpR = np.stack([S.lp(g[("base", s)][1:17], g[("R", s)][1:17]) for s in SEEDS])
    per[cid] = {
        "L_real": float(lreal_f.mean()), "L_static": float(lstat_f.mean()),
        "L_real_f": lreal_f.mean(0).tolist(), "L_static_f": lstat_f.tolist(),
        "D_seed_base": float(dseed["base"].mean()), "D_seed_R": float(dseed["R"].mean()), "D_seed_N": float(dseed["N"].mean()),
        "D_seed_base_f": dseed["base"].mean(0).tolist(),
        "D_prompt_N": float(dpN.mean()), "D_prompt_R": float(dpR.mean()),
        "D_prompt_N_f": dpN.mean(0).tolist(), "D_prompt_R_f": dpR.mean(0).tolist(),
        "L_real_per_seed": lreal_f.mean(1).tolist(),
    }
    print(cid, {k: round(v, 4) for k, v in per[cid].items() if isinstance(v, float)}, flush=True)

# cross-check against my frozen t210 scores (same metric, should match L_real/L_static)
sc = json.load(open(scoresp))
chk = max(abs(per[c]["L_real"] - np.mean([sc["clips"][f"t210_base_{c}_s{s}"]["lpips"] for s in SEEDS])) for c in cids)
chk_s = max(abs(per[c]["L_static"] - sc["static"][c]["lpips"]) for c in cids)

rng = np.random.default_rng(0)
B = 10000
bi = rng.integers(0, len(cids), (B, len(cids)))
def summ(x, stat=np.mean):
    x = np.asarray(x, float)
    bs = np.array([stat(x[b]) for b in bi])
    return {"value": float(stat(x)), "se": float(x.std(ddof=1) / np.sqrt(len(x))) if stat is np.mean else None,
            "ci95_boot": [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))],
            "n_pos": int((x > 0).sum()), "n": len(x)}
col = lambda k: np.array([per[c][k] for c in cids])
colf = lambda k: np.array([per[c][k] for c in cids])  # clips x 16
out = {
    "setup": "t210 base/R/N x seeds 0-3, q8-0..7, CUDA noise (no noise.device), 24 devset_bridge clips, chunk 1 frames 1-16, LPIPS-alex",
    "check_vs_t210_scores_maxabs": {"L_real": chk, "L_static": chk_s},
    "L_real": summ(col("L_real")), "L_static": summ(col("L_static")),
    "margin_static_minus_real": summ(col("L_static") - col("L_real")),
    "D_seed_base": summ(col("D_seed_base")), "D_seed_R": summ(col("D_seed_R")), "D_seed_N": summ(col("D_seed_N")),
    "ratio_Lreal_over_Dseed_median": summ(col("L_real") / col("D_seed_base"), np.median),
    "ratio_Lreal_over_Dseed_mean": summ(col("L_real") / col("D_seed_base")),
    "D_prompt_N": summ(col("D_prompt_N")), "D_prompt_R": summ(col("D_prompt_R")),
    "ratio_DpromptN_over_Dseed_median": summ(col("D_prompt_N") / col("D_seed_base"), np.median),
    "ratio_DpromptR_over_Dseed_median": summ(col("D_prompt_R") / col("D_seed_base"), np.median),
    "n_clips_DpromptN_lt_Dseed": int((col("D_prompt_N") < col("D_seed_base")).sum()),
    "n_clips_DpromptR_lt_Dseed": int((col("D_prompt_R") < col("D_seed_base")).sum()),
    "per_frame": {f"f{f}": {k: float(colf(k)[:, f - 1].mean()) for k in
                  ("L_real_f", "L_static_f", "D_seed_base_f", "D_prompt_N_f", "D_prompt_R_f")} for f in FR},
    "seed_means_L_real": [float(np.mean([per[c]["L_real_per_seed"][i] for c in cids])) for i in range(len(SEEDS))],
    "per_clip": per,
}
json.dump(out, open(outp, "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "per_clip"}, indent=1))
