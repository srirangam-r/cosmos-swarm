# Washout survey (dk2): per clip, global-luma excursion from frame 0 and the share of frames that are washed out.
# washed frame: |mean - mean0| > 30 gray OR luma std < 0.6 * std0.  usage: python3 -I washout.py OUT.json clips...
import sys, json, os, re, cv2, numpy as np
res = {}
for p in sys.argv[2:]:
    c = cv2.VideoCapture(p); m, s = [], []
    while True:
        ok, f = c.read()
        if not ok: break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32); m.append(g.mean()); s.append(g.std())
    if not m: continue
    m, s = np.array(m), np.array(s); w = (np.abs(m - m[0]) > 30) | (s < 0.6 * s[0])
    res[os.path.basename(p)[:-4]] = dict(max_dmean=float(np.abs(m - m[0]).max()), min_std_ratio=float((s / s[0]).min()),
                                         washed_frac=float(w.mean()), n=len(m))
json.dump(res, open(sys.argv[1], "w"), indent=1)
arms = {}
for k, v in res.items():
    a = "recon" if k.startswith("A_") else "base" if k.startswith("B_") else re.search(r"_(tlo|slo|all)_s\d+$", k).group(1) if re.search(r"_(tlo|slo|all)_s\d+$", k) else "W/other"
    arms.setdefault(a, []).append(v)
for a, L in arms.items():
    wf = np.array([x["washed_frac"] for x in L])
    print(f"{a:6s} n={len(L):3d} clips with >=10% washed frames: {int((wf >= .1).sum())}  median washed_frac {np.median(wf):.2f}  median max|dmean| {np.median([x['max_dmean'] for x in L]):.1f}")
