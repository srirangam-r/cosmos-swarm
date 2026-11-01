"""ro-1 task 22: run measure_pend v1 (raj-3, planted PASS) on every sweep clip at its CONDITIONED fps.
Reports period in conditioned seconds and in frames (period_frames = T_s * fps_cond) — the key quantity:
if Nano honours the fps, period_frames should scale with fps_cond (real period constant in seconds)."""
import json, subprocess, sys, glob, os
PY = sys.executable; TOOL = "../cosmos-swarm/tools/trk_ballfall/measure_pend.py"
rows = []
for side in sorted(glob.glob("out/*.json")):
    j = json.load(open(side)); mp4 = side[:-5] + ".mp4"; name = j["name"]
    if name.startswith("ball"):  # measure_bounce v1 (raj-3, referee composite PASS): g from first rebound flight
        cmd = [PY, "-I", TOOL.replace("measure_pend", "measure_bounce"), mp4, "--fps", str(j["fps"]), "--ppm", "539.8", "--qc", f"meas/{name}_qc.png"]
    else:
        cmd = [PY, "-I", TOOL, mp4, "--fps", str(j["fps"]), "--qc", f"meas/{name}_qc.png"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        m = json.loads(r.stdout[r.stdout.index("{"):])
    except Exception:
        m = {"error": r.stderr[-500:]}
    fps = float(j["fps"])
    row = dict(name=name, arm=j.get("arm"), fps=fps, num_frames=j["num_frames"], seed=j["seed"],
               stated_s=round(j["num_frames"] / fps, 3), **{k: m.get(k) for k in ("g", "g_ci95", "g_pooled", "period_s", "period_ci95", "period_zc_s", "r2", "n_halfcycles", "flag", "release_frame", "amp_px", "error")})
    if m.get("period_s"):
        row["period_frames"] = m["period_s"] * fps
        row["period_zc_frames"] = (m["period_zc_s"] or float("nan")) * fps
    if row.get("g") is not None:
        row["g_per_frame2_px"] = row["g"] * 539.8 / fps**2  # px/frame^2: fps-independent motion per frame
    rows.append(row); print(json.dumps(row), flush=True)
json.dump(rows, open("meas/pend_results.json", "w"), indent=1)
