"""Task 255 E1 analysis (frozen before any clip is fetched).

Usage: python3 analyze.py <devset_dir> <clips_dir> <out.json>
Clips: t255_<clip>_{own,swap}_s{1,2,3}.mp4 (17 frames, 256x256, frame 0 = conditioning frame).
All metrics use generated frames 1..16 vs real frames 1..16 (real.mp4 frames 0..32 at 5 fps).

Per clip:
  D_seed   = mean LPIPS between different seeds within an arm (3 pairs x 2 arms)
  D_action = mean LPIPS between OWN and SWAP at the same seed (3 seeds)
  ratio    = D_action / D_seed
  E_own, E_swap = LPIPS to the real future, averaged over seeds; dE = E_swap - E_own
  eta2_action, eta2_seed = pixel two-way (arm x seed) sum-of-squares shares, frames 1..16
  floor = LPIPS(repeat real frame 0, real future)
Per frame t: D_seed(t), D_action(t) (does noise decide early and action late, or vice versa?).
PRIMARY (prereg): fraction of clips with D_action > D_seed, and median ratio with a clip-bootstrap 95% CI.
  "Action decides" if CI lower bound > 1; "noise decides" if CI upper bound < 1; else mixed.
SECONDARY: dE mean +/- SE (clip-level) and sign count (wrong actions should raise error vs real);
  eta2 shares; Spearman of D_action vs normalized action distance ||a_own - a_donor||.
Determinism check: *_dup clips vs originals, max abs pixel diff.
"""
import glob, itertools, json, os, sys
import av, numpy as np, torch, lpips
from scipy.stats import spearmanr

dev, cdir, outp = sys.argv[1:4]
ids = [c["id"] for c in json.load(open(os.path.join(dev, "index.json")))["clips"]]
N = len(ids)
SEEDS = [1, 2, 3]
net = lpips.LPIPS(net="alex", verbose=False)


def load(p):
    with av.open(p) as c:
        return np.stack([f.to_ndarray(format="rgb24") for f in c.decode(video=0)]).astype(np.float32) / 255.0


def lp(a, b):  # per-frame LPIPS, a,b: T,H,W,3 in [0,1]
    ta = torch.from_numpy(a).permute(0, 3, 1, 2) * 2 - 1
    tb = torch.from_numpy(b).permute(0, 3, 1, 2) * 2 - 1
    with torch.no_grad():
        return net(ta, tb).flatten().numpy()


res, rng = {}, np.random.default_rng(0)
for i, cid in enumerate(ids):
    donor = ids[(i + N // 2) % N]
    X = {}
    try:
        for arm in ("own", "swap"):
            for s in SEEDS:
                X[arm, s] = load(os.path.join(cdir, f"t255_{cid}_{arm}_s{s}.mp4"))[1:17]
    except Exception as e:
        print("skip", cid, e); continue
    real = load(os.path.join(dev, cid, "real.mp4"))[1:17]
    r0 = np.repeat(load(os.path.join(dev, cid, "real.mp4"))[:1], 16, 0)
    ds = [lp(X[a, s1], X[a, s2]) for a in ("own", "swap") for s1, s2 in itertools.combinations(SEEDS, 2)]
    da = [lp(X["own", s], X["swap", s]) for s in SEEDS]
    eo = [lp(X["own", s], real).mean() for s in SEEDS]
    es = [lp(X["swap", s], real).mean() for s in SEEDS]
    A = np.stack([np.stack([X[a, s] for s in SEEDS]) for a in ("own", "swap")])  # 2,3,T,H,W,C
    g = A.mean((0, 1)); ma = A.mean(1); ms = A.mean(0)
    sst = ((A - g) ** 2).sum(); ssa = 3 * ((ma - g) ** 2).sum(); sss = 2 * ((ms - g) ** 2).sum()
    ao = np.array(json.load(open(os.path.join(dev, cid, "action_chunks.json")))["action_chunks"][0])
    ad = np.array(json.load(open(os.path.join(dev, donor, "action_chunks.json")))["action_chunks"][0])
    res[cid] = dict(donor=donor, D_seed=float(np.mean(ds)), D_action=float(np.mean(da)),
                    ratio=float(np.mean(da) / np.mean(ds)), E_own=float(np.mean(eo)), E_swap=float(np.mean(es)),
                    dE=float(np.mean(es) - np.mean(eo)), floor=float(lp(r0, real).mean()),
                    eta2_action=float(ssa / sst), eta2_seed=float(sss / sst),
                    D_seed_t=np.mean(ds, 0).tolist(), D_action_t=np.mean(da, 0).tolist(),
                    act_dist=float(np.linalg.norm(ao - ad) / np.sqrt(ao.size)))
    print(cid, {k: round(v, 3) for k, v in res[cid].items() if isinstance(v, float)}, flush=True)

k = list(res)
r = np.array([res[c]["ratio"] for c in k]); dE = np.array([res[c]["dE"] for c in k])
boot = [np.median(rng.choice(r, len(r))) for _ in range(5000)]
lo, hi = np.percentile(boot, [2.5, 97.5])
summ = dict(n_clips=len(k),
            frac_action_gt_seed=float(np.mean(r > 1)), median_ratio=float(np.median(r)), ratio_ci95=[float(lo), float(hi)],
            verdict="action decides" if lo > 1 else ("noise decides" if hi < 1 else "mixed"),
            D_seed_mean=float(np.mean([res[c]["D_seed"] for c in k])), D_action_mean=float(np.mean([res[c]["D_action"] for c in k])),
            dE_mean=float(dE.mean()), dE_se=float(dE.std(ddof=1) / np.sqrt(len(dE))), dE_pos=int((dE > 0).sum()),
            E_own_mean=float(np.mean([res[c]["E_own"] for c in k])), floor_mean=float(np.mean([res[c]["floor"] for c in k])),
            eta2_action_median=float(np.median([res[c]["eta2_action"] for c in k])),
            eta2_seed_median=float(np.median([res[c]["eta2_seed"] for c in k])),
            spearman_Daction_actdist=float(spearmanr([res[c]["D_action"] for c in k], [res[c]["act_dist"] for c in k])[0]),
            D_seed_t=np.mean([res[c]["D_seed_t"] for c in k], 0).tolist(),
            D_action_t=np.mean([res[c]["D_action_t"] for c in k], 0).tolist())
dups = {}
for p in glob.glob(os.path.join(cdir, "t255_*_dup.mp4")):
    o = p.replace("_dup.mp4", ".mp4")
    if os.path.exists(o):
        dups[os.path.basename(p)] = float(np.abs(load(p) - load(o)).max() * 255)
summ["determinism_maxabs"] = dups
json.dump(dict(summary=summ, per_clip=res), open(outp, "w"), indent=1)
print(json.dumps({k2: v for k2, v in summ.items() if not k2.endswith("_t")}, indent=1))
