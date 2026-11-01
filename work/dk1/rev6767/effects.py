"""Main effects of the 2x2 box swap (dk1 review of #6767). Own code.
Usage: effects.py <scores.json from score.py> <t319 scores_gen.json> <out.json>
corridor = 1/2[(np-pp)+(nn-pn)], background = 1/2[(pn-pp)+(nn-np)], interaction = 1/2[(nn-np)-(pn-pp)].
CI: cluster bootstrap over the 6 scenes (resample scenes, average their 3-seed means), 20000 draws, seed 0.
"""
import json, re, sys
from pathlib import Path
import numpy as np

sc, ref, outp = sys.argv[1:4]
S = json.load(open(sc)); S = S if isinstance(S, list) else S.get("clips", list(S.values()))
R = json.load(open(ref)); R = R if isinstance(R, list) else R.get("clips", list(R.values()))
cell = {}
for r in S:
    m = re.search(r"bx_(\d\d)_s(\d)_(pp|nn|np|pn)\.mp4", r["clip"])
    if m:
        for met in ("dover_fused", "dover_technical", "dover_aesthetic"):
            cell[(m[1], m[2], m[3], met)] = r[met]
orig = {}
for r in R:
    m = re.search(r"t276_real_(\d\d)_(plain|nphys)_s(\d)\.mp4", r["clip"])
    if m:
        orig[(m[1], m[3], m[2])] = r["dover_fused"]
scenes = sorted({k[0] for k in cell}); seeds = sorted({k[1] for k in cell})
rng = np.random.default_rng(0)
out = {"n_scenes": len(scenes), "seeds": seeds}
for met in ("dover_fused", "dover_technical", "dover_aesthetic"):
    g = lambda s, d, c: cell[(s, d, c, met)]
    eff = {
        "total_nn_pp": lambda s, d: g(s, d, "nn") - g(s, d, "pp"),
        "corridor": lambda s, d: 0.5 * ((g(s, d, "np") - g(s, d, "pp")) + (g(s, d, "nn") - g(s, d, "pn"))),
        "background": lambda s, d: 0.5 * ((g(s, d, "pn") - g(s, d, "pp")) + (g(s, d, "nn") - g(s, d, "np"))),
        "interaction": lambda s, d: 0.5 * ((g(s, d, "nn") - g(s, d, "np")) - (g(s, d, "pn") - g(s, d, "pp"))),
    }
    res = {}
    for name, f in eff.items():
        X = np.array([[f(s, d) for d in seeds] for s in scenes])
        sm = X.mean(1)
        boot = sm[rng.integers(0, len(scenes), (20000, len(scenes)))].mean(1)
        res[name] = {"mean": float(X.mean()), "ci95": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                     "n_neg": int((X < 0).sum()), "n": int(X.size), "scene_means": dict(zip(scenes, map(float, sm)))}
    tot = res["total_nn_pp"]["mean"]
    res["background_share"] = res["background"]["mean"] / tot if tot else None
    out[met] = res
# re-encode sanity (fused): lossless pp vs original plain, nn vs original nphys
sh = {"pp_minus_plain": [], "nn_minus_nphys": [], "orig_nphys_minus_plain": []}
for s in scenes:
    for d in seeds:
        if (s, d, "plain") in orig:
            sh["pp_minus_plain"].append(cell[(s, d, "pp", "dover_fused")] - orig[(s, d, "plain")])
            sh["nn_minus_nphys"].append(cell[(s, d, "nn", "dover_fused")] - orig[(s, d, "nphys")])
            sh["orig_nphys_minus_plain"].append(orig[(s, d, "nphys")] - orig[(s, d, "plain")])
out["reencode_sanity_fused"] = {k: {"mean": float(np.mean(v)), "min": float(np.min(v)), "max": float(np.max(v)), "n": len(v)}
                                for k, v in sh.items() if v}
Path(outp).write_text(json.dumps(out, indent=1))
f = out["dover_fused"]
for k in ("total_nn_pp", "background", "corridor", "interaction"):
    print(f"{k:12s} {f[k]['mean']:+.4f} [{f[k]['ci95'][0]:+.4f}, {f[k]['ci95'][1]:+.4f}]  neg {f[k]['n_neg']}/{f[k]['n']}")
print("background share", round(f["background_share"], 3))
for met in ("dover_technical", "dover_aesthetic"):
    print(met, {k: round(out[met][k]["mean"], 4) for k in ("total_nn_pp", "background", "corridor")})
print(out["reencode_sanity_fused"])
