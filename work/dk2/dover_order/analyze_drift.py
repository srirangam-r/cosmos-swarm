"""DOVER batch-order noise check + independent 20-rep rescoring of dk1 t336 band clips.
Usage: python3 analyze_drift.py <drift_dir> <t319 scores_gen.json> <dk1 quality_band5.json> <out.json>
"""
import json, sys, os
D, G, Q, OUT = sys.argv[1:5]
L = lambda f: json.load(open(os.path.join(D, f)))
g = json.load(open(G)); q = json.load(open(Q))
out = {}
# 1. batch-order dependence without per-clip seeding (3 reps) and 20-rep reference
o = {}
for f in ["pair_fwd", "pair_rev", "pair_r20", "pcs_fwd", "pcs_rev"]:
    for k, v in L(f + ".json").items():
        o.setdefault(k, {})[f] = round(v["dover_fused"], 4)
for k in o:
    o[k]["t319_batch42_r3"] = round(g[k]["dover_fused"], 4)
out["order_check"] = o
# 2. per-draw SD at 20 reps
r20 = {**L("pair_r20.json"), **L("ref12_r20.json"), **L("t336_r20.json")}
if os.path.exists(os.path.join(D, "t319_r20_partial.json")):
    r20p = L("t319_r20_partial.json")
else:
    r20p = {}
sds = [v["dover_fused_sd"] for v in list(r20.values()) + list(r20p.values())]
out["per_draw_sd_fused"] = dict(n=len(sds), median=sorted(sds)[len(sds) // 2], min=min(sds), max=max(sds))
out["t319_partial_r20_vs_r3"] = {k: [round(v["dover_fused"], 4), round(g[k]["dover_fused"], 4)] for k, v in r20p.items()}
# 3. band arms vs plain/nphys, same seed, all at 20 reps per-clip-seeded
ref = L("ref12_r20.json"); band = L("t336_r20.json")
rows = []
dk1 = {r["clip"]: r for r in q["rows"]}
for k, v in sorted(band.items()):
    s = k.split("_s")[-1].split(".")[0]
    pl = ref[f"t276_real_12_plain_s{s}.mp4"]["dover_fused"]; np_ = ref[f"t276_real_12_nphys_s{s}.mp4"]["dover_fused"]
    d = dk1[k[:-4]]
    rows.append(dict(clip=k, dover_r20=round(v["dover_fused"], 4), dk1_r3=round(d["dover_fused"], 4),
                     plain_r20=round(pl, 4), nphys_r20=round(np_, 4),
                     d_vs_plain=round(v["dover_fused"] - pl, 4), dk1_d_vs_plain_raw=round(d["d_vs_plain"], 4),
                     dk1_d_vs_plain_driftcorr=round(d["d_vs_plain_driftcorr"], 4),
                     d_vs_nphys=round(v["dover_fused"] - np_, 4), pass_ge_m0020=v["dover_fused"] - pl >= -0.020))
out["band_rows"] = rows
for arm in ["reg", "regsfr"]:
    rr = [r for r in rows if f"_{arm}_s" in r["clip"]]
    out[f"summary_{arm}"] = dict(n=len(rr), mean_d_vs_plain=round(sum(r["d_vs_plain"] for r in rr) / len(rr), 4),
                                 mean_d_vs_nphys=round(sum(r["d_vs_nphys"] for r in rr) / len(rr), 4),
                                 n_pass=sum(r["pass_ge_m0020"] for r in rr))
json.dump(out, open(OUT, "w"), indent=1)
print(json.dumps(out, indent=1))
