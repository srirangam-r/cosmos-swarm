#!/usr/bin/env python3
"""Print the task-113 numbers compactly for the board post (reads summary.json [+ refdist.json])."""
import json, os, sys
d = json.load(open(sys.argv[1]))
v = d["validity"]
print("n_clips_judged", d["n_clips_judged"])
print("V1 real-static mf_phys %.3f gauge_phys %.3f pass=%s" % (v["V1_real_minus_static_mf_physical"],
      v["V1_real_minus_static_gauge_physical"], v["V1_pass"]))
print("V2 16+17 %.2f  18+19 %.2f" % (v["V2_twin_sum_bounce_lower(16+17)"], v["V2_twin_sum_rest(18+19)"]))
for k, c in d["contrasts"].items():
    print("%-34s %+.3f±%.3f CI90[%+.3f,%+.3f] n=%d up=%d %s  (%s=%.3f F=%.3f)" % (
        k, c["mean"], c["se"], c["ci90"][0], c["ci90"][1], c["n"], c["n_up"], c.get("verdict", ""),
        k.split(":")[1].split("-")[0], c[[x for x in c if x.startswith("mean_") and x != "mean_F"][0]], c["mean_F"]))
for k, r in d["real"].items():
    print("real", k, {s: round(x, 3) for s, x in r.items()})
for k, r in d["static"].items():
    print("static", k, {s: round(x, 3) for s, x in r.items()})
for k, r in d["arm_means"].items():
    print("arm", k, {s: round(x, 3) for s, x in r.items()})
pr = d["perq_raw_full"]
print("perq full (F/QT/real):")
real = list(d["perq_raw_real"].values())
for q in range(1, 23):
    print(" q%d F %.2f QT %.2f%s" % (q, pr["F"][str(q)] if str(q) in pr["F"] else pr["F"][q],
          pr["QT"][str(q)] if str(q) in pr["QT"] else pr["QT"][q],
          "".join(" r %.2f" % (r[str(q)] if str(q) in r else r[q]) for r in real)))
if len(sys.argv) > 2 and os.path.exists(sys.argv[2]):
    print("REFDIST", open(sys.argv[2]).read()[:3000])
