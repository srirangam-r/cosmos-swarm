"""POST HOC (after seeing result.json): are same-seed clips on different inputs the same video?
Gray 208x120 per-frame MAE (frames 0-92). Compare same seed / different input vs different seed / same input,
and the input first frames against each other."""
import itertools, json, sys
import cv2, numpy as np
def load(p):
    c = cv2.VideoCapture(p); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (208, 120), interpolation=cv2.INTER_AREA).astype(np.float32))
    return np.stack(F)
I = ['pend10', 'pend11', 'pend14']; S = range(601, 625)
V = {(i, s): load(f'clips/N_E3_{i}_s{s}.mp4') for i in I for s in S}
mae = lambda a, b: float(np.abs(a - b).mean())
f0 = {f'{a}:{b}': mae(V[a, 601][0], V[b, 601][0]) for a, b in itertools.combinations(I, 2)}
same_seed = {f'{a}:{b}': [mae(V[a, s], V[b, s]) for s in S] for a, b in itertools.combinations(I, 2)}
rng = np.random.default_rng(0)
diff_seed = {i: [mae(V[i, s], V[i, t]) for s, t in itertools.combinations(S, 2)] for i in I}
# late-half only (frames 46-92): motion content after the shared start
late = lambda a, b: float(np.abs(a[46:] - b[46:]).mean())
same_late = [late(V[a, s], V[b, s]) for a, b in itertools.combinations(I, 2) for s in S]
diff_late = [late(V[i, s], V[i, t]) for i in I for s, t in itertools.combinations(S, 2)]
out = dict(f0_mae=f0,
           same_seed_cross_input_median={k: float(np.median(v)) for k, v in same_seed.items()},
           same_seed_cross_input_range={k: [float(min(v)), float(max(v))] for k, v in same_seed.items()},
           diff_seed_same_input_median={k: float(np.median(v)) for k, v in diff_seed.items()},
           diff_seed_same_input_min={k: float(min(v)) for k, v in diff_seed.items()},
           late_same_seed_median=float(np.median(same_late)), late_diff_seed_median=float(np.median(diff_late)),
           late_diff_seed_p5=float(np.percentile(diff_late, 5)),
           frac_same_seed_below_diff_min=float(np.mean([x < min(min(v) for v in diff_seed.values()) for v in same_seed.values() for x in v])))
json.dump(out, open('posthoc_sameclip.json', 'w'), indent=1)
print(json.dumps(out, indent=1))

# POST HOC 2: matched control = cross-input pairs with DIFFERENT seeds (same image-difference floor).
# Also the pendulum ROI (x 200-460, y 60-300 at 832x480 -> 50-115, 15-75 at 208x120) and the
# motion-energy time series (mean |frame diff| in the ROI) correlation.
roi = (slice(15, 75), slice(50, 115))
me = {k: np.abs(np.diff(v[:, roi[0], roi[1]], axis=0)).mean((1, 2)) for k, v in V.items()}
res2 = {}
for a, b in itertools.combinations(I, 2):
    ss = [mae(V[a, s][:, roi[0], roi[1]], V[b, s][:, roi[0], roi[1]]) for s in S]
    ds = [mae(V[a, s][:, roi[0], roi[1]], V[b, t][:, roi[0], roi[1]]) for s in S for t in S if s != t]
    rs = [float(np.corrcoef(me[a, s], me[b, s])[0, 1]) for s in S]
    rd = [float(np.corrcoef(me[a, s], me[b, t])[0, 1]) for s in S for t in S if s != t]
    # rank of each same-seed pair among the 24 candidates for that seed (1 = closest)
    ranks = []
    for s in S:
        d = {t: mae(V[a, s][:, roi[0], roi[1]], V[b, t][:, roi[0], roi[1]]) for t in S}
        ranks.append(1 + sum(d[t] < d[s] for t in S if t != s))
    res2[f'{a}:{b}'] = dict(roi_mae_same_med=float(np.median(ss)), roi_mae_diff_med=float(np.median(ds)),
                            roi_mae_diff_p5=float(np.percentile(ds, 5)),
                            me_r_same_med=float(np.median(rs)), me_r_diff_med=float(np.median(rd)),
                            same_seed_rank1=int(sum(r == 1 for r in ranks)), ranks=ranks)
out['matched_cross_input'] = res2
json.dump(out, open('posthoc_sameclip.json', 'w'), indent=1)
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'ranks'} for k, v in res2.items()}, indent=1))
