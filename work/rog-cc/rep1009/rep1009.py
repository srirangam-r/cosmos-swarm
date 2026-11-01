#!/usr/bin/env python3
"""Independent replication of rahul's #1009 (Nano DROID forward dynamics: does the output follow the action input, per view?).
Written from the #1009 text only (not robot_pred/compare_swap.py); reuses my own rep701.py I/O conventions.
Gens: per item gen_base528_seed{0,1}.mp4 and gen_swap5_seed{0,1}.mp4 (swap = item i driven by the actions of item (i+5)%10),
17 f at 640x528; frames 1..16 compared (frame 0 = shared conditioning frame). Real = real_future.npy[:, :528] (16 f).
Views as in rep701: wrist rows 0-360; ext1 360-528 x 0-320; ext2 360-528 x 320-640; all = full.
Per item (n=10), LPIPS-alex mean over 16 frames:
  act_same  = mean_s LPIPS(swap_s, base_s)              (#1009's 'swap vs base, same seed')
  seed      = LPIPS(base_0, base_1)                      (#1009's noise floor)
  act_cross = mean_s LPIPS(swap_s, base_{1-s})           (my addition: cross-seed pairing, so both terms carry seed noise)
  d_act = act_same - seed ; d_act_cross = act_cross - seed
  err_base/err_swap = mean_s LPIPS(gen_s, real); d_err = err_swap - err_base. Also PSNR versions of err.
Stats: item-level mean +- SE (n=10), n_pos.
Usage: rep1009.py devset_dir gens_dir --out out.json"""
import sys, os, glob, json
import numpy as np, cv2, torch, lpips
VIEWS = {"all": (slice(0, 528), slice(0, 640)), "wrist": (slice(0, 360), slice(0, 640)),
         "ext1": (slice(360, 528), slice(0, 320)), "ext2": (slice(360, 528), slice(320, 640))}
torch.set_num_threads(12)
net = lpips.LPIPS(net="alex", verbose=False).eval()
def read(p):
    cap = cv2.VideoCapture(p); F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
    F = np.stack(F); assert F.shape[1:3] == (528, 640) and len(F) >= 17, (p, F.shape); return F[1:17]
def lp(A, B):
    t = lambda X: torch.from_numpy(np.ascontiguousarray(X)).permute(0, 3, 1, 2).float() / 127.5 - 1
    with torch.no_grad(): return float(net(t(A), t(B)).mean())
def psnr(A, B):
    mse = ((A.astype(np.float64) - B.astype(np.float64)) ** 2).reshape(len(A), -1).mean(1)
    return float((10 * np.log10(255.0 ** 2 / np.maximum(mse, 1e-10))).mean())
def views(f, A, B): return {v: f(A[:, ys, xs], B[:, ys, xs]) for v, (ys, xs) in VIEWS.items()}
def ms(x):
    x = np.asarray(x, float); return {"mean": float(x.mean()), "se": float(x.std(ddof=1) / np.sqrt(len(x))), "n": len(x), "n_pos": int((x > 0).sum())}
dev, gdir = sys.argv[1], sys.argv[2]; out = sys.argv[sys.argv.index("--out") + 1]
per = {}
for d in sorted(glob.glob(gdir + "/droid*")):
    it = os.path.basename(d); R = np.load(f"{dev}/{it}/real_future.npy")[:16, :528]
    B = {s: read(f"{d}/gen_base528_seed{s}.mp4") for s in (0, 1)}; W = {s: read(f"{d}/gen_swap5_seed{s}.mp4") for s in (0, 1)}
    r = {"seed": views(lp, B[0], B[1]),
         "act_same": {s: views(lp, W[s], B[s]) for s in (0, 1)}, "act_cross": {s: views(lp, W[s], B[1 - s]) for s in (0, 1)},
         "err_base": {s: views(lp, B[s], R) for s in (0, 1)}, "err_swap": {s: views(lp, W[s], R) for s in (0, 1)},
         "psnr_base": {s: views(psnr, B[s], R) for s in (0, 1)}, "psnr_swap": {s: views(psnr, W[s], R) for s in (0, 1)},
         "swap_seed": views(lp, W[0], W[1])}
    per[it] = r; print(it, {k: round(np.mean([r[k][s]["all"] for s in (0, 1)]), 3) for k in ("act_same", "err_base", "err_swap")}, "seed", round(r["seed"]["all"], 3), flush=True)
S = {}
m2 = lambda r, k, v: np.mean([r[k][s][v] for s in (0, 1)])
for v in VIEWS:
    P = list(per.values())
    seed = np.array([r["seed"][v] for r in P]); a_s = np.array([m2(r, "act_same", v) for r in P]); a_c = np.array([m2(r, "act_cross", v) for r in P])
    eb = np.array([m2(r, "err_base", v) for r in P]); es = np.array([m2(r, "err_swap", v) for r in P])
    pb = np.array([m2(r, "psnr_base", v) for r in P]); pw = np.array([m2(r, "psnr_swap", v) for r in P])
    S[v] = {"seed": ms(seed), "swap_seed": ms([r["swap_seed"][v] for r in P]), "act_same": ms(a_s), "act_cross": ms(a_c),
            "d_act": ms(a_s - seed), "d_act_cross": ms(a_c - seed), "err_base": ms(eb), "err_swap": ms(es), "d_err": ms(es - eb),
            "psnr_base": ms(pb), "psnr_swap": ms(pw), "d_psnr": ms(pw - pb)}
json.dump({"n_items": len(per), "summary": S, "per_item": per}, open(out, "w"), indent=1)
for v, x in S.items():
    print(v, " ".join(f"{k}={y['mean']:+.4f}±{y['se']:.4f}({y['n_pos']}/{y['n']})" for k, y in x.items()))
