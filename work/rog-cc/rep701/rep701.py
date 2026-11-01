#!/usr/bin/env python3
"""Independent replication of rahul's #701 (base Nano robot FD vs a frozen frame, per view, + seed-noise floor).

Written from the finding text only (not from robot_pred/score_seeds.py).
Protocol as stated in #701: gen = 17 f at 640x528 (frame 0 = conditioning), compared against real_future.npy[:, :528]
(16 f), gen frames 1..16 vs real 0..15. Views (rows, cols): wrist 0-360 x 0-640, ext1 360-528 x 0-320, ext2 360-528 x 320-640,
all = full 528x640. Frozen baseline = gen frame 0 held for 16 frames (cancels the resize/VAE/codec floor).
Metrics: LPIPS-alex (lpips 0.1.4, inputs scaled to [-1,1], per frame, mean over 16 frames) and my own PSNR.
Item level: average over the seeds an item has, then mean +- SE over items. Seed noise: seed0 - seed1 per item (items with both).
Usage: rep701.py devset_dir gens_dir --out out.json
"""
import sys, os, glob, json, re
import numpy as np, cv2, torch, lpips

VIEWS = {"all": (slice(0, 528), slice(0, 640)), "wrist": (slice(0, 360), slice(0, 640)),
         "ext1": (slice(360, 528), slice(0, 320)), "ext2": (slice(360, 528), slice(320, 640))}
net = lpips.LPIPS(net="alex", verbose=False).eval()


def read(p):
    cap = cv2.VideoCapture(p); F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    return np.stack(F)


def lp(A, B):  # A, B: (T,H,W,3) uint8 -> per-frame LPIPS
    t = lambda X: torch.from_numpy(X).permute(0, 3, 1, 2).float() / 127.5 - 1
    with torch.no_grad():
        return net(t(A), t(B)).flatten().numpy()


def psnr(A, B):
    mse = ((A.astype(np.float64) - B.astype(np.float64)) ** 2).reshape(len(A), -1).mean(1)
    return 10 * np.log10(255.0 ** 2 / np.maximum(mse, 1e-10))


def score(G, R):
    return {v: {"lpips": float(lp(np.ascontiguousarray(G[:, ys, xs]), np.ascontiguousarray(R[:, ys, xs])).mean()),
                "psnr": float(psnr(G[:, ys, xs], R[:, ys, xs]).mean())} for v, (ys, xs) in VIEWS.items()}


def ms(x):
    x = np.asarray(x, float); n = len(x)
    return {"mean": float(x.mean()), "se": float(x.std(ddof=1) / np.sqrt(n)) if n > 1 else None, "n": n,
            "n_pos": int((x > 0).sum())}


dev, gdir = sys.argv[1], sys.argv[2]; out = sys.argv[sys.argv.index("--out") + 1]
per = {}
for d in sorted(glob.glob(gdir + "/droid*")):
    item = os.path.basename(d)
    R = np.load(f"{dev}/{item}/real_future.npy")[:, :528]
    seeds = {}
    for p in sorted(glob.glob(d + "/gen_base528_seed*.mp4")):
        s = int(re.search(r"seed(\d+)", p).group(1)); G0 = read(p)
        assert G0.shape[1:3] == (528, 640), G0.shape
        G = G0[1:17]; n = min(len(G), len(R)); G, Rn = G[:n], R[:n]
        Z = np.repeat(G0[:1], n, axis=0)
        seeds[s] = {"gen": score(G, Rn), "frozen": score(Z, Rn), "n_frames": n, "_G": G}
    if not seeds: continue
    r = {"seeds": {s: {k: v for k, v in x.items() if k != "_G"} for s, x in seeds.items()}}
    if 0 in seeds and 1 in seeds:
        r["seed_vs_seed"] = score(seeds[0]["_G"], seeds[1]["_G"])
    per[item] = r
    print(item, sorted(seeds), {s: round(x["gen"]["all"]["lpips"], 3) for s, x in seeds.items()}, flush=True)

S = {}
for v in VIEWS:
    for m in ("lpips", "psnr"):
        gen = [np.mean([x["gen"][v][m] for x in r["seeds"].values()]) for r in per.values()]
        frz = [np.mean([x["frozen"][v][m] for x in r["seeds"].values()]) for r in per.values()]
        S[f"{v}/{m}"] = {"gen": ms(gen), "frozen": ms(frz), "gen_minus_frozen": ms(np.array(gen) - np.array(frz)),
                         "n_items_gen_worse": int(sum((g > f) if m == "lpips" else (g < f) for g, f in zip(gen, frz)))}
both = [r for r in per.values() if "seed_vs_seed" in r]
for v in VIEWS:
    S[f"{v}/seed"] = {"seed0_minus_seed1_lpips": ms([r["seeds"][0]["gen"][v]["lpips"] - r["seeds"][1]["gen"][v]["lpips"] for r in both]),
                      "lpips_seed0_vs_seed1": ms([r["seed_vs_seed"][v]["lpips"] for r in both])}
res = {"n_items": len(per), "n_clips": sum(len(r["seeds"]) for r in per.values()), "summary": S, "per_item": per}
json.dump(res, open(out, "w"), indent=1)
for k, v in S.items():
    print(k, json.dumps({a: {b: (round(c, 4) if isinstance(c, float) else c) for b, c in x.items()} if isinstance(x, dict) else x for a, x in v.items()}))
