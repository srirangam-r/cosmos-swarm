"""Frozen re-decision for E6 and E6-W (dk2, task 258). Implements README rule 2/3 exactly; committed BEFORE any B/C/W clip is
visible to dk2. Input: one xcheck.py JSON covering real_XX, realw_XX, A_/B_/C_ (E6) and WA_/W_ (E6-W) clips.
usage: python3 -I redecide.py xcheck1.json [xcheck2.json ...] > redecide.json  (rows merged by clip name)

E6 per arm (recon/base/tlo/slo/all), for tool in (acf, mp):
  ratio = P_clip / P_real[target]. acf: P_real needs flag_acf ok, P_clip any non-null (as analyze_e6).
  mp: P_real needs flag_mp ok (real_13 drops), P_clip any non-null P_mp (mp flag does not gate; README rule 1).
  category = "real clock" if |median ratio - 1| <= 0.10, "slower than real" if > 1.10, "faster than real" if < 0.90.
E6-W per arm (tlo, all): f = ln(P_W/P_C)/ln(0.7), mean per target, median over targets, 2000 target-cluster bootstrap
  (rng seed 0), decision thresholds as analyze_e6w (lo > 0.5 carries / hi < 0.25 does not / else inconclusive).
  acf variant gates on flag_acf ok for both W and C (as analyze_e6w); mp variant uses any non-null P_mp.
Verdict per quantity: "planted-backed" if category/decision identical for acf and mp, else "tool-dependent".
"""
import json, re, sys
import numpy as np


def load(paths):
    rows = {}
    for p in paths:
        for r in json.load(open(p)): rows[r["clip"]] = r
    return rows


def P(row, tool, gate):
    if row is None: return None
    if tool == "acf":
        return row.get("P_acf") if (row.get("flag_acf") == "ok" or not gate) else None
    return row.get("P_mp") if (row.get("flag_mp") == "ok" or not gate) else None


def cat(m):
    if m is None: return "no data"
    return "real clock" if abs(m - 1) <= 0.10 else ("slower than real" if m > 1.10 else "faster than real")


def e6(rows, tool):
    out = {}
    for arm in ("recon", "base", "tlo", "slo", "all"):
        R = []
        for c, r in rows.items():
            m = (re.match(r"A_rec(\d+)$", c) if arm == "recon" else re.match(r"B_rec(\d+)_s\d+$", c) if arm == "base"
                 else re.match(rf"C_t(\d+)_d\d+_{arm}_s\d+$", c))
            if not m: continue
            Pr = P(rows.get(f"real_{int(m.group(1)):02d}"), tool, gate=True); Pc = P(r, tool, gate=False)
            R.append(Pc / Pr if Pc and Pr else None)
        ok = [x for x in R if x]
        med = float(np.median(ok)) if ok else None
        out[arm] = dict(n=len(R), n_read=len(ok), median_ratio=med, within_10pct=sum(abs(x - 1) <= 0.10 for x in ok),
                        category=cat(med))
    return out


def e6w(rows, tool):
    out = {}
    for arm in ("tlo", "all"):
        byt, npairs = {}, 0
        for c, r in rows.items():
            m = re.match(rf"W_t(\d+)_d(\d+)_{arm}_s(\d+)$", c)
            if not m: continue
            npairs += 1; t, d, s = m.groups()
            gate = tool == "acf"
            Pw, Pc = P(r, tool, gate), P(rows.get(f"C_t{t}_d{d}_{arm}_s{s}"), tool, gate)
            if Pw and Pc: byt.setdefault(int(t), []).append(np.log(Pw / Pc) / np.log(0.7))
        ft = np.array([np.mean(v) for v in byt.values()]); a = dict(n_pairs=npairs, n_targets=len(ft))
        if len(ft) >= 3:
            rng = np.random.default_rng(0)
            lo, hi = np.percentile([np.median(rng.choice(ft, len(ft))) for _ in range(2000)], [2.5, 97.5])
            a.update(median_f=float(np.median(ft)), ci=[float(lo), float(hi)],
                     decision=("band carries the donor's clock" if lo > 0.5 else
                               "donor speed does not set the clock" if hi < 0.25 else "partial / inconclusive"))
        else:
            a["decision"] = "too few readable pairs (<3 targets)"
        out[arm] = a
    return out


if __name__ == "__main__":
    rows = load(sys.argv[1:])
    both = [r for r in rows.values() if r.get("flag_acf") == "ok" and r.get("P_mp") and r.get("P_acf")]
    agree = sum(abs(r["P_mp"] / r["P_acf"] - 1) <= 0.05 for r in both)
    res = dict(agreement=dict(n=len(both), within_5pct=agree), e6={t: e6(rows, t) for t in ("acf", "mp")},
               e6w={t: e6w(rows, t) for t in ("acf", "mp")})
    res["verdict"] = {f"e6_{a}": ("planted-backed" if res["e6"]["acf"][a]["category"] == res["e6"]["mp"][a]["category"]
                                  else "tool-dependent") for a in ("recon", "base", "tlo", "slo", "all")}
    res["verdict"].update({f"e6w_{a}": ("planted-backed" if res["e6w"]["acf"][a]["decision"] == res["e6w"]["mp"][a]["decision"]
                                        else "tool-dependent") for a in ("tlo", "all")})
    print(json.dumps(res, indent=1))
