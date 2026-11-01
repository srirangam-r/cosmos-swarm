"""t331 analysis: 2x2 factorial (corridor src x background src) on DOVER fused/technical/aesthetic.
Usage: python analyze_t331.py scores_t331.json swap_meta.json ../t319/scores_gen.json out.json"""
import sys, json, re, itertools, numpy as np
sc_path, meta_path, orig_path, outp = sys.argv[1:5]
def load(p):
    t = open(p).read().strip()
    try: d = json.loads(t)
    except Exception: d = [json.loads(l) for l in t.splitlines() if l.startswith("{")]
    if isinstance(d, dict): d = d.get("results", d.get("clips", list(d.values())))
    return {re.sub(r".*/|\.mp4$", "", r["clip"]): r for r in d}
S, O = load(sc_path), load(orig_path); meta = json.load(open(meta_path))
scenes = ["09", "12", "16", "17", "18", "19"]; seeds = [1, 2, 3]
res = {}
rng = np.random.default_rng(0)
for met in ["dover_fused", "dover_technical", "dover_aesthetic"]:
    rows = []
    for sc, s in itertools.product(scenes, seeds):
        g = lambda k: S[f"sw_{sc}_s{s}_{k}"][met]
        pp, nn, np_, pn = g("pp"), g("nn"), g("np"), g("pn")
        rows.append(dict(scene=sc, seed=s, pp=pp, nn=nn, np=np_, pn=pn,
                         total=nn - pp,
                         corridor=0.5 * ((np_ - pp) + (nn - pn)),   # swap corridor plain->nphys
                         background=0.5 * ((pn - pp) + (nn - np_)), # swap background plain->nphys
                         interaction=(nn - np_) - (pn - pp),
                         reenc_plain=pp - O[f"t276_real_{sc}_plain_s{s}"][met],
                         reenc_nphys=nn - O[f"t276_real_{sc}_nphys_s{s}"][met]))
    summ = {}
    for k in ["total", "corridor", "background", "interaction", "reenc_plain", "reenc_nphys"]:
        x = np.array([r[k] for r in rows]).reshape(6, 3)
        sm = x.mean(1)  # scene means
        boot = [sm[rng.integers(0, 6, 6)].mean() for _ in range(20000)]
        summ[k] = dict(mean=float(x.mean()), ci95=[float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
                       n_neg=int((x < 0).sum()), n=18, scene_means=[float(v) for v in sm])
    t = summ["total"]["mean"]
    summ["share_background"] = summ["background"]["mean"] / t if t else None
    summ["share_corridor"] = summ["corridor"]["mean"] / t if t else None
    res[met] = dict(summary=summ, rows=rows)
prox = {k: {m: v[m] for m in ["dover_fused", "dover_technical", "dover_aesthetic"]} for k, v in S.items() if k.startswith("proxy_")}
res["proxies"] = prox
res["proxy_mean_fused_nphys"] = float(np.mean([v["dover_fused"] for k, v in prox.items() if not k.endswith("x17")]))
res["mask"] = meta["meta"]; res["mask_params"] = meta["params"]
sh = meta["sharp"]
for k in ["plain", "nphys"]:
    res[f"bg_sharp_ratio_{k}"] = float(np.mean([v["ratio_mean"] for kk, v in sh.items() if kk.endswith(k)]))
    res[f"bg_sharp_ratio_last10_{k}"] = float(np.mean([v["ratio_last10"] for kk, v in sh.items() if kk.endswith(k)]))
json.dump(res, open(outp, "w"), indent=1)
for met in ["dover_fused", "dover_technical", "dover_aesthetic"]:
    s = res[met]["summary"]
    print(met, {k: (round(v["mean"], 4), [round(c, 4) for c in v["ci95"]], v["n_neg"]) for k, v in s.items() if isinstance(v, dict)},
          "share_bg", s["share_background"] and round(s["share_background"], 2), "share_corr", s["share_corridor"] and round(s["share_corridor"], 2))
print("proxy DOVER fused (nphys proxies):", round(res["proxy_mean_fused_nphys"], 4), {k: round(v["dover_fused"], 3) for k, v in prox.items()})
print("bg sharpness ratio vs frame0: plain", round(res["bg_sharp_ratio_plain"], 3), "nphys", round(res["bg_sharp_ratio_nphys"], 3),
      "| last10: plain", round(res["bg_sharp_ratio_last10_plain"], 3), "nphys", round(res["bg_sharp_ratio_last10_nphys"], 3))
