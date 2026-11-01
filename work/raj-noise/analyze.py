"""Program N analysis (fixed before the clips land). Usage: python -I analyze.py <clips_dir> <E0|E1|E2|E4>

Features per clip, from the mp4 (gray, 1/8 scale, blurred):
  e_t   motion energy, mean |g_t - g_{t-1}| per frame pair (92 values)
  LM    log(mean e over the last 24 pairs + 0.05)    -- "is it still moving at the end"
  V     the whole downsampled video, for clip-to-clip distance (MAE in gray levels)
Pendulum period: tools/pend_acf (ro-3; within 1% of mocap on 20/20 real GAUGE recordings), skip 8 frames.
Every clip's sidecar must record the noise spec (new server); clips without it are dropped and counted.
"""
import glob, json, os, sys
import numpy as np, cv2

PEND_ACF = os.path.expanduser("~/swarm/internals/cosmos-swarm/tools/pend_acf/pend_acf.py")

RNG = np.random.default_rng(0)


def load(path):
    c = cv2.VideoCapture(path); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    return F


def gray(F):
    G = []
    for f in F:
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)
        G.append(cv2.GaussianBlur(cv2.resize(g, (g.shape[1] // 8, g.shape[0] // 8), interpolation=cv2.INTER_AREA), (3, 3), 0))
    return np.array(G)


def features(path, period=False, color=False):
    F = load(path); G = gray(F)
    e = np.abs(np.diff(G, axis=0)).mean(axis=(1, 2))
    out = dict(e=e, LM=float(np.log(e[-24:].mean() + 0.05)), V=G)
    if period:  # the tool's own CLI, so its ok/check flag logic is unchanged
        import subprocess
        r = subprocess.run([sys.executable, "-I", PEND_ACF, path, "--fps", "24", "--skip", "8"], capture_output=True, text=True)
        try:
            j = json.loads(r.stdout.strip().splitlines()[-1])
            out["period_f"], out["period_flag"] = j.get("period_frames"), j.get("flag")
        except Exception:
            out["period_f"], out["period_flag"] = None, "error"
    if color:  # which colour dominates the saturated pixels in the middle third of the clip
        H = []
        for f in F[len(F) // 3: 2 * len(F) // 3: 3]:
            hsv = cv2.cvtColor(f, cv2.COLOR_BGR2HSV); s = hsv[..., 1] > 120; v = hsv[..., 2] > 60
            h = hsv[..., 0][s & v]
            H.append(((h < 10) | (h > 170)).sum() - ((h > 100) & (h < 130)).sum())
        out["redness"] = float(np.mean(H))  # >0: red dominates, <0: blue dominates
    return out


def clips(d, prefix):
    """(name, mp4, queue sidecar). The server-side sidecars (noise record) are checked separately on the boxes."""
    rows = [(os.path.basename(m)[:-4], m, json.load(open(m[:-4] + ".json"))) for m in sorted(glob.glob(f"{d}/{prefix}*.mp4"))]
    return rows, 0


def mae(a, b):
    return float(np.abs(a - b).mean())


def corr(a, b):
    a, b = a - a.mean(), b - b.mean(); return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum() + 1e-12))


def eta2(y, seed, arm):
    """Two-way (seed x arm, one clip per cell) sums of squares: fractions of the total for seed, arm and residual."""
    y = np.asarray(y, float); S = sorted(set(seed)); A = sorted(set(arm))
    Y = np.full((len(S), len(A)), np.nan)
    for v, s, a in zip(y, seed, arm): Y[S.index(s), A.index(a)] = v
    ok = ~np.isnan(Y).any(axis=1); Y = Y[ok]
    m = Y.mean(); sst = ((Y - m) ** 2).sum()
    sss = Y.shape[1] * ((Y.mean(axis=1) - m) ** 2).sum(); ssa = Y.shape[0] * ((Y.mean(axis=0) - m) ** 2).sum()
    return dict(seed=sss / sst, arm=ssa / sst, resid=(sst - sss - ssa) / sst, n_seeds=int(ok.sum()), n_arms=len(A))


def boot_eta2(y, seed, arm, n=2000):
    S = sorted(set(seed)); by = {s: [(v, a) for v, s2, a in zip(y, seed, arm) if s2 == s] for s in S}
    out = []
    for _ in range(n):
        pick = RNG.choice(S, len(S)); yy, ss, aa = [], [], []
        for k, s in enumerate(pick):
            for v, a in by[s]: yy.append(v); ss.append(k); aa.append(a)
        out.append(eta2(yy, ss, aa)["seed"])
    return np.percentile(out, [5, 95]).tolist()


def e0(d):
    rows, dropped = clips(d, "N_E0_"); f = {n: features(p) for n, p, _ in rows}
    key = lambda n: (n.split("_")[2], n.split("_")[3], int(n.split("_s")[-1]))  # cls, device, seed
    by = {key(n): v["V"] for n, v in f.items()}
    res = {"dropped_without_noise_record": dropped}
    for dev in ("cpu", "cuda"):
        same, diff = [], []
        for (c1, d1, s1), v1 in by.items():
            for (c2, d2, s2), v2 in by.items():
                if d1 != dev or d2 != dev or c1 >= c2: continue
                (same if s1 == s2 else diff).append(mae(v1, v2))
        res[dev] = dict(same_seed_cross_gpu_mae=(np.mean(same), len(same)) if same else None,
                        diff_seed_cross_gpu_mae=(np.mean(diff), len(diff)) if diff else None)
    within = [mae(v1, v2) for (c1, d1, s1), v1 in by.items() for (c2, d2, s2), v2 in by.items()
              if c1 == c2 and d1 == d2 == "cpu" and s1 < s2]
    res["cpu_diff_seed_same_gpu_mae"] = (np.mean(within), len(within)) if within else None
    print(json.dumps(res, indent=1, default=float))


def e4(d):
    rows, dropped = clips(d, "N_E4_"); f = {n: features(p) for n, p, _ in rows}
    pairs = sorted({int(n.split("_s")[-1]) for n in f}); arms = ["tlo", "thi", "slo", "shi", "reg"]
    res = {"dropped_without_noise_record": dropped, "n_pairs": len(pairs)}
    for arm in arms + ["A", "B"]:
        sv, se, slm = [], [], []
        for s in pairs:
            A, B, X = f.get(f"N_E4_A_s{s}"), f.get(f"N_E4_B_s{s}"), f.get(f"N_E4_{arm}_s{s}")
            if not (A and B and X): continue
            dA, dB = mae(X["V"], A["V"]), mae(X["V"], B["V"]); sv.append(dA / (dA + dB + 1e-9))
            eA, eB = 1 - corr(X["e"], A["e"]), 1 - corr(X["e"], B["e"]); se.append(eA / (eA + eB + 1e-9))
            if abs(B["LM"] - A["LM"]) > 0.3: slm.append((X["LM"] - A["LM"]) / (B["LM"] - A["LM"]))
        summ = lambda v: (round(float(np.mean(v)), 3), round(float(np.std(v, ddof=1) / np.sqrt(len(v))), 3), len(v)) if len(v) > 1 else None
        res[arm] = dict(video_toward_B=summ(sv), motion_course_toward_B=summ(se), late_motion_toward_B=summ(slm))
    print(json.dumps(res, indent=1))


def e1(d):
    rows, dropped = clips(d, "N_E1_"); out = []
    for n, p, _ in rows:
        _, _, c, v, s = n.split("_"); ft = features(p, period=True, color=True)
        out.append(dict(name=n, color=c, speed=v, seed=int(s[1:]), redness=ft["redness"], LM=ft["LM"],
                        period_s=(ft["period_f"] / 24.0) if ft.get("period_f") else None, flag=ft.get("period_flag")))
    acc = np.mean([(r["redness"] > 0) == (r["color"] == "red") for r in out])
    ok = [r for r in out if r["period_s"]]
    res = {"dropped": dropped, "n": len(out), "colour_follows_text": round(float(acc), 3), "n_period_read": len(ok)}
    for sp in ("slow", "fast"):
        ps = [r["period_s"] for r in ok if r["speed"] == sp]
        res[f"period_s_{sp}"] = (round(float(np.median(ps)), 2), len(ps)) if ps else None
    full = [s for s in {r["seed"] for r in ok} if sum(1 for r in ok if r["seed"] == s) == 4]
    sub = [r for r in ok if r["seed"] in full]
    if len(full) >= 3:
        y = [np.log(r["period_s"]) for r in sub]
        res["log_period_eta2_speed_vs_seed"] = eta2(y, [r["seed"] for r in sub], [r["speed"] for r in sub])
        res["log_period_eta2_colour_vs_seed"] = eta2(y, [r["seed"] for r in sub], [r["color"] for r in sub])
    lm = eta2([r["LM"] for r in out], [r["seed"] for r in out], [f'{r["color"]}_{r["speed"]}' for r in out])
    res["late_motion_eta2_seed_vs_prompt"] = lm
    json.dump(out, open(f"{d}/E1_rows.json", "w"), indent=1)
    print(json.dumps(res, indent=1, default=float))


def e2(d):
    rows, dropped = clips(d, "N_E2_"); out = []
    for n, p, _ in rows:
        _, _, inp, arm, s = n.split("_"); ft = features(p, period=(inp == "pend"))
        out.append(dict(name=n, input=inp, arm=arm, seed=int(s[1:]), LM=ft["LM"], e=ft["e"].tolist(),
                        period_s=(ft["period_f"] / 24.0) if ft.get("period_f") else None, flag=ft.get("period_flag")))
    res = {"dropped": dropped, "n": len(out)}
    for inp in ("ball", "held", "pend"):
        r = [x for x in out if x["input"] == inp]
        if not r: continue
        y, s, a = [x["LM"] for x in r], [x["seed"] for x in r], [x["arm"] for x in r]
        res[f"{inp}_late_motion"] = dict(eta2(y, s, a), seed_ci90=boot_eta2(y, s, a, 1000))
        same = [corr(np.array(x["e"]), np.array(z["e"])) for x in r for z in r if x["seed"] == z["seed"] and x["arm"] < z["arm"]]
        diff = [corr(np.array(x["e"]), np.array(z["e"])) for x in r for z in r if x["seed"] != z["seed"] and x["arm"] < z["arm"]]
        res[f"{inp}_motion_course_corr"] = dict(same_seed_other_prompt=round(float(np.mean(same)), 3),
                                                other_seed_other_prompt=round(float(np.mean(diff)), 3))
        if inp == "pend":
            ok = [x for x in r if x["period_s"]]
            full = [sd for sd in {x["seed"] for x in ok} if sum(1 for x in ok if x["seed"] == sd) == len({x["arm"] for x in r})]
            sub = [x for x in ok if x["seed"] in full]
            res["pend_period_median_s_by_arm"] = {arm: round(float(np.median([x["period_s"] for x in ok if x["arm"] == arm])), 2)
                                                  for arm in sorted({x["arm"] for x in ok})}
            res["pend_n_period_read"] = len(ok)
            if len(full) >= 3:
                res["pend_log_period_eta2"] = eta2([np.log(x["period_s"]) for x in sub], [x["seed"] for x in sub], [x["arm"] for x in sub])
    # seed transfer across inputs (E3 preview): does a seed's late motion rank carry from one input to another?
    from scipy.stats import spearmanr
    m = {}
    for x in out: m.setdefault((x["input"], x["seed"]), []).append(x["LM"])
    seeds = sorted({x["seed"] for x in out})
    for a, b in (("ball", "held"), ("ball", "pend"), ("held", "pend")):
        sa = [np.mean(m[(a, s)]) for s in seeds if (a, s) in m and (b, s) in m]
        sb = [np.mean(m[(b, s)]) for s in seeds if (a, s) in m and (b, s) in m]
        if len(sa) > 4: res[f"seed_rank_transfer_{a}_{b}"] = round(float(spearmanr(sa, sb)[0]), 3)
    json.dump(out, open(f"{d}/E2_rows.json", "w"))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    {"E0": e0, "E1": e1, "E2": e2, "E4": e4}[sys.argv[2]](sys.argv[1])
