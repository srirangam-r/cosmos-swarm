"""rahul-api-2 review of rog1 #5243. usage: review.py <devset_dir> <clips_dir> <out.json>"""
import itertools, json, os, sys
import cv2, numpy as np

dev, cdir, outp = sys.argv[1:4]
ids = [c["id"] for c in json.load(open(os.path.join(dev, "index.json")))["clips"]]
SEEDS = [1, 2, 3]


def load(p):
    c = cv2.VideoCapture(p); F = []
    while True:
        ok, f = c.read()
        if not ok:
            break
        F.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float64))
    return np.stack(F)


def ssim_map(a, b):
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    g = lambda x: cv2.GaussianBlur(x, (11, 11), 1.5)
    ma, mb = g(a), g(b)
    va, vb, cab = g(a * a) - ma ** 2, g(b * b) - mb ** 2, g(a * b) - ma * mb
    return ((2 * ma * mb + C1) * (2 * cab + C2)) / ((ma ** 2 + mb ** 2 + C1) * (va + vb + C2))


def dist(A, B, mask=None):
    """A, B: T,H,W gray. returns dict of per-clip scalar distances."""
    d = A - B
    out = {"rmse": float(np.sqrt((d ** 2).mean())),
           "dssim": float(np.mean([1 - ssim_map(a, b).mean() for a, b in zip(A, B)]))}
    if mask is not None:
        out["rmse_mask"] = float(np.sqrt((d[:, mask] ** 2).mean()))
    return out


def motion_mask(real):
    r = np.stack([cv2.GaussianBlur(f, (3, 3), 0) for f in real])
    m = (np.abs(r[1:] - r[:1]).max(0) > 25).astype(np.uint8)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    return m.astype(bool)


def selftest():
    rng = np.random.default_rng(0)
    A = rng.uniform(0, 255, (16, 64, 64))
    assert all(abs(v) < 1e-9 for v in dist(A, A, np.ones((64, 64), bool)).values())
    S = np.repeat(A[:1], 17, 0)
    assert motion_mask(S).sum() == 0
    print("selftest ok")


selftest()
METRICS = ["rmse", "dssim", "rmse_mask"]
res = {}
for cid in ids:
    realall = load(os.path.join(dev, cid, "real.mp4"))
    real, r0 = realall[1:17], np.repeat(realall[:1], 16, 0)
    m = motion_mask(realall[:17])
    use_mask = m.mean() >= 0.01
    mk = m if use_mask else None
    X = {(a, s): load(os.path.join(cdir, f"t255_{cid}_{a}_s{s}.mp4"))[1:17] for a in ("own", "swap") for s in SEEDS}
    assert all(v.shape == real.shape for v in X.values()), cid
    ds = [dist(X[a, s1], X[a, s2], mk) for a in ("own", "swap") for s1, s2 in itertools.combinations(SEEDS, 2)]
    da = [dist(X["own", s], X["swap", s], mk) for s in SEEDS]
    eo = [dist(X["own", s], real, mk) for s in SEEDS]
    es = [dist(X["swap", s], real, mk) for s in SEEDS]
    fl = dist(r0, real, mk)
    assert dist(real, real, mk)["rmse"] == 0
    row = {"mask_frac": float(m.mean()), "mask_used": bool(use_mask)}
    for k in METRICS:
        if k == "rmse_mask" and not use_mask:
            continue
        mean = lambda L: float(np.mean([x[k] for x in L]))
        row[k] = dict(D_seed=mean(ds), D_action=mean(da), ratio=mean(da) / mean(ds), E_own=mean(eo),
                      E_swap=mean(es), floor=fl[k])
    res[cid] = row
    print(cid, round(m.mean(), 3), {k: round(row[k]["ratio"], 2) for k in METRICS if k in row}, flush=True)

rng = np.random.default_rng(0)
summ = {}
for k in METRICS:
    c = [cid for cid in res if k in res[cid]]
    g = lambda f: np.array([res[cid][k][f] for cid in c])
    r = g("ratio"); boot = [np.median(rng.choice(r, len(r))) for _ in range(5000)]
    gain = g("floor") - g("E_own"); dE = g("E_swap") - g("E_own")
    se = lambda x: float(x.std(ddof=1) / np.sqrt(len(x)))
    summ[k] = dict(n=len(c), median_ratio=float(np.median(r)), ratio_ci95=[float(v) for v in np.percentile(boot, [2.5, 97.5])],
                   frac_action_gt_seed=float(np.mean(r > 1)), D_seed_mean=float(g("D_seed").mean()),
                   D_action_mean=float(g("D_action").mean()), E_own_mean=float(g("E_own").mean()),
                   floor_mean=float(g("floor").mean()), gain_floor_minus_own=float(gain.mean()), gain_se=se(gain),
                   gain_pos=int((gain > 0).sum()), rel_gain=float(gain.mean() / g("floor").mean()),
                   dE_swap_minus_own=float(dE.mean()), dE_se=se(dE), dE_pos=int((dE > 0).sum()),
                   seed_over_err=float(g("D_seed").mean() / g("E_own").mean()))
summ["mask_frac_median"] = float(np.median([res[c]["mask_frac"] for c in res]))
json.dump(dict(summary=summ, per_clip=res), open(outp, "w"), indent=1)
print(json.dumps(summ, indent=1))
