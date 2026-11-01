# task 45: per-arm motion index (mean |frame diff| in drop ROI) aggregated over seeds; contrasts with paired-by-seed SE.
import sys, glob, re, cv2, numpy as np, json, collections, os
Y0,Y1,X0,X1=[int(v) for v in os.environ.get("ROI","150,440,180,440").split(",")]
def midx(p):
    cap = cv2.VideoCapture(p); prev = None; d = []
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)[Y0:Y1, X0:X1].astype(np.float32)
        if prev is not None: d.append(float(np.mean(np.abs(g - prev))))
        prev = g
    d = np.array(d); return d.mean(), d[-24:].mean()
R = collections.defaultdict(dict)
for p in sorted(sum([glob.glob(d + "/arm*_s*.mp4") for d in sys.argv[1].split(",")], [])):
    m = re.search(r"arm(\w)_rope\d+_text\d+_s(\d+)", p); arm, s = m.group(1), int(m.group(2))
    R[arm][s] = midx(p)
out = {}
for arm in sorted(R):
    v = np.array(list(R[arm].values())); n = len(v)
    out[arm] = dict(n=n, all=[v[:, 0].mean(), v[:, 0].std(ddof=1) / np.sqrt(n) if n > 1 else np.nan],
                    last24=[v[:, 1].mean(), v[:, 1].std(ddof=1) / np.sqrt(n) if n > 1 else np.nan])
    print(f"{arm} n={n} all {out[arm]['all'][0]:.2f}±{out[arm]['all'][1]:.2f}  last24 {out[arm]['last24'][0]:.2f}±{out[arm]['last24'][1]:.2f}")
for a, b, lab in [("B", "A", "RoPE 12 vs 24 @text24"), ("C", "A", "text 12 vs 24 @rope24"), ("D", "B", "text 12 vs 24 @rope12"),
                  ("D", "C", "RoPE 12 vs 24 @text12"), ("E", "A", "RoPE 6 vs 24 @text24")]:
    s = sorted(set(R[a]) & set(R[b]))
    if len(s) < 2: continue
    for k, nm in [(0, "all"), (1, "last24")]:
        d = np.array([R[a][i][k] - R[b][i][k] for i in s])
        print(f"{a}-{b} ({lab}) {nm}: {d.mean():+.2f}±{d.std(ddof=1)/np.sqrt(len(d)):.2f} (n={len(d)})")
json.dump(dict(per_clip={a: {str(s): list(v) for s, v in R[a].items()} for a in R}, summary=out), open(sys.argv[2], "w"), indent=1)
