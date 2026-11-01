"""E7b (Raj via Claude), add-on to E7 v2, frozen before any E7b clip. E6's slo arm (donor's spatial-low band, every temporal
frequency, + fresh fine detail) gives real swings (eye check, no flicker; pend_acf/measure_pend agree on 34/39 ok clips,
median P/P_real 1.00). But every real recording has the same period, so it can't tell 'slo copies the donor's clock' from
'slo lets Nano find the right clock'. Here: slo_C = spatial band max(|fy|,|fx|) <= 0.125 cycles/latent px (noise.py's
spatial_low cut .25) from E6's k=0 donor; slo_W = the same band from the 10/7-sped-up donor (E6-W WA_recDD); the rest is the
same fresh noise (numpy default_rng(s)) as E7. Spatial-only mixing, so no frame-0 ringing. Clock: f = ln(P_W/P_C)/ln 0.7
(analyze_e7.py, pair 'slo'). Same targets, seeds, request and clean criterion as E7 v2."""
import run_e7 as E, numpy as np, threading, queue as Q, time, traceback

def sband(donor, fresh):
    H, W = fresh.shape[3], fresh.shape[4]
    fy, fx = np.abs(np.fft.fftfreq(H)).reshape(H, 1), np.abs(np.fft.fftfreq(W)).reshape(1, W)
    M = (np.maximum(fy, fx) <= 0.125 + 1e-9).astype(float)
    return np.fft.ifft2(M * np.fft.fft2(donor, axes=(3, 4)) + (1 - M) * np.fft.fft2(fresh, axes=(3, 4)), axes=(3, 4)).real

def build(arm, t, s):
    p = E.NZ / f"{arm}_t{t:02}_s{s}.npz"
    if p.exists(): return p
    d = E.DONOR[t]; fresh = np.random.default_rng(s).standard_normal(E.load(E.E6 / "out" / f"A_rec{d:02}.npz").shape)
    donor = E.load(E.E6 / "out" / f"A_rec{d:02}.npz") if arm == "slo_C" else E.load(E.E6W / "out" / f"WA_rec{d:02}.npz")
    np.savez(p, x_start=sband(donor, fresh).astype(np.float32)); return p

def main():
    jobs = [dict(name=f"{a}_t{t:02}_s{s}", t=t, s=s, arm=a) for s in E.SEEDS for a in ("slo_C", "slo_W") for t in E.TARGETS]
    E.log("E7b start", len(jobs))
    q = Q.Queue(); [q.put(j) for j in jobs]
    def worker(url):
        while True:
            try: j = q.get_nowait()
            except Q.Empty: return
            for attempt in range(3):
                try:
                    if E.post(url, j["name"], E.E6 / "out" / f"f0_{j['t']:02}.png", build(j["arm"], j["t"], j["s"]), j["s"]): break
                except Exception: E.log("EXC", j["name"], traceback.format_exc()[-300:])
                time.sleep(20)
    ts = [threading.Thread(target=worker, args=(u,)) for u in E.EPS]; [t.start() for t in ts]; [t.join() for t in ts]
    E.log("E7b generation finished")

if __name__ == "__main__":
    main()
