"""rog2 independent mocap pendulum period (replication of raj-3 msg 201a).
Method (differs from raj-3's PCA + zero crossings): 3D least-squares sphere fit -> pivot, L;
swing angle theta(t) = signed angle from the lowest direction in the best-fit swing plane;
turning points (parabolic-refined extrema of theta) -> period from same-side extrema (t[i+2]-t[i]);
compare with the exact finite-amplitude period 4*sqrt(L/g)*K(sin^2(theta0/2)) using the measured amplitude."""
import json, sys, numpy as np
from scipy.special import ellipk
G = 9.81
def sphere_fit(P):
    A = np.c_[2*P, np.ones(len(P))]; b = (P**2).sum(1)
    c, *_ = np.linalg.lstsq(A, b, rcond=None)
    ctr = c[:3]; R = np.sqrt(c[3] + ctr @ ctr); return ctr, R
def extrema(t, th):
    out = []
    for i in range(1, len(th)-1):
        if (th[i] > th[i-1] and th[i] >= th[i+1]) or (th[i] < th[i-1] and th[i] <= th[i+1]):
            y0, y1, y2 = th[i-1], th[i], th[i+1]; den = y0 - 2*y1 + y2
            dx = 0.5*(y0 - y2)/den if den != 0 else 0.0
            out.append((t[i] + dx*(t[1]-t[0]), y1 - 0.25*(y0-y2)*dx))
    return out
res = []
for k in range(1, 21):
    d = json.load(open(f'json/{k}.json')); fps = d['FPS']
    P = np.c_[d['ball']['x'], d['ball']['y'], d['ball']['z']] / 1000.0
    ok = np.isfinite(P).all(1); t = np.arange(len(P))/fps; P, t = P[ok], t[ok]
    sp = np.linalg.norm(np.diff(P, axis=0), axis=1)*fps
    rel = int(np.argmax(sp > 0.05))            # first frame moving > 5 cm/s
    Ps = P[rel:]
    ctr, L = sphere_fit(Ps)
    v = Ps - ctr
    # swing plane normal: smallest PCA of v
    _, _, Vt = np.linalg.svd(v - v.mean(0)); n = Vt[2]
    down = v.mean(0) - (v.mean(0)@n)*n; down /= np.linalg.norm(down)   # mean direction ~ bottom
    side = np.cross(n, down)
    th = np.arctan2(v@side, v@down); ts = t[rel:]
    ex = [e for e in extrema(ts, th) if abs(e[1]) > 0.02]
    # keep alternating sign extrema only
    ex2 = [ex[0]]
    for e in ex[1:]:
        if np.sign(e[1]) != np.sign(ex2[-1][1]): ex2.append(e)
        elif abs(e[1]) > abs(ex2[-1][1]): ex2[-1] = e
    te = np.array([e[0] for e in ex2]); ae = np.abs([e[1] for e in ex2])
    T = te[2:] - te[:-2]; tm = 0.5*(te[2:]+te[:-2]); amp = ae[1:-1]
    Tth = 4*np.sqrt(L/G)*ellipk(np.sin(amp/2)**2)
    T0 = 2*np.pi*np.sqrt(L/G)
    t_rel = ts[0]
    w8 = (te[2:] - t_rel) <= 8.0
    # also matched-window: ~5.5 s of swing in a Cosmos clip (see raj-3), use first 5.5 s
    w55 = (te[2:] - t_rel) <= 5.5
    r = dict(clip=k, L=L, theta0_deg=float(np.degrees(ae[0])), T0_small=T0,
             T_first=float(T[0]), T_8s=float(T[w8].mean()), T_5p5s=float(T[w55].mean()),
             T_all=float(T.mean()), T_late=float(T[-20:].mean()), amp_late_deg=float(np.degrees(amp[-20:].mean())),
             theory_ratio_8s=float((T[w8]/Tth[w8]).mean()), theory_ratio_all=float((T/Tth).mean()),
             duration=float(ts[-1]-t_rel), n_halfcycles=len(te))
    res.append(r); print({a: (round(b, 4) if isinstance(b, float) else b) for a, b in r.items()}, flush=True)
json.dump(res, open(sys.argv[1], 'w'), indent=1)
def ms(key):
    a = np.array([r[key] for r in res]); return f'{key}: {a.mean():.4f} ± {a.std(ddof=1):.4f} (sd), SE {a.std(ddof=1)/np.sqrt(len(a)):.4f}'
for kk in ['L', 'theta0_deg', 'T0_small', 'T_first', 'T_5p5s', 'T_8s', 'T_all', 'T_late', 'amp_late_deg', 'theory_ratio_8s', 'theory_ratio_all']:
    print(ms(kk))
