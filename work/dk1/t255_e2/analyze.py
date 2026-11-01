"""Task 255 E2 analysis -- FROZEN before any E2 clip is generated or fetched.

Usage: python3 analyze.py <devset_dir> <e2_clips_dir> <e1_clips_dir or -> <out.json>
Clips: t255e2_<clip>_{own,zero}_s{1,2,3}.mp4, 17 frames 256x256 (frame 0 = model's re-rendered conditioning frame).
Real: devset <clip>/real.mp4, frames 0..16 used.

Definitions (x in [0,1] RGB, all on 256x256):
  DE(V)      = mean_{k=1..16} mean_pix |V_k - V_0|          (CoCo-style drift energy vs the clip's own frame 0;
                                                              using the generated frame 0 cancels the VAE re-render)
  mask M     = real-motion mask: pixels whose gray |R_k - R_0| > 0.08 for any k in 1..16, dilated 7x7.
               DE_in / DE_out = DE restricted to M / to ~M.  (M ~ arm + manipulated objects; ~M ~ static scene.)
  e_k(V)     = mean_pix |V_k - V_{k-1}|, k=1..16              (motion-energy time series)
  LP(A,B)    = mean over frames 1..16 of LPIPS-alex(A_k, B_k)

PRIMARY (per clip, seeds averaged): rho = DE(zero) / DE(own).
  Report median rho, clip-bootstrap 95% CI (10k), and #clips with rho < 0.5.
  Decision: "stops when told"  if CI upper < 0.5;
            "ignores stop"     if CI lower > 0.8;
            else "partial".
SECONDARY:
  S1 where the zero-action drift is: DE_in(zero) vs DE_out(zero) (paired over clips, mean +/- SE, sign count);
     DE_out(zero) vs DE_out(own) (does background drift depend on the action at all?).
  S2 does the seed carry motion when the action says stop?
     same-seed  r_same = corr(e(zero_s), e(own_s)),  LP_same = LP(zero_s, own_s)
     diff-seed  r_diff = corr(e(zero_s), e(own_s')), LP_diff = LP(zero_s, own_s'), s != s'
     per clip: r_same - r_diff and LP_diff - LP_same; mean +/- SE, sign count, sign-flip p over clips.
  S3 seed spread under each arm: D_seed(arm) = mean LP over the 3 seed pairs; ratio zero/own.
  S4 cross-stack (needs E1 dir): OWN_s here vs E1 own_s (q8, same request, CPU noise): LP and max|diff|,
     compared with D_seed(own). Tests whether noise.device=cpu pairs FD rollouts across GPU types.
  Known answers: DE(repeat real frame 0) = 0 exactly; DE(real) reported as the real-motion reference.
  Determinism: *_dup vs originals, max abs pixel diff.
"""
import itertools, json, os, sys
import av, numpy as np, torch, lpips
from scipy.ndimage import binary_dilation

dev, cdir, e1dir, outp = sys.argv[1:5]
ids = [c["id"] for c in json.load(open(os.path.join(dev, "index.json")))["clips"]]
SEEDS = [1, 2, 3]
ARMS = ("own", "zero")
net = lpips.LPIPS(net="alex", verbose=False)
rng = np.random.default_rng(0)


def load(p):
    with av.open(p) as c:
        return np.stack([f.to_ndarray(format="rgb24") for f in c.decode(video=0)]).astype(np.float32)[:17] / 255.0


def gray(v):
    return v @ np.array([0.299, 0.587, 0.114], np.float32)


def de(v, m=None):
    d = np.abs(v[1:17] - v[0:1]).mean(-1)  # T,H,W
    return float(d.mean()) if m is None else float(d[:, m].mean())


def energy(v):
    return np.abs(np.diff(v[:17], axis=0)).mean(axis=(1, 2, 3))


def lp(a, b):
    ta = torch.from_numpy(a[1:17]).permute(0, 3, 1, 2) * 2 - 1
    tb = torch.from_numpy(b[1:17]).permute(0, 3, 1, 2) * 2 - 1
    with torch.no_grad():
        return float(net(ta, tb).mean())


def boot_median(x, n=10000):
    x = np.asarray(x)
    b = np.median(x[rng.integers(0, len(x), (n, len(x)))], axis=1)
    return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]


def signflip_p(x, n=20000):
    x = np.asarray(x)
    obs = abs(x.mean())
    f = rng.choice([-1, 1], (n, len(x)))
    return float((np.abs((f * x).mean(1)) >= obs - 1e-12).mean())


def summ(x):
    x = np.asarray(x, float)
    return {"mean": float(x.mean()), "se": float(x.std(ddof=1) / np.sqrt(len(x))), "n_pos": int((x > 0).sum()),
            "n": int(len(x)), "signflip_p": signflip_p(x)}


per = {}
for cid in ids:
    try:
        X = {(a, s): load(os.path.join(cdir, f"t255e2_{cid}_{a}_s{s}.mp4")) for a in ARMS for s in SEEDS}
    except Exception as e:
        print("skip", cid, e); continue
    R = load(os.path.join(dev, cid, "real.mp4"))
    g = gray(R)
    M = binary_dilation((np.abs(g[1:17] - g[0:1]) > 0.08).any(0), np.ones((7, 7), bool))
    if M.all() or not M.any():
        M = None
    r = {"mask_frac": None if M is None else float(M.mean()), "DE_real": de(R),
         "DE_static0": de(np.repeat(R[:1], 17, 0))}
    for a in ARMS:
        r[f"DE_{a}"] = float(np.mean([de(X[a, s]) for s in SEEDS]))
        if M is not None:
            r[f"DEin_{a}"] = float(np.mean([de(X[a, s], M) for s in SEEDS]))
            r[f"DEout_{a}"] = float(np.mean([de(X[a, s], ~M) for s in SEEDS]))
        r[f"Dseed_{a}"] = float(np.mean([lp(X[a, s1], X[a, s2]) for s1, s2 in itertools.combinations(SEEDS, 2)]))
        r[f"LPreal_{a}"] = float(np.mean([lp(X[a, s], R) for s in SEEDS]))
    r["rho"] = r["DE_zero"] / max(r["DE_own"], 1e-9)
    E = {k: energy(v) for k, v in X.items()}
    rs = [np.corrcoef(E["zero", s], E["own", s])[0, 1] for s in SEEDS]
    rd = [np.corrcoef(E["zero", s], E["own", t])[0, 1] for s in SEEDS for t in SEEDS if s != t]
    ls = [lp(X["zero", s], X["own", s]) for s in SEEDS]
    ld = [lp(X["zero", s], X["own", t]) for s in SEEDS for t in SEEDS if s != t]
    r.update(r_same=float(np.mean(rs)), r_diff=float(np.mean(rd)), LP_same=float(np.mean(ls)), LP_diff=float(np.mean(ld)))
    if e1dir != "-":
        try:
            c = [(lp(X["own", s], load(os.path.join(e1dir, f"t255_{cid}_own_s{s}.mp4"))),
                  float(np.abs(X["own", s] - load(os.path.join(e1dir, f"t255_{cid}_own_s{s}.mp4"))).max() * 255)) for s in SEEDS]
            r["xstack_LP"] = float(np.mean([a for a, _ in c])); r["xstack_maxdiff"] = float(max(b for _, b in c))
        except Exception as e:
            print("xstack skip", cid, e)
    per[cid] = r
    print(cid, {k: round(v, 4) if isinstance(v, float) else v for k, v in r.items()}, flush=True)

C = list(per.values())
out = {"n_clips": len(C), "per_clip": per}
rho = [c["rho"] for c in C]
ci = boot_median(rho)
out["primary"] = {"median_rho": float(np.median(rho)), "ci95": ci, "n_rho_lt_0.5": int(sum(x < 0.5 for x in rho)),
                  "decision": "stops when told" if ci[1] < 0.5 else ("ignores stop" if ci[0] > 0.8 else "partial")}
mk = [c for c in C if "DEin_zero" in c]
out["S1"] = {"DEin_minus_DEout_zero": summ([c["DEin_zero"] - c["DEout_zero"] for c in mk]),
             "DEout_zero_minus_DEout_own": summ([c["DEout_zero"] - c["DEout_own"] for c in mk]),
             "DEin_zero_over_DEin_own_median": float(np.median([c["DEin_zero"] / c["DEin_own"] for c in mk]))}
out["S2"] = {"r_same_minus_r_diff": summ([c["r_same"] - c["r_diff"] for c in C]),
             "LP_diff_minus_LP_same": summ([c["LP_diff"] - c["LP_same"] for c in C])}
out["S3"] = {"Dseed_own": summ([c["Dseed_own"] for c in C]), "Dseed_zero": summ([c["Dseed_zero"] for c in C]),
             "median_ratio_zero_over_own": float(np.median([c["Dseed_zero"] / c["Dseed_own"] for c in C]))}
xs = [c for c in C if "xstack_LP" in c]
if xs:
    out["S4"] = {"xstack_LP": summ([c["xstack_LP"] for c in xs]),
                 "xstack_LP_over_Dseed_own_median": float(np.median([c["xstack_LP"] / c["Dseed_own"] for c in xs])),
                 "max_abs_diff_max": float(max(c["xstack_maxdiff"] for c in xs))}
out["known_answers"] = {"DE_static0_max": float(max(c["DE_static0"] for c in C)),
                        "DE_real": summ([c["DE_real"] for c in C])}
for a in ARMS:
    out[f"DE_{a}"] = summ([c[f"DE_{a}"] for c in C])
dups = {}
for a in ARMS:
    p = os.path.join(cdir, f"t255e2_{ids[0]}_{a}_s1_dup.mp4")
    if os.path.exists(p):
        dups[a] = float(np.abs(load(p) - load(os.path.join(cdir, f"t255e2_{ids[0]}_{a}_s1.mp4"))).max() * 255)
out["determinism_maxdiff"] = dups
json.dump(out, open(outp, "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "per_clip"}, indent=1))
