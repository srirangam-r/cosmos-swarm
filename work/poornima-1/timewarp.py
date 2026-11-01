# task 45: does the RoPE fps act as a clock? Per-frame motion profile m(t) = mean|frame diff| in drop ROI.
# For each arm X vs reference A (same seed), find the time-compression k minimising
#   || m_X(t) - m_A(k*t) ||  over t where k*t stays inside the clip (k in [0.5, 4]).
# If RoPE is a pure clock, B/D (rope12) should give k~2 and E (rope6) k~4; C (text12) k~1.
# Also report "settle frame": first frame after which the 5-frame smoothed motion stays < 1.5 (gray levels).
import sys, glob, re, json, collections, cv2, numpy as np
def prof(p):
    cap = cv2.VideoCapture(p); prev = None; d = []
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)[150:440, 180:440].astype(np.float32)
        if prev is not None: d.append(float(np.mean(np.abs(g - prev))))
        prev = g
    return np.array(d)
def settle(m, thr=1.5):
    s = np.convolve(m, np.ones(5) / 5, mode="same")
    above = np.where(s >= thr)[0]
    return int(above[-1] + 1) if len(above) else 0
def best_k(mx, ma, ks=np.round(np.arange(0.5, 4.01, 0.05), 3)):
    t = np.arange(len(mx)); errs = []
    for k in ks:
        tt = k * t; ok = tt <= len(ma) - 1
        if ok.sum() < 12: errs.append(np.inf); continue
        ia = np.interp(tt[ok], np.arange(len(ma)), ma)
        errs.append(np.mean((mx[ok] - ia) ** 2))
    return float(ks[int(np.argmin(errs))])
P = collections.defaultdict(dict)
for d in sys.argv[1:-1]:
    for p in sorted(glob.glob(d + "/arm*_s*.mp4")):
        m = re.search(r"arm(\w)_rope\d+_text\d+_s(\d+)", p)
        P[m.group(1)][int(m.group(2))] = prof(p)
out = {"settle": {}, "k_vs_A": {}}
for arm in sorted(P):
    st = [settle(v) for v in P[arm].values()]
    out["settle"][arm] = dict(n=len(st), mean=float(np.mean(st)), se=float(np.std(st, ddof=1) / np.sqrt(len(st))), vals=st)
    print(f"settle {arm}: {np.mean(st):.1f}±{np.std(st, ddof=1)/np.sqrt(len(st)):.1f} f  {st}")
for arm in sorted(P):
    if arm == "A": continue
    s = sorted(set(P[arm]) & set(P["A"]))
    ks = [best_k(P[arm][i], P["A"][i]) for i in s]
    # pooled: mean profile per arm over common seeds
    kp = best_k(np.mean([P[arm][i] for i in s], 0), np.mean([P["A"][i] for i in s], 0))
    # null: A vs A with seeds shifted (different seed), to see what k looks like by chance
    out["k_vs_A"][arm] = dict(n=len(s), per_seed=ks, median=float(np.median(ks)), pooled=kp)
    print(f"k {arm} vs A: per-seed median {np.median(ks):.2f} {ks}  pooled-profile k={kp:.2f}")
sA = sorted(P["A"]); null = [best_k(P["A"][sA[i]], P["A"][sA[(i + 1) % len(sA)]]) for i in range(len(sA))]
out["k_null_A_vs_A_otherseed"] = null; print("null A(seed i) vs A(seed i+1):", null, "median", np.median(null))
json.dump(out, open(sys.argv[-1], "w"), indent=1)
