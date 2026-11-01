"""rev6747 summary: dk2 pend_track readout of dk1 t329a (supplied A=18 deg) vs the paired release-from-rest clips (276/277)."""
import json, re, numpy as np
R = json.load(open("../cosmos-swarm/work/dk1/t329_amp/out/t276_results.json"))["rows"]
Preal = {}
for r in R:
    if r["ratio"] and r["arm"] == "nphys": Preal[r["frame"]] = r["P_acf_s"] / r["ratio"]
new, old = json.load(open("t329a_est.json")), json.load(open("old_est.json")); out = {"P_real_s": Preal, "rows": []}
for tag, D in [("A18", new), ("rest", old)]:
    for k, v in D.items():
        m = re.search(r"(real_\d\d)_nphys(_x17)?_s(\d+)", k); sc, x17, s = m.group(1), bool(m.group(2)), int(m.group(3))
        out["rows"].append(dict(clip=k, proxy=tag, scene=sc, x17=x17, seed=s, flag=v["flag"], ratio=v.get("P_fit", np.nan) / Preal[sc], amp_px=v.get("amp_px"), R2=v.get("R2")))
summ = {}
for tag in ["A18", "rest"]:
    for x17 in [False, True]:
        rr = [r for r in out["rows"] if r["proxy"] == tag and r["x17"] == x17]
        ok = [r for r in rr if r["flag"] == "ok"]; rat = np.array([r["ratio"] for r in ok])
        tgt = 1.7 if x17 else 1.0; within = int(np.sum(np.abs(rat / tgt - 1) < 0.10))
        summ[f"{tag}{'_x17' if x17 else ''}"] = dict(n=len(rr), n_ok=len(ok), n_ok_within10=within,
            median_ratio_ok=float(np.median(rat)) if len(rat) else None, ratio_ok=[round(float(x), 3) for x in rat],
            median_amp_px=float(np.median([r["amp_px"] for r in rr])), amp_px=[round(r["amp_px"], 1) for r in rr])
out["summary"] = summ
# paired on scene x seed (normal period arm)
pairs = []
for r in out["rows"]:
    if r["proxy"] == "A18" and not r["x17"]:
        o = [q for q in out["rows"] if q["proxy"] == "rest" and not q["x17"] and q["scene"] == r["scene"] and q["seed"] == r["seed"]]
        if o: pairs.append((r["clip"], o[0]["clip"], r["flag"] == "ok" and abs(r["ratio"] - 1) < .1, o[0]["flag"] == "ok" and abs(o[0]["ratio"] - 1) < .1, r["amp_px"] / max(o[0]["amp_px"], 1e-6)))
out["pairs"] = pairs
json.dump(out, open("rev6747_summary.json", "w"), indent=1)
for k, v in summ.items(): print(k, v)
for p in pairs: print(p)
