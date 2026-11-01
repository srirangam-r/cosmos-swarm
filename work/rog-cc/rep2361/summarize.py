"""rog-cc rep2361: aggregate readout.json + eye_codes.json by arm (rest vs mid); Fisher exact on swing counts."""
import json, sys, numpy as np
from math import comb
R = json.load(open(sys.argv[1])); E = json.load(open(sys.argv[2])); real = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else {}
out = {}
for arm in ("rest", "mid"):
    names = sorted(n for n in R if f"_{arm}_" in n)
    zm = np.array([R[n]["zone_motion"] for n in names]); ps = np.array([R[n]["passes"] for n in names])
    sw = [n for n in names if E.get(n, "").startswith("swing")]
    out[arm] = dict(n=len(names), swing_eye=len(sw), coded=sum(n in E for n in names),
                    zone_motion_mean=float(zm.mean()), zone_motion_se=float(zm.std(ddof=1) / np.sqrt(len(zm))) if len(zm) > 1 else None,
                    passes=ps.tolist(), clips_with_pass=int((ps > 0).sum()), names=names)
a, b = out["rest"]["swing_eye"], out["mid"]["swing_eye"]; n1, n2 = out["rest"]["coded"], out["mid"]["coded"]
# two-sided Fisher exact on [[a, n1-a],[b, n2-b]]
K = a + b; N = n1 + n2
def p(x): return comb(n1, x) * comb(n2, K - x) / comb(N, K)
p0 = p(a); out["fisher_p_two_sided"] = float(sum(p(x) for x in range(max(0, K - n2), min(K, n1) + 1) if p(x) <= p0 + 1e-12))
out["real_reference"] = {k: {kk: v[kk] for kk in ("zone_motion", "passes", "occupancy")} for k, v in real.items()}
print(json.dumps(out, indent=1)); json.dump(out, open("summary.json", "w"), indent=1)
