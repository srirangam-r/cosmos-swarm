#!/usr/bin/env python3
"""Task 337 arm C (dk2): Time-to-Move DUAL CLOCK with a real weak clock (arXiv 2511.08633 Sec.3, Table 3 (t_weak, t_strong)).
Contrast to dk1 t336b inj19 (start_step 0 = TTM's (T, t_strong) row, which TTM says "often produces duplicate copies"):
here the WHOLE frame starts from the Nano-Phys proxy noised to sigma[KW] (KW=10: 0.979, KW=14: 0.959), so the background
carries the proxy still's coarse signal ("nothing swings here"; signal-leak fix, arXiv 2309.15842) but has 21-25 steps to
build texture; inside dk1's box the predicted x0 is replaced by the proxy latent for steps [KW, 19), then free (release at
the old Nano-Phys sigma 0.898). Everything else (prompt, proxies, boxes, seeds, settings, CPU noise) = t336b.
Derived from dk1's build_jobs_b.py @dc1a6f7 (docstring below).
Task 336b (dk1): DUAL-CLOCK variant (Time-to-Move 2511.08633; server latent.x0_inject = PhyRPR 2601.09255 latent fusion).
Why: t336 region-band fill at sigma 0.898 turned the whole background into a flat wall (peek_real12_reg_regsfr_s1.jpg).
Here the background runs the full plain schedule from step 0; inside box B the predicted clean video is replaced by the proxy latent
for steps [0, K) (K=19: release at the old Nano-Phys start sigma 0.898; K=27: sigma 0.573), then sampling is free.
Arms: inj19, inj27 (seeds 1-3), inj19_x17, inj27_x17 (seed 1). Same scenes, boxes (boxes.json), proxies, prompt, settings.
Original t336 docstring follows.
Task 336 (dk1): does ProxyUp region-wise latent noising (+SFR) remove Nano-Phys's DOVER cost (#6690)
while keeping period transfer? FROZEN before any clip (see README.md prereg).

Contract = work/dk2/t276/build_jobs.py @a33fc5a (prompt, proxy.py defaults: release_from_rest, A=|theta0|,
k19 sigma 0.89844, 93 f @ 24 fps, 832x480, 35 steps, CFG 6, CPU noise, latent.ref noised), proxies
regenerated with the same call (tools/nano_phys unchanged since a33fc5a). Scenes: real_12/17/18/19 (t276 nphys 12/12
clean). Only the latent spec changes:
  reg      latent.band = {band: region, box: B}  (proxy latent inside B, variance-matched fresh noise outside;
           ProxyUp region-wise latent noising, arXiv 2607.03732)
  regsfr   reg + latent.sfr = 15, sfr_guidance = 3.0 (ProxyUp defaults)
  *_x17    same with the 1.7 x P_real proxy (wrong-period control), seed 1 only
Box B per scene: pixels whose max over time |proxy_t - proxy_0| > 30 grey levels (either period proxy) plus the
pivot and bob points, dilated by 32 px, bounding rectangle, as fractions of 832x480.
usage (repo root): python3 work/dk1/t336_region/build_jobs.py -> jobs.jsonl, boxes.json
"""
import json, sys
from pathlib import Path
import numpy as np, cv2
H = Path(__file__).resolve().parent; R = H.parents[2]
P336 = R / "work/dk1/t336_region"  # dk1 proxies + boxes, read-only (same box/proxy as t336b inj19)
sys.path.insert(0, str(R))
from tools.nano_phys.proxy import generate_pendulum_proxy
from tools.nano_phys.runner import sigma_to_step

T276 = R / "work/dk2/t276"
PROMPT = json.loads(open(T276 / "jobs_plain.jsonl").readline())["prompt"]
SCENES = ("real_12", "real_17", "real_18", "real_19")
W, Hh, DIL, THR = 832, 480, 32, 30


def frames(p):
    cap = cv2.VideoCapture(str(p)); out = []
    while True:
        ok, f = cap.read()
        if not ok: break
        out.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.int16))
    return np.stack(out)


def box_for(proxies, pivot, bob):
    m = np.zeros((Hh, W), bool)
    for p in proxies:
        F = frames(p)
        m |= np.abs(F - F[0]).max(0) > THR
    for x, y in (pivot, bob):
        m[y, x] = True
    m = cv2.dilate(m.astype(np.uint8), np.ones((2 * DIL + 1, 2 * DIL + 1), np.uint8)) > 0
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return [round(x0 / W, 4), round(y0 / Hh, 4), round(x1 / W, 4), round(y1 / Hh, 4)], int(m.sum())


def main():
    k = sigma_to_step(0.90, steps=35); assert k == 19, k
    fr = {f["id"]: f for f in json.load(open(T276 / "frames.json"))}
    jobs, boxes = [], {}
    
    for fid in SCENES:
        f = fr[fid]; img = T276 / f["image"]
        pp = {}
        for arm, P in (("nphys", float(f["P_real_s"])), ("nphys_x17", round(float(f["P_real_s"]) * 1.7, 5))):
            pp[arm] = P336 / "proxies" / f"proxy_{fid}_{arm}.mp4"
            if not pp[arm].exists():
                generate_pendulum_proxy(image_path=img, out_path=pp[arm], pivot=tuple(f["pivot"]), bob=tuple(f["bob"]),
                                        period=P, num_frames=93, fps=24, width=W, height=Hh)
        box, npx = box_for(pp.values(), f["pivot"], f["bob"])
        boxes[fid] = dict(box=box, moving_px_dilated=npx, area_frac=round((box[2] - box[0]) * (box[3] - box[1]), 4))
        base = dict(prompt=PROMPT, negative_prompt=None, image=str(img.relative_to(R)), width=W, height=Hh,
                    num_frames=93, fps=24, steps=35, guidance=6.0, flow_shift=10.0)
        for arm, seeds in (("dc10", (1, 2, 3)), ("dc14", (1, 2, 3)), ("dc10_x17", (1,)), ("dc14_x17", (1,))):
            prox = pp["nphys_x17" if arm.endswith("x17") else "nphys"]
            KW = int(arm[2:4])  # weak clock: whole frame starts from the proxy noised to sigma[KW]
            lat = {"ref": prox.name, "start_step": KW, "init": "noised", "x0_inject": {"steps": [KW, 19], "box": box}}
            for s in seeds:
                jobs.append(dict(name=f"t337c_{fid}_{arm}_s{s}", **base, seed=s, files=[str(prox.relative_to(R))],
                                 extra_params={"client": "nano_phys", "noise": {"device": "cpu"}, "latent": lat}))
    with open(H / "jobs.jsonl", "w") as fh:
        for j in jobs: fh.write(json.dumps(j) + "\n")
    assert boxes == json.load(open(P336 / "boxes.json")), "boxes changed"
    print(len(jobs), "jobs"); print(json.dumps(boxes, indent=1))


if __name__ == "__main__":
    main()
