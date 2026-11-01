"""t332 quality readout (pre-registered in README): paired DOVER rln − plain and rln − nphys by scene×seed, exact scene bootstrap.
Usage: python analyze_t332.py scores_t332.json ../t319/scores_gen.json out.json"""
import sys, json, re, itertools, numpy as np
def load(p):
    t = open(p).read().strip()
    try: d = json.loads(t)
    except Exception: d = [json.loads(l) for l in t.splitlines() if l.startswith("{")]
    if isinstance(d, dict): d = d.get("results", d.get("clips", list(d.values())))
    return {re.sub(r".*/|\.mp4$", "", r["clip"]): r for r in d}
N, O = load(sys.argv[1]), load(sys.argv[2]); out = {}
scenes = sorted({re.match(r"t332_(real_\d\d)_", k).group(1) for k in N})
for met in ["dover_fused", "dover_technical", "dover_aesthetic"]:
    for ref in ["plain", "nphys"]:
        d = np.array([[N[f"t332_{sc}_rln_s{s}"][met] - O[f"t276_{sc}_{ref}_s{s}"][met] for s in [1, 2, 3]] for sc in scenes])
        sm = d.mean(1); B = np.array(list(itertools.product(range(len(sc_ := scenes)), repeat=len(scenes))))
        bm = sm[B].mean(1)
        out[f"{met}_rln_minus_{ref}"] = dict(mean=float(d.mean()), ci95=[float(np.percentile(bm, 2.5)), float(np.percentile(bm, 97.5))],
                                             n_neg=int((d < 0).sum()), n=int(d.size), scene_means=dict(zip(scenes, map(float, sm))))
    x = [N[f"t332_{sc}_rln_x17_s1"][met] - N[f"t332_{sc}_rln_s1"][met] for sc in scenes if f"t332_{sc}_rln_x17_s1" in N]
    out[f"{met}_x17rln_minus_rln_s1"] = float(np.mean(x)) if x else None
tot = out["dover_fused_rln_minus_plain"]["mean"]; nph = np.mean([O[f"t276_{sc}_nphys_s{s}"]["dover_fused"] - O[f"t276_{sc}_plain_s{s}"]["dover_fused"] for sc in scenes for s in [1, 2, 3]])
out["nphys_minus_plain_same_scenes"] = float(nph); out["fraction_recovered"] = float(1 - tot / nph)
out["PASS_quality"] = out["dover_fused_rln_minus_plain"]["ci95"][0] > -0.030
json.dump(out, open(sys.argv[3], "w"), indent=1)
for k, v in out.items(): print(k, v if not isinstance(v, dict) else (round(v["mean"], 4), [round(c, 4) for c in v["ci95"]], f"{v['n_neg']}/{v['n']}"))
