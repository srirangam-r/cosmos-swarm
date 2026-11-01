"""Per-clip comparison: original-VBench dd (rog2) vs tools/nv_scoreboard re-implementation (raj-4, msg 159)."""
import json, sys
import numpy as np

mine = json.load(open(sys.argv[1]))
ref = json.load(open(sys.argv[2]))
alias = lambda k: k.replace("slope_", "slopewood_")
rows, out = [], {}
print(f"{'clip':14s} {'bin r4/me':>9s} {'norm r4':>8s} {'norm me':>8s} {'rel%':>6s} {'frac r4':>7s} {'frac me':>7s} {'maxrad |d| med/max px':>22s}")
for k, m in mine.items():
    r = ref.get(alias(k))
    if r is None:
        continue
    a, b = np.array(r["dd_maxrad"]), np.array(m["maxrad"])
    n = min(len(a), len(b))
    d = np.abs(a[:n] - b[:n])
    rel = 100 * (m["dd_norm"] - r["dd_norm"]) / r["dd_norm"]
    out[k] = dict(bin_r4=r["dd_binary"], bin_me=m["dd_binary"], norm_r4=r["dd_norm"], norm_me=m["dd_norm"],
                  rel_pct=rel, frac_r4=r["dd_frac"], frac_me=m["dd_frac"], pairs_r4=len(a), pairs_me=len(b),
                  maxrad_absdiff_median=float(np.median(d)), maxrad_absdiff_max=float(d.max()))
    print(f"{k:14s} {r['dd_binary']:>4d}/{m['dd_binary']:<4d} {r['dd_norm']:8.3f} {m['dd_norm']:8.3f} {rel:6.2f} "
          f"{r['dd_frac']:7.3f} {m['dd_frac']:7.3f} {np.median(d):10.4f}/{d.max():.4f}  pairs {len(a)}/{len(b)}")
for t in ("ball", "pend", "slope"):
    ks = [k for k in out if k.startswith(t)]
    if not ks:
        continue
    nm = np.array([out[k]["norm_me"] for k in ks]); fm = np.array([out[k]["frac_me"] for k in ks])
    bm = sum(out[k]["bin_me"] for k in ks)
    print(f"{t}: mine dd_binary {bm}/{len(ks)}, dd_norm {nm.mean():.3f}±{nm.std(ddof=1):.3f}, dd_frac {fm.mean():.3f}±{fm.std(ddof=1):.3f}")
json.dump(out, open(sys.argv[3], "w"), indent=1)
