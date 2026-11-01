"""Paired analysis of flow.json (from flow_regions.py) for the #1448 replication.
Arms: A rope24/text24, B rope12/text24, C rope24/text12, D rope12/text12, E rope6/text24; seeds 3-10.
Stats: per-seed paired differences, mean +- SE (sd/sqrt(n)), n=8.
Clock test: per pair (ref A_s, X_s) find k in [0.5,4] minimising mean sq. error between X(t) and A(k t)
(both divided by their own clip mean; linear interp; >=20 overlapping pairs). A pure clock predicts
k = 24/rope (B,D: 2; E: 4; C: 1). Null: A_s vs A_{s'} (different seeds) for the same fit.
"""
import json, sys, itertools
import numpy as np

R = json.load(open(sys.argv[1]))
ARMS = {"A": "armA_rope24_text24", "B": "armB_rope12_text24", "C": "armC_rope24_text12",
        "D": "armD_rope12_text12", "E": "armE_rope6_text24"}
SEEDS = range(3, 11)
get = lambda arm, s, roi: np.array(R[f"{ARMS[arm]}_s{s}"][roi])
out = {}


def ms(v):
    v = np.asarray(v, float); return float(v.mean()), float(v.std(ddof=1) / np.sqrt(len(v)))


for roi in ["arm", "table", "whole"]:
    for win, sl in [("last24", slice(-24, None)), ("all", slice(None))]:
        lv = {a: [get(a, s, roi)[sl].mean() for s in SEEDS] for a in ARMS}
        row = {a: ms(lv[a]) for a in ARMS}
        for x, y in [("B", "A"), ("D", "C"), ("C", "A"), ("D", "B"), ("E", "A")]:
            d = np.array(lv[x]) - np.array(lv[y])
            row[f"{x}-{y}"] = ms(d) + (int((d > 0).sum()),)
        out[f"{roi}_{win}"] = row

KS = np.round(np.arange(0.5, 4.001, 0.05), 3)


def mse_k(ref, x, k):
    ref = ref / ref.mean(); x = x / x.mean()
    t = np.arange(len(x)); tk = k * t; ok = tk <= len(ref) - 1
    if ok.sum() < 20: return np.nan
    return float(np.mean((x[ok] - np.interp(tk[ok], np.arange(len(ref)), ref)) ** 2))


for roi in ["arm", "table", "whole"]:
    res = {}
    for x in ["B", "C", "D", "E"]:
        curves = np.array([[mse_k(get("A", s, roi), get(x, s, roi), k) for k in KS] for s in SEEDS])
        res[x] = {"k_pooled": float(KS[np.nanargmin(np.nanmean(curves, 0))]),
                  "k_per_seed": [float(KS[np.nanargmin(c)]) for c in curves]}
        res[x]["k_median"] = float(np.median(res[x]["k_per_seed"]))
    nullc = np.array([[mse_k(get("A", s, roi), get("A", s2, roi), k) for k in KS]
                      for s, s2 in itertools.permutations(SEEDS, 2)])
    nk = [float(KS[np.nanargmin(c)]) for c in nullc]
    res["null_AA"] = {"k_pooled": float(KS[np.nanargmin(np.nanmean(nullc, 0))]), "k_median": float(np.median(nk)),
                      "k_p10_p90": [float(np.percentile(nk, 10)), float(np.percentile(nk, 90))], "n_pairs": len(nk)}
    out[f"timewarp_{roi}"] = res

# motion "settle" proxy: first pair after which 5-pair smoothed whole-frame flow stays below 0.5 px/frame
def settle(v, thr=0.5):
    sm = np.convolve(v, np.ones(5) / 5, mode="same")
    above = np.where(sm >= thr)[0]
    return int(above[-1] + 1) if len(above) else 0
out["settle_pair_whole_thr0.5px"] = {a: ms([settle(get(a, s, "whole")) for s in SEEDS]) for a in ARMS}
json.dump(out, open(sys.argv[2], "w"), indent=1)
for k, v in out.items():
    print(k, json.dumps(v, default=lambda o: o)[:600])
