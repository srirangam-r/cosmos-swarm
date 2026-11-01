"""ro-1 task 22: per-arm table from meas/pend_results.json.
Key quantities: period in generated frames (P_f), period in conditioned seconds (P_f/fps_cond),
and the period when played back at 24 fps (P_f/24, the 'condition low, play at 24' recipe). Real GAUGE small-angle period ~1.05 s."""
import json, statistics as st, collections
rows = json.load(open("meas/pend_results.json"))
g = collections.defaultdict(list)
for r in rows:
    if r["name"].startswith("pend") and r.get("period_frames"):
        g[(r["arm"], r["fps"], "durOFF" in r["name"])].append(r)
def ms(x): return (st.mean(x), st.stdev(x) if len(x) > 1 else float("nan"))
out = []
for (arm, fps, off), rs in sorted(g.items()):
    pf = [r["period_frames"] for r in rs]
    m, s = ms(pf)
    d = dict(arm=arm, fps_cond=fps, dur_template=("off" if off else "on"), n=len(rs), seeds=[r["seed"] for r in rs],
             flags=[r["flag"] for r in rs], r2=[round(r["r2"], 2) for r in rs],
             period_frames=[round(p, 1) for p in pf], P_frames_mean=round(m, 1), P_frames_sd=round(s, 1),
             P_cond_s=round(m / fps, 2), P_play24_s=round(m / 24, 2), ratio_play24_vs_real=round(m / 24 / 1.05, 2))
    out.append(d); print(json.dumps(d))
json.dump(out, open("meas/summary.json", "w"), indent=1)
