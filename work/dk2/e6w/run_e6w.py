"""E6-W (dk2, add-on to task 258/E6, frozen before any W clip exists): WRONG-PERIOD DONOR control.
Why: the 20 real GAUGE continuations all have the same period (29.15-29.87 frames), so in E6 stage C a clip that takes the
'real' period cannot be told apart from one that copies the DONOR's frequency out of the transplanted band. Here the donor
is the same recording sped up by 10/7 (realw_XX.mp4, build_warp.py; pend_acf 20.2-20.7 f). Everything else is identical to
E6 stage C (Raj's run_e6.py @76d9e51): same request fields, prompt, 93 f @ 24 fps, 832x480, 35 steps, CFG 6, CPU noise,
same target frames, same donor recording per target (E6's k=0 donor), same fill seeds 1-2, band temporal_low cut .25.
Stages:  WA  invert each warped donor with its own first frame (midpoint, 2 substeps), regenerate (reconstruction check)
         WC  8 targets x 1 warped donor: tlo s1, s2 and 'all' s1  (pairs with E6's C_tTT_dDD_{tlo_s1,tlo_s2,all_s1})
Run on the box: E6W_ENDPOINT=http://127.0.0.1:8011 python run_e6w.py   (outputs in ./out, driver.log)
"""
import json, os, subprocess, time, traceback
from pathlib import Path

ROOT = Path(__file__).parent; OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)
CLIPS = ROOT / "clips"
E6 = Path.home() / "swarm/internals/cosmos-swarm/work/raj-noise/e6"
PROMPT = (E6 / "pend_base.txt").read_text().strip()
URL = os.environ.get("E6W_ENDPOINT", "http://127.0.0.1:8011").rstrip("/")
TARGETS = list(range(1, 9))
RECS = list(range(1, 21))
LOG = open(ROOT / "driver.log", "a", buffering=1)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, file=LOG, flush=True)


def k0_donor(t):  # E6 stage C donor mapping, k = 0
    donors = [d for d in RECS if d != t]
    return donors[(TARGETS.index(t) * 3) % len(donors)]


def first_frame(src, name):
    p = OUT / f"{name}.png"
    if not p.exists():
        import cv2
        cap = cv2.VideoCapture(str(src)); ok, f = cap.read(); cap.release(); cv2.imwrite(str(p), f)
    return p


def post(name, image, extra, files=(), seed=1):  # same request as run_e6.post
    mp4 = OUT / f"{name}.mp4"
    if mp4.exists() and mp4.stat().st_size > 1000:
        return True
    hdr = OUT / f"{name}.headers"
    cmd = ["curl", "-s", "-o", str(mp4), "-D", str(hdr), "-w", "%{http_code}", "--max-time", "3000", "-X", "POST",
           f"{URL}/v1/videos/sync", "-F", f"prompt={PROMPT}", "-F", "num_frames=93", "-F", "fps=24",
           "-F", "num_inference_steps=35", "-F", "guidance_scale=6", "-F", f"seed={seed}",
           "-F", f"input_reference=@{image}", "-F", f"extra_params={json.dumps(extra)}"]
    for f in files:
        cmd += ["-F", f"internals_files=@{f}"]
    code = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    if code != "200":
        log("FAIL", name, code, mp4.read_text()[:300] if mp4.exists() else ""); mp4.unlink(missing_ok=True); return False
    H = hdr.read_text().splitlines()
    aids = [l.split(":", 1)[1].strip() for l in H if l.lower().startswith("x-artifact-ids")]
    for aid in (aids[0].split(",") if aids else []):
        subprocess.run(["curl", "-s", "-o", str(OUT / f"{name}.npz"), f"{URL}/v1/artifacts/{aid}"])
    cid = [l.split(":", 1)[1].strip() for l in H if l.lower().startswith("x-clip-id")]
    if cid:
        subprocess.run(["curl", "-s", "-o", str(OUT / f"{name}.server.json"), f"{URL}/v1/sidecars/{cid[0]}"])
    (OUT / f"{name}.job.json").write_text(json.dumps(dict(prompt=PROMPT, image=str(image), seed=seed, extra=extra,
        files=[str(f) for f in files], num_frames=93, fps=24, steps=35, cfg=6, size="832x480", url=URL), indent=1))
    log("done", name); return True


def run(jobs):
    for j in jobs:
        for attempt in range(3):
            try:
                if post(**j): break
            except Exception:
                log("EXC", j["name"], traceback.format_exc()[-300:])
            time.sleep(20)


def main():
    cpu = {"device": "cpu"}
    pairs = [(t, k0_donor(t)) for t in TARGETS]
    log("E6W start", "pairs", pairs)
    donors = sorted({d for _, d in pairs})
    run([dict(name=f"WA_rec{d:02}", image=first_frame(CLIPS / f"realw_{d:02}.mp4", f"f0w_{d:02}"),
              files=[CLIPS / f"realw_{d:02}.mp4"],
              extra={"noise": cpu, "latent": {"ref": f"realw_{d:02}.mp4", "init": "inverted", "start_step": 0,
                                              "invert_substeps": 2, "return": ["x_inverted"]}}) for d in donors])
    jobs = []
    for t, d in pairs:
        inv = OUT / f"WA_rec{d:02}.npz"
        if not inv.exists():
            log("MISSING", inv); continue
        img = E6 / "out" / f"f0_{t:02}.png"
        for s in (1, 2):
            jobs.append(dict(name=f"W_t{t:02}_d{d:02}_tlo_s{s}", image=img, seed=s, files=[inv],
                             extra={"noise": cpu, "latent": {"start_file": inv.name,
                                                             "band": {"band": "temporal_low", "cut": 0.25}}}))
        jobs.append(dict(name=f"W_t{t:02}_d{d:02}_all_s1", image=img, seed=1, files=[inv],
                         extra={"noise": cpu, "latent": {"start_file": inv.name}}))
    run(jobs)
    log("E6W generation finished")


if __name__ == "__main__":
    main()
