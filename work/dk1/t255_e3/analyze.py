"""Task 255 E3 analysis -- FROZEN before any E3 clip is generated or fetched (design: make_jobs.py).

Usage: python3 analyze.py <devset_dir> <e3_clips_dir> <out.json>
Clips: t255e3_<clip>_<arm>_s<seed>.mp4 (17 f, 256x256); optional <name>.server.json / <name>.json sidecars.
Real future: devset <clip>/real.mp4 frames 0..16. All metrics over frames 1..16, x in [0,1].

Metrics vs the real future (per clip: mean over seeds of the per-seed value):
  LP    LPIPS-alex (as E1/E2)          RMSE  root mean square pixel error     DSSIM 1 - SSIM (gray, gaussian 11/1.5)
  DE    mean |V_k - V_0| (E2), reported as DE/DE_real (motion amount; guards against fake wins by freezing or by
        over-motion)
  static floor = metrics of the real frame 0 repeated (the "nothing moves" prediction)

PRIMARY (one per guided arm A in neg1, neg3, zero1): d_A = LP(A) - LP(plain), paired by clip and seed, averaged over
  seeds per clip. Report median, clip-bootstrap 95% CI and the Bonferroni (3 arms) 98.33% CI, #clips < 0.
  Decision (98.33% CI): "improves" if upper < 0; "hurts" if lower > 0; else "no detectable change".
  An "improves" arm counts as a FIX CANDIDATE only if ALL guards hold:
    G1 RMSE and DSSIM do not get worse: median paired delta <= 0 for both;
    G2 motion amount: median |log(DE_A/DE_real)| <= median |log(DE_plain/DE_real)| + log(1.15);
    G3 the action matters at least as much: S1 dgap >= 0 (only checkable for neg3; for neg1/zero1 reported n/a).
SECONDARY:
  S1 action sensitivity, plain vs neg3 guidance:
     gap(cond) = LP(swap_cond) - LP(own_cond) per clip (cond = plain: swap vs plain; neg3: swap_neg3 vs neg3);
     dgap = gap(neg3) - gap(plain): summ + sign-flip p.  >0 = guidance makes the commanded action matter more.
     D_action(cond) = mean_s LP(own_s, swap_s); D_seed(cond) = mean LP over seed pairs of own; ratio per clip, median.
  S2 seed spread per arm (D_seed) and median ratio arm/plain.
  S3 motion amount per arm: median DE/DE_real.
  S4 ctrl (a' = a, s = 3) vs plain s1: max abs pixel diff per clip (expected 0; hook wiring control).
  S5 static floor comparison: LP(arm) - LP(static) per clip.
  Hook execution: from sidecars, count of guided steps per guided job (expected 30) and ctrl/plain have none.
"""
import itertools, json, math, os, sys
import av, numpy as np, torch, lpips
from scipy.ndimage import gaussian_filter

dev, cdir, outp = sys.argv[1:4]
ids = [c["id"] for c in json.load(open(os.path.join(dev, "index.json")))["clips"]]
SEEDS = [1, 2, 3]
ARMS = ["plain", "neg1", "neg3", "zero1", "swap", "swap_neg3"]
GUIDED = ["neg1", "neg3", "zero1"]
net = lpips.LPIPS(net="alex", verbose=False)
rng = np.random.default_rng(0)


def load(p):
    with av.open(p) as c:
        return np.stack([f.to_ndarray(format="rgb24") for f in c.decode(video=0)]).astype(np.float32)[:17] / 255.0


def gray(v):
    return v @ np.array([0.299, 0.587, 0.114], np.float32)


def de(v):
    return float(np.abs(v[1:17] - v[0:1]).mean())


def lp(a, b):
    ta = torch.from_numpy(a[1:17]).permute(0, 3, 1, 2) * 2 - 1
    tb = torch.from_numpy(b[1:17]).permute(0, 3, 1, 2) * 2 - 1
    with torch.no_grad():
        return float(net(ta, tb).mean())


def rmse(a, b):
    return float(np.sqrt(((a[1:17] - b[1:17]) ** 2).mean()))


def dssim(a, b):
    C1, C2 = 0.01 ** 2, 0.03 ** 2
    out = []
    for x, y in zip(gray(a[1:17]).astype(np.float64), gray(b[1:17]).astype(np.float64)):
        f = lambda z: gaussian_filter(z, 1.5, truncate=3.5)
        mx, my = f(x), f(y)
        sxx, syy, sxy = f(x * x) - mx * mx, f(y * y) - my * my, f(x * y) - mx * my
        s = ((2 * mx * my + C1) * (2 * sxy + C2)) / ((mx * mx + my * my + C1) * (sxx + syy + C2))
        out.append(1 - s.mean())
    return float(np.mean(out))


def boot_median(x, q=(2.5, 97.5), n=10000):
    x = np.asarray(x)
    b = np.median(x[rng.integers(0, len(x), (n, len(x)))], axis=1)
    return [float(np.percentile(b, q[0])), float(np.percentile(b, q[1]))]


def signflip_p(x, n=20000):
    x = np.asarray(x)
    obs = abs(x.mean())
    f = rng.choice([-1, 1], (n, len(x)))
    return float((np.abs((f * x).mean(1)) >= obs - 1e-12).mean())


def summ(x):
    x = np.asarray(x, float)
    return {"mean": float(x.mean()), "se": float(x.std(ddof=1) / np.sqrt(len(x))), "median": float(np.median(x)),
            "ci95_median": boot_median(x), "n_pos": int((x > 0).sum()), "n_neg": int((x < 0).sum()),
            "n": int(len(x)), "signflip_p": signflip_p(x)}


def sidecar(name):
    for suf in (".server.json", ".json"):
        p = os.path.join(cdir, name + suf)
        if os.path.exists(p):
            try:
                d = json.load(open(p))
            except Exception:
                continue
            # AMENDMENT 1 (post-run bug fix, no statistic changed): the server sidecar's "server" key is a str label,
            # so the old fallback crashed on unguided arms (no action_cfg key). Only dict values are searched now.
            srv = d.get("server") if isinstance(d, dict) else None
            a = (d.get("action_cfg") or (srv.get("action_cfg") if isinstance(srv, dict) else None)) if isinstance(d, dict) else None
            if a is not None:
                return a
    return None


per, hook = {}, {"guided_steps_counts": {}, "unexpected": []}
for cid in ids:
    try:
        X = {(a, s): load(os.path.join(cdir, f"t255e3_{cid}_{a}_s{s}.mp4")) for a in ARMS for s in SEEDS}
    except Exception as e:
        print("skip", cid, e); continue
    R = load(os.path.join(dev, cid, "real.mp4"))
    st = np.repeat(R[:1], 17, 0)
    r = {"DE_real": de(R), "LP_static": lp(st, R), "RMSE_static": rmse(st, R), "DSSIM_static": dssim(st, R)}
    for a in ARMS:
        r[f"LP_{a}"] = [lp(X[a, s], R) for s in SEEDS]
        r[f"RMSE_{a}"] = [rmse(X[a, s], R) for s in SEEDS]
        r[f"DSSIM_{a}"] = [dssim(X[a, s], R) for s in SEEDS]
        r[f"DE_{a}"] = float(np.mean([de(X[a, s]) for s in SEEDS]))
        r[f"Dseed_{a}"] = float(np.mean([lp(X[a, s1], X[a, s2]) for s1, s2 in itertools.combinations(SEEDS, 2)]))
    for own, sw in (("plain", "swap"), ("neg3", "swap_neg3")):
        r[f"Daction_{own}"] = float(np.mean([lp(X[own, s], X[sw, s]) for s in SEEDS]))
    cp = os.path.join(cdir, f"t255e3_{cid}_ctrl_s1.mp4")
    r["ctrl_maxdiff"] = float(np.abs(load(cp) - X["plain", 1]).max() * 255) if os.path.exists(cp) else None
    for a in ARMS + ["ctrl"]:
        for s in (SEEDS if a != "ctrl" else [1]):
            sc = sidecar(f"t255e3_{cid}_{a}_s{s}")
            if sc is None:
                continue
            n = len(sc.get("guided_steps", []))
            hook["guided_steps_counts"].setdefault(a, []).append(n)
            if (a in GUIDED + ["swap_neg3", "ctrl"]) != (n > 0):
                hook["unexpected"].append(f"{cid}/{a}/s{s}: guided_steps={n}")
    per[cid] = r
    print(cid, round(float(np.mean(r["LP_plain"])), 4), {a: round(float(np.mean(r[f"LP_{a}"])), 4) for a in GUIDED},
          flush=True)

C = list(per.values())
m = lambda c, k: float(np.mean(c[k]))
out = {"n_clips": len(C), "per_clip": per}
prim = {}
for A in GUIDED:
    d = [m(c, f"LP_{A}") - m(c, "LP_plain") for c in C]
    ci = boot_median(d)
    cib = boot_median(d, q=(100 / 120, 100 - 100 / 120))  # 98.33% two-sided
    dec = "improves" if cib[1] < 0 else ("hurts" if cib[0] > 0 else "no detectable change")
    g1 = all(np.median([m(c, f"{k}_{A}") - m(c, f"{k}_plain") for c in C]) <= 0 for k in ("RMSE", "DSSIM"))
    lr = lambda a: float(np.median([abs(math.log(max(c[f"DE_{a}"], 1e-9) / c["DE_real"])) for c in C]))
    g2 = lr(A) <= lr("plain") + math.log(1.15)
    prim[A] = {"dLP": summ(d), "ci95": ci, "ci9833": cib, "decision": dec,
               "dRMSE": summ([m(c, f"RMSE_{A}") - m(c, "RMSE_plain") for c in C]),
               "dDSSIM": summ([m(c, f"DSSIM_{A}") - m(c, "DSSIM_plain") for c in C]),
               "G1": bool(g1), "G2": bool(g2), "abslog_DE_over_real": lr(A), "abslog_DE_over_real_plain": lr("plain")}
gap = lambda c, own, sw: m(c, f"LP_{sw}") - m(c, f"LP_{own}")
dgap = [gap(c, "neg3", "swap_neg3") - gap(c, "plain", "swap") for c in C]
out["S1"] = {"gap_plain": summ([gap(c, "plain", "swap") for c in C]),
             "gap_neg3": summ([gap(c, "neg3", "swap_neg3") for c in C]), "dgap": summ(dgap),
             "Daction_over_Dseed_plain_median": float(np.median([c["Daction_plain"] / c["Dseed_plain"] for c in C])),
             "Daction_over_Dseed_neg3_median": float(np.median([c["Daction_neg3"] / c["Dseed_neg3"] for c in C]))}
for A in GUIDED:
    g3 = (np.mean(dgap) >= 0) if A == "neg3" else None
    prim[A]["G3"] = None if g3 is None else bool(g3)
    prim[A]["fix_candidate"] = prim[A]["decision"] == "improves" and prim[A]["G1"] and prim[A]["G2"] and g3 is not False
out["primary"] = prim
out["S2"] = {a: {"Dseed": summ([c[f"Dseed_{a}"] for c in C]),
                 "median_ratio_vs_plain": float(np.median([c[f"Dseed_{a}"] / c["Dseed_plain"] for c in C]))} for a in ARMS}
out["S3"] = {a: float(np.median([c[f"DE_{a}"] / c["DE_real"] for c in C])) for a in ARMS}
cm = [c["ctrl_maxdiff"] for c in C if c["ctrl_maxdiff"] is not None]
out["S4_ctrl"] = {"n": len(cm), "max_abs_diff_max": float(max(cm)) if cm else None,
                  "n_exact": int(sum(x == 0 for x in cm))}
out["S5_static"] = {a: summ([m(c, f"LP_{a}") - c["LP_static"] for c in C]) for a in ARMS}
out["means"] = {k: {a: float(np.mean([m(c, f"{k}_{a}") for c in C])) for a in ARMS} for k in ("LP", "RMSE", "DSSIM")}
out["means"]["static"] = {k: float(np.mean([c[f"{k}_static"] for c in C])) for k in ("LP", "RMSE", "DSSIM")}
out["hook_execution"] = {"counts": {a: sorted(set(v)) for a, v in hook["guided_steps_counts"].items()},
                         "unexpected": hook["unexpected"][:50]}
json.dump(out, open(outp, "w"), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != "per_clip"}, indent=1))
