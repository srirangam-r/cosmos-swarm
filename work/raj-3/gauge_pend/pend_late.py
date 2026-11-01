"""Check rog2's challenge (msg 211): per-cycle period vs amplitude over the whole mocap record.
Reports mean-of-cycles over whole record, late-cycle (small amplitude) period, and the amplitude there."""
import json, sys, glob, os, numpy as np
def cycles(t, x):
    xx = x - np.median(x[-int(len(x)/3):])
    s = np.sign(xx); i = np.where((s[:-1] < 0) & (s[1:] >= 0))[0]
    tc = t[i] - xx[i]*(t[i+1]-t[i])/(xx[i+1]-xx[i])
    amps = [np.ptp(x[(t >= a) & (t < b)])/2 for a, b in zip(tc[:-1], tc[1:])]
    return np.diff(tc), np.array(amps), tc[:-1]
res = {}
for f in sorted(glob.glob(sys.argv[1]+'/*.json'), key=lambda p: int(os.path.basename(p)[:-5])):
    c = os.path.basename(f)[:-5]; d = json.load(open(f)); fps = d['FPS']
    P = np.array([d['ball'][k] for k in 'xyz']).T/1000.0
    t = np.arange(len(P))/fps
    mu = P.mean(0); U, S, Vt = np.linalg.svd(P-mu, full_matrices=False); a = (P-mu)@Vt[0]
    a0 = a[:5].mean(); rel = int(np.argmax(np.abs(a-a0) > 0.005)); m = t >= t[rel]+0.2
    T, A, tc = cycles(t[m], a[m])
    L = 0.2726
    th = np.degrees(np.arcsin(np.clip(A/L, -1, 1)))
    late = (th < 5) & (th > 1.5)
    res[c] = dict(T_mean_all=float(T.mean()), T_median_all=float(np.median(T)), n=len(T),
                  T_late=float(np.median(T[late])) if late.sum() else None, n_late=int(late.sum()),
                  amp_late_deg=float(np.median(th[late])) if late.sum() else None,
                  amp_last_deg=float(th[-1]))
    print(c, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in res[c].items()})
k = lambda key: np.array([v[key] for v in res.values() if v[key] is not None])
for key in ['T_mean_all', 'T_median_all', 'T_late', 'amp_late_deg']:
    x = k(key); print(f"{key}: {x.mean():.4f} +- {x.std(ddof=1)/np.sqrt(len(x)):.4f} (sd {x.std(ddof=1):.4f}, n={len(x)})")
json.dump(res, open(sys.argv[2], 'w'), indent=1)
