"""E6 (task 250): does the coarse noise of inverted REAL pendulum recordings give Nano the real clock on new frames?

Unattended driver (Raj via Claude). Calls the endpoints in E6_ENDPOINTS directly (the queue can't upload reference files
yet). Run: E6_ENDPOINTS=http://host:port,... python3 run_e6.py   (results in out/, report.md at the end)
Stages, all CPU-drawn noise, the GAUGE pendulum base prompt, 832x480, 93 f @ 24 fps, 35 steps, CFG 6:
  A  bank:      invert each real continuation (codex-api-4 t8 real_XX.mp4, frames [93:186) after de-dup) with its own
                first frame, midpoint solver, 2 substeps; regenerate from the inverted noise (reconstruction test);
                keep x_inverted.
  B  baseline:  plain Nano from each recording's first frame, seeds 1-3 (Nano's own clock from that frame).
  C  transfer:  for 8 target recordings x 4 donor recordings: start from a band of the DONOR's inverted noise plus fresh
                fill noise, conditioned on the TARGET frame. Arms: tlo (temporal_low cut .25) and slo (spatial_low cut .25),
                fill seeds 1 and 2; 'all' (the donor's full noise, a copy control).
Analysis (fixed now, run at the end): tools/pend_acf period (frames, skip 8) on every clip and on the real clips;
ratio to the target's real period; trajectory-copy index (motion-course correlation with the donor's real clip vs the
target's real continuation). Writes report.json / report.md. Posts nothing to the board.
"""
import json, os, subprocess, sys, threading, time, queue as Q, traceback
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "out"; OUT.mkdir(exist_ok=True)
REAL = Path.home() / "swarm/internals/cosmos-swarm/work/codex-api-4/t8/output/clips"
PROMPT = (Path(__file__).parent / "pend_base.txt").read_text().strip()
# Endpoints running tools/cosmos_local/server.py with features 'latent' and 'noise' (see /health), comma-separated URLs.
ENDPOINTS = [u.rstrip("/") for u in os.environ.get("E6_ENDPOINTS", "http://100.111.167.68:8011").split(",") if u]
REAL = Path(os.environ.get("E6_REAL_CLIPS", str(REAL)))
RECS = [i for i in range(1, 21) if (REAL / f"real_{i:02}.mp4").exists()]
TARGETS = RECS[:8]
LOG = open(ROOT / "driver.log", "a", buffering=1)


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, file=LOG, flush=True)


def first_frame(i):
    p = OUT / f"f0_{i:02}.png"
    if not p.exists():
        import cv2
        cap = cv2.VideoCapture(str(REAL / f"real_{i:02}.mp4")); ok, f = cap.read(); cap.release()
        cv2.imwrite(str(p), f)
    return p


def post(url, name, image, extra, files=(), seed=1):
    mp4 = OUT / f"{name}.mp4"
    if mp4.exists() and mp4.stat().st_size > 1000:
        return True
    hdr = OUT / f"{name}.headers"
    cmd = ["curl", "-s", "-o", str(mp4), "-D", str(hdr), "-w", "%{http_code}", "--max-time", "3000", "-X", "POST",
           f"{url}/v1/videos/sync", "-F", f"prompt={PROMPT}", "-F", "num_frames=93", "-F", "fps=24",
           "-F", "num_inference_steps=35", "-F", "guidance_scale=6", "-F", f"seed={seed}",
           "-F", f"input_reference=@{image}", "-F", f"extra_params={json.dumps(extra)}"]
    for f in files:
        cmd += ["-F", f"internals_files=@{f}"]
    code = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    if code != "200":
        log("FAIL", name, url, code, mp4.read_text()[:300] if mp4.exists() else "")
        mp4.unlink(missing_ok=True)
        return False
    aids = [l.split(":", 1)[1].strip() for l in hdr.read_text().splitlines() if l.lower().startswith("x-artifact-ids")]
    for aid in (aids[0].split(",") if aids else []):
        subprocess.run(["curl", "-s", "-o", str(OUT / f"{name}.npz"), f"{url}/v1/artifacts/{aid}"])
    cid = [l.split(":", 1)[1].strip() for l in hdr.read_text().splitlines() if l.lower().startswith("x-clip-id")]
    if cid:
        subprocess.run(["curl", "-s", "-o", str(OUT / f"{name}.server.json"), f"{url}/v1/sidecars/{cid[0]}"])
    log("done", name, url)
    return True


def run_stage(jobs):
    q = Q.Queue()
    for j in jobs:
        q.put(j)
    def worker(port):
        while True:
            try:
                j = q.get_nowait()
            except Q.Empty:
                return
            for attempt in range(3):
                try:
                    if post(port, **j):
                        break
                except Exception:
                    log("EXC", j["name"], traceback.format_exc()[-300:])
                time.sleep(20)
    ts = [threading.Thread(target=worker, args=(u,)) for u in ENDPOINTS]
    [t.start() for t in ts]; [t.join() for t in ts]


def main():
    log("E6 start", "recordings", RECS, "targets", TARGETS)
    cpu = {"device": "cpu"}
    # A: bank + reconstruction
    run_stage([dict(name=f"A_rec{i:02}", image=first_frame(i), files=[REAL / f"real_{i:02}.mp4"],
                    extra={"noise": cpu, "latent": {"ref": f"real_{i:02}.mp4", "init": "inverted", "start_step": 0,
                                                    "invert_substeps": 2, "return": ["x_inverted"]}}) for i in RECS])
    # B: baselines
    run_stage([dict(name=f"B_rec{i:02}_s{s}", image=first_frame(i), seed=s, extra={"noise": cpu})
               for i in RECS for s in (1, 2, 3)])
    # C: transfer
    jobs = []
    for t in TARGETS:
        donors = [d for d in RECS if d != t][:]
        donors = [donors[(TARGETS.index(t) * 3 + k) % len(donors)] for k in range(4)]
        for d in donors:
            inv = OUT / f"A_rec{d:02}.npz"
            if not inv.exists():
                continue
            for band, tag in (({"band": "temporal_low", "cut": 0.25}, "tlo"), ({"band": "spatial_low", "cut": 0.25}, "slo")):
                for s in (1, 2):
                    jobs.append(dict(name=f"C_t{t:02}_d{d:02}_{tag}_s{s}", image=first_frame(t), seed=s, files=[inv],
                                     extra={"noise": cpu, "latent": {"start_file": inv.name, "band": band}}))
            jobs.append(dict(name=f"C_t{t:02}_d{d:02}_all_s1", image=first_frame(t), seed=1, files=[inv],
                             extra={"noise": cpu, "latent": {"start_file": inv.name}}))
    run_stage(jobs)
    log("generation finished; analysing")
    subprocess.run([str(Path.home() / "swarm-work/raj-1/venv312/bin/python"), "-I", str(ROOT / "analyze_e6.py")],
                   stdout=open(ROOT / "analyze.log", "w"), stderr=subprocess.STDOUT)
    log("E6 done")


if __name__ == "__main__":
    main()
