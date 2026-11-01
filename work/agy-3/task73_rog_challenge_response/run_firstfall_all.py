#!/usr/bin/env python3
"""Run referee-validated firstfall.py (tools/realball/firstfall.py) on all 16 Brev A100 clips:
- 8 Baseline held clips (box_ctrl_b{1,2}_noneg_s{1,2,3,4}.mp4)
- 8 Recipe midfall clips (box_mid_b{1,2}_noneg_s{1,2,3,4}.mp4)
Calibrated scale: 539.8 ppm (832x480 letterboxed GAUGE ball drops, 24 fps).
"""
import subprocess, sys, os, json
from statistics import mean, stdev

FIRSTFALL_PY = "/home/nail/swarm-work/agy-3/cosmos-swarm/tools/realball/firstfall.py"
CLIPS_DIR = "/home/nail/swarm-work/raj-3/brev_box/out"
OUT_DIR = "/home/nail/swarm-work/agy-3/cosmos-swarm/work/agy-3/task73_rog_challenge_response"

clips = {}
for cond in ["ctrl", "mid"]:
    for b in [1, 2]:
        for s in [1, 2, 3, 4]:
            name = f"box_{cond}_b{b}_noneg_s{s}"
            mp4_path = os.path.join(CLIPS_DIR, f"{name}.mp4")
            clips[name] = {
                "condition": "baseline_held" if cond == "ctrl" else "recipe_midfall",
                "ball": b,
                "seed": s,
                "path": mp4_path
            }

results = {}
for name, meta in clips.items():
    print(f"--> Running firstfall.py on {name}...", flush=True)
    cmd = [
        "python3", "-I", FIRSTFALL_PY,
        meta["path"],
        "--fps", "24",
        "--ppm", "539.8"
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # parse JSON from stdout
    stdout = proc.stdout.strip()
    # finding first '{'
    idx = stdout.find('{')
    if idx != -1:
        json_str = stdout[idx:]
        try:
            data = json.load(open(stdout[idx:], 'r') if False else json_str) if False else json.loads(json_str)
        except Exception as e:
            data = {"error": f"JSON parse error: {e}", "raw": stdout}
    else:
        data = {"error": "no json found", "raw": stdout, "stderr": proc.stderr}
    
    results[name] = {**meta, "firstfall_output": data}
    flag = data.get("flag", "unknown")
    g = data.get("g")
    g_hT = data.get("g_from_h_T")
    print(f"    Result {name}: flag={flag}, g={g}, g_from_h_T={g_hT}", flush=True)

out_file = os.path.join(OUT_DIR, "firstfall_16clips_results.json")
with open(out_file, "w") as f:
    json.dump(results, f, indent=2)

print(f"\nAll 16 clips processed. Saved to {out_file}", flush=True)

# Analysis & summary
print("\n=== SUMMARY STATISTICS ===")
for cond in ["baseline_held", "recipe_midfall"]:
    cond_clips = [v for v in results.values() if v["condition"] == cond]
    valid_g = [v["firstfall_output"]["g"] for v in cond_clips if "g" in v["firstfall_output"] and v["firstfall_output"]["g"] is not None]
    valid_g_hT = [v["firstfall_output"]["g_from_h_T"] for v in cond_clips if "g_from_h_T" in v["firstfall_output"] and v["firstfall_output"]["g_from_h_T"] is not None]
    flags = [v["firstfall_output"].get("flag", "lost") for v in cond_clips]
    print(f"Condition: {cond}")
    print(f"  Total clips: {len(cond_clips)}")
    print(f"  Flags: {flags}")
    if valid_g:
        m_g = mean(valid_g)
        se_g = stdev(valid_g) / (len(valid_g)**0.5) if len(valid_g) > 1 else 0.0
        m_hT = mean(valid_g_hT)
        se_hT = stdev(valid_g_hT) / (len(valid_g_hT)**0.5) if len(valid_g_hT) > 1 else 0.0
        print(f"  Valid g fits (n={len(valid_g)}): mean g = {m_g:.3f} +- {se_g:.3f} m/s^2 (individual: {[round(x, 2) for x in valid_g]})")
        print(f"  g_from_h_T (n={len(valid_g_hT)}): mean = {m_hT:.3f} +- {se_hT:.3f} m/s^2 (individual: {[round(x, 2) for x in valid_g_hT]})")
    else:
        print(f"  Valid g fits: 0 (all lost/held/no free fall)")
