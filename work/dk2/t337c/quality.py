# dk2 t337c: copy of dk1 work/dk1/t336_region/quality_b.py @dc1a6f7, names only changed (t336b_->t337c_, inj19->dc10, inj27->dc14).
#!/usr/bin/env python3
"""Task 336 quality readout (FROZEN before any clip). Compares score.py output for the t336 arms with t319's stored
plain/nphys scores (work/dk2/t319/scores_gen.json @9e92945, same scorer, same RTX 4060 laptop, --dover_reps 3).
usage: python3 quality.py <t336 scores.json> <out.json>
Per arm A in {reg, regsfr}: per scene seed-mean of A - plain (paired by scene, seeds 1-3); Delta_A = mean over 4 scenes;
95% CI = percentile interval over all 4^4 scene resamples; recovery = (A - nphys)/(plain - nphys) pooled; same for
technical, aesthetic, dd_norm (and dd_norm vs real 1.94). Also per-pair sign counts (A - plain, A - nphys).
x17 arms (seed 1): A_x17 - plain_s1 per scene, descriptive.
Fix-candidate quality half: Delta_A >= -0.020.
"""
import itertools, json, sys
from pathlib import Path
import numpy as np
R = Path(__file__).resolve().parents[3]
BASE = json.load(open(R / "work/dk2/t319/scores_gen.json"))
SC = ("real_12", "real_17", "real_18", "real_19"); SEEDS = (1, 2, 3)
METRICS = ("dover_fused", "dover_technical", "dover_aesthetic", "dd_norm")


def get(d, name, m):
    v = d.get(name + ".mp4") or d.get(name)
    return None if v is None else v.get(m)


def boot(per_scene):
    means = [np.mean(c) for c in itertools.product(per_scene, repeat=len(per_scene))]
    return [round(float(np.percentile(means, 2.5)), 5), round(float(np.percentile(means, 97.5)), 5)]


def main():
    new = json.load(open(sys.argv[1])); out = {"arms": {}, "x17": {}}
    for arm in ("dc10", "dc14"):
        A = {}
        for m in METRICS:
            dA, dN, base_gap, pairs_lt_plain, pairs_gt_nphys, n = [], [], [], 0, 0, 0
            for sc in SC:
                a = [get(new, f"t337c_{sc}_{arm}_s{s}", m) for s in SEEDS]
                p = [get(BASE, f"t276_{sc}_plain_s{s}", m) for s in SEEDS]
                q = [get(BASE, f"t276_{sc}_nphys_s{s}", m) for s in SEEDS]
                if None in a: continue
                dA.append(np.mean(a) - np.mean(p)); dN.append(np.mean(a) - np.mean(q)); base_gap.append(np.mean(p) - np.mean(q))
                pairs_lt_plain += sum(x < y for x, y in zip(a, p)); pairs_gt_nphys += sum(x > y for x, y in zip(a, q)); n += 3
            if not dA: continue
            A[m] = dict(n_scenes=len(dA), delta_vs_plain=round(float(np.mean(dA)), 5), ci95=boot(dA),
                        delta_vs_nphys=round(float(np.mean(dN)), 5), ci95_vs_nphys=boot(dN),
                        recovery=round(float(np.mean(dN) / np.mean(base_gap)), 3) if np.mean(base_gap) else None,
                        pairs_below_plain=f"{pairs_lt_plain}/{n}", pairs_above_nphys=f"{pairs_gt_nphys}/{n}",
                        per_scene_vs_plain=[round(float(x), 5) for x in dA])
        if "dover_fused" in A:
            A["quality_half_pass"] = A["dover_fused"]["delta_vs_plain"] >= -0.020
        out["arms"][arm] = A
    for arm in ("dc10_x17", "dc14_x17"):
        out["x17"][arm] = {sc: dict(fused=get(new, f"t337c_{sc}_{arm}_s1", "dover_fused"),
                                    fused_minus_plain_s1=(None if get(new, f"t337c_{sc}_{arm}_s1", "dover_fused") is None else
                                                          round(get(new, f"t337c_{sc}_{arm}_s1", "dover_fused") - get(BASE, f"t276_{sc}_plain_s1", "dover_fused"), 5)),
                                    dd_norm=get(new, f"t337c_{sc}_{arm}_s1", "dd_norm")) for sc in SC}
    json.dump(out, open(sys.argv[2], "w"), indent=1)
    for arm, A in out["arms"].items():
        for m, v in A.items():
            if isinstance(v, dict): print(arm, m, v["delta_vs_plain"], v["ci95"], "rec", v["recovery"], v["pairs_below_plain"])
        print(arm, "quality_half_pass", A.get("quality_half_pass"))


if __name__ == "__main__":
    main()
