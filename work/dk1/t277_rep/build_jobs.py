#!/usr/bin/env python3
"""Task 277 executed as a fresh-scene, fresh-seed replication of finding #6239 (task 276), by dk1.
FROZEN before any clip. Same contract as work/dk2/t276/build_jobs.py @a33fc5a (prompt, proxy builder defaults,
sigma 0.90 -> k19, 93 f @ 24 fps, 832x480, 35 steps, CFG 6, CPU noise, latent.ref noised); only changes:
  scenes  = real_06, real_14 (ro-sol1 t292 pinned inputs, container frame 186; not used in 276/265/E6)
  seeds   = 101, 102, 103 for ALL three arms (276 had x17 at seed 1 only; codex-1 #6454 asked for 3 seeds)
  P_real  = codex-api-4 t8 table.csv tool_period_s (measure_pend v1 on the real clip), see frames.json
Arms: plain (no proxy), nphys (P = P_real), nphys_x17 (P = 1.7 P_real, wrong-physics control). 18 jobs.
usage: python3 work/dk1/t277_rep/build_jobs.py   (from repo root) -> jobs.jsonl (paths relative to repo root)
"""
import json, sys
from pathlib import Path
H = Path(__file__).resolve().parent; R = H.parents[2]
sys.path.insert(0, str(R))
from tools.nano_phys.proxy import generate_pendulum_proxy
from tools.nano_phys.runner import sigma_to_step

PROMPT = open(R / "work/dk2/t276/jobs_plain.jsonl").readline()
PROMPT = json.loads(PROMPT)["prompt"]  # byte-identical to t276
SEEDS = (101, 102, 103)

def main():
    k = sigma_to_step(0.90, steps=35); assert k == 19, k
    jobs = []
    for f in json.load(open(H / "frames.json")):
        fid, img = f["id"], H / f["image"]
        base = dict(prompt=PROMPT, negative_prompt=None, image=str(img.relative_to(R)), width=832, height=480,
                    num_frames=93, fps=24, steps=35, guidance=6.0, flow_shift=10.0)
        for arm, P in (("nphys", f["P_real_s"]), ("nphys_x17", round(1.7 * f["P_real_s"], 5))):
            pp = H / "proxies" / f"proxy_{fid}_{arm}.mp4"
            if not pp.exists():
                generate_pendulum_proxy(image_path=img, out_path=pp, pivot=tuple(f["pivot"]), bob=tuple(f["bob"]),
                                        period=P, num_frames=93, fps=24, width=832, height=480)
        for s in SEEDS:
            jobs.append(dict(name=f"t277r_{fid}_plain_s{s}", **base, seed=s, extra_params={"noise": {"device": "cpu"}}))
            for arm in ("nphys", "nphys_x17"):
                pp = H / "proxies" / f"proxy_{fid}_{arm}.mp4"
                jobs.append(dict(name=f"t277r_{fid}_{arm}_s{s}", **base, seed=s, files=[str(pp.relative_to(R))],
                                 extra_params={"client": "nano_phys", "noise": {"device": "cpu"},
                                               "latent": {"ref": pp.name, "start_step": k, "init": "noised"}}))
    with open(H / "jobs.jsonl", "w") as fh:
        for j in jobs: fh.write(json.dumps(j) + "\n")
    print(len(jobs), "jobs")

if __name__ == "__main__":
    main()
