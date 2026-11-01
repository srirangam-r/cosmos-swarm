"""E7 (Raj via Claude), frozen before any E7 clip exists. WHY does E6's temporal_low transplant make Nano swing cleanly
(64/64 pend_acf 'ok' vs 10/60 plain), and where is the clock? E6-W: the tlo band (temporal bins |k|<=3 of 24) does NOT carry
the donor's clock (f=0.03), the full donor noise does (f=1.07). All start noises are built here (numpy) and uploaded as
latent.start_file (x_start, used as is; latent frame 0 stays the conditioning frame). Same request as E6 stage C otherwise
(GAUGE pendulum prompt, 832x480, 93 f @ 24 fps, 35 steps, CFG 6, noise.device cpu). Targets t1-8 (E6 first frames), fill
seeds 1,2 (numpy default_rng(s), the SAME fresh noise for every arm -> paired). Donor = E6's k=0 donor (t1-8 -> d2,5,8,11,14,17,20,3).
Arms (16 clips each):
  up_fresh        fresh noise, uploaded unchanged (control for the upload path)
  damp_a{90,70,40,0}  fresh noise with its slow band (|k|<=3) scaled by a (energy hypothesis; inverted tlo std is ~0.92x white)
  tlo_phrand      donor's slow-band MAGNITUDE with the fresh noise's phase (+ fresh elsewhere): magnitude vs phase
  tlo_shuf        donor's slow band with (h,w) positions permuted (same perm for all c,t) (+ fresh elsewhere): spatial alignment
  osc_C / osc_W   bins 3<=|k|<=6 from the donor / from the 10/7-sped-up donor (E6-W WA_recDD) (+ fresh elsewhere): clock band
  low_C / low_W   bins |k|<=6 from the donor / sped-up donor (+ fresh elsewhere)
"""
import io, json, os, subprocess, threading, time, traceback, queue as Q
from pathlib import Path
import numpy as np

ROOT = Path(__file__).parent; OUT = ROOT / "out"; NZ = ROOT / "npz"; OUT.mkdir(exist_ok=True); NZ.mkdir(exist_ok=True)
E6 = Path(os.environ.get("E6_DIR", str(Path.home() / "e6")))
E6W = Path(os.environ.get("E6W_DIR", str(Path.home() / "swarm/internals/cosmos-swarm/work/dk2/e6w")))
PROMPT = (E6 / "pend_base.txt").read_text().strip()
EPS = [u.rstrip("/") for u in os.environ.get("E7_ENDPOINTS", ",".join(f"http://127.0.0.1:{p}" for p in range(8041, 8049))).split(",") if u]
TARGETS = list(range(1, 9)); SEEDS = [1, 2]
DONOR = {1: 2, 2: 5, 3: 8, 4: 11, 5: 14, 6: 17, 7: 20, 8: 3}
LOG = open(ROOT / "driver.log", "a", buffering=1)
def log(*a): print(time.strftime("%H:%M:%S"), *a, file=LOG, flush=True)

def load(p):
    z = np.load(p); return np.asarray(z["x_inverted"] if "x_inverted" in z.files else z["x_start"], dtype=np.float64)

def kbins(T): return np.abs(np.fft.fftfreq(T) * T)

def tmask(T, kmin, kmax):
    k = kbins(T); return ((k >= kmin - 1e-9) & (k <= kmax + 1e-9)).astype(float).reshape(1, 1, T, 1, 1)

def mixT(donor, fresh, kmin, kmax):
    M = tmask(fresh.shape[2], kmin, kmax)
    return np.fft.ifft(M * np.fft.fft(donor, axis=2) + (1 - M) * np.fft.fft(fresh, axis=2), axis=2).real

def damp(fresh, a):
    M = tmask(fresh.shape[2], 0, 3); return np.fft.ifft((1 - M + a * M) * np.fft.fft(fresh, axis=2), axis=2).real

def phrand(donor, fresh):
    M = tmask(fresh.shape[2], 0, 3); Fd, Ff = np.fft.fft(donor, axis=2), np.fft.fft(fresh, axis=2)
    band = np.abs(Fd) * np.exp(1j * np.angle(Ff))
    return np.fft.ifft(M * band + (1 - M) * Ff, axis=2).real

def shuf(donor, fresh, s):
    M = tmask(fresh.shape[2], 0, 3); bd = np.fft.ifft(M * np.fft.fft(donor, axis=2), axis=2).real
    _, C, T, H, W = bd.shape; perm = np.random.default_rng(100 + s).permutation(H * W)
    bd = bd.reshape(1, C, T, H * W)[..., perm].reshape(1, C, T, H, W)
    return bd + np.fft.ifft((1 - M) * np.fft.fft(fresh, axis=2), axis=2).real

def build(arm, t, s):
    p = NZ / f"{arm}_t{t:02}_s{s}.npz"
    if p.exists(): return p
    d = DONOR[t]; dC = load(E6 / "out" / f"A_rec{d:02}.npz"); shape = dC.shape
    fresh = np.random.default_rng(s).standard_normal(shape)
    if arm == "up_fresh": x = fresh
    elif arm.startswith("damp_a"): x = damp(fresh, int(arm[6:]) / 100)
    elif arm == "tlo_phrand": x = phrand(dC, fresh)
    elif arm == "tlo_shuf": x = shuf(dC, fresh, s)
    else:
        donor = dC if arm.endswith("_C") else load(E6W / "out" / f"WA_rec{d:02}.npz")
        x = mixT(donor, fresh, 3, 6) if arm.startswith("osc") else mixT(donor, fresh, 0, 6)
    np.savez(p, x_start=x.astype(np.float32)); return p

ARMS = ["up_fresh", "damp_a90", "damp_a70", "damp_a40", "damp_a0", "tlo_phrand", "tlo_shuf", "osc_C", "osc_W", "low_C", "low_W"]

def post(url, name, image, npz, seed):
    mp4 = OUT / f"{name}.mp4"
    if mp4.exists() and mp4.stat().st_size > 1000: return True
    hdr = OUT / f"{name}.headers"
    extra = {"noise": {"device": "cpu"}, "latent": {"start_file": npz.name}}
    cmd = ["curl", "-s", "-o", str(mp4), "-D", str(hdr), "-w", "%{http_code}", "--max-time", "3000", "-X", "POST",
           f"{url}/v1/videos/sync", "-F", f"prompt={PROMPT}", "-F", "num_frames=93", "-F", "fps=24",
           "-F", "num_inference_steps=35", "-F", "guidance_scale=6", "-F", f"seed={seed}",
           "-F", f"input_reference=@{image}", "-F", f"extra_params={json.dumps(extra)}", "-F", f"internals_files=@{npz}"]
    code = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
    if code != "200":
        log("FAIL", name, url, code, mp4.read_text()[:300] if mp4.exists() else ""); mp4.unlink(missing_ok=True); return False
    cid = [l.split(":", 1)[1].strip() for l in hdr.read_text().splitlines() if l.lower().startswith("x-clip-id")]
    if cid: subprocess.run(["curl", "-s", "-o", str(OUT / f"{name}.server.json"), f"{url}/v1/sidecars/{cid[0]}"])
    log("done", name, url); return True

def main():
    jobs = [dict(name=f"{a}_t{t:02}_s{s}", t=t, s=s, arm=a) for s in SEEDS for a in ARMS for t in TARGETS]
    log("E7 start", len(jobs), "jobs on", EPS)
    q = Q.Queue(); [q.put(j) for j in jobs]
    def worker(url):
        while True:
            try: j = q.get_nowait()
            except Q.Empty: return
            for attempt in range(3):
                try:
                    npz = build(j["arm"], j["t"], j["s"])
                    if post(url, j["name"], E6 / "out" / f"f0_{j['t']:02}.png", npz, j["s"]): break
                except Exception: log("EXC", j["name"], traceback.format_exc()[-300:])
                time.sleep(20)
    ts = [threading.Thread(target=worker, args=(u,)) for u in EPS]; [t.start() for t in ts]; [t.join() for t in ts]
    log("generation finished; analysing")
    subprocess.run([str(Path(os.sys.executable)), "-I", str(ROOT / "analyze_e7.py")], stdout=open(ROOT / "analyze.log", "w"), stderr=subprocess.STDOUT)
    log("E7 done")

if __name__ == "__main__":
    main()
