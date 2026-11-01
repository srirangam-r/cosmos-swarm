"""Per-latent-frame variance of E7's temporal mixes when donor slot 0 := fresh slot 0 (shared source), vs independent slot 0.
Exact (linear algebra, unit-variance iid donor and fresh) + Monte Carlo check. Mirrors run_e7.py tmask/mixT (9dd4fc8) and latent.py d66b830."""
import json, sys
import numpy as np
T = 24
def tmask(kmin, kmax):
    k = np.abs(np.fft.fftfreq(T) * T); return ((k >= kmin - 1e-9) & (k <= kmax + 1e-9)).astype(float)
def mixmat(kmin, kmax):
    # x = H donor + (I-H) fresh, H = circulant real projection
    M = tmask(kmin, kmax); F = np.fft.fft(np.eye(T), axis=0); H = (np.fft.ifft(M[:, None] * F, axis=0)).real
    return H
out = {}
for name, (a, b) in {"tlo_fix |k|<=3": (0, 3), "low |k|<=6": (0, 6), "osc 3<=|k|<=6": (3, 6)}.items():
    H = mixmat(a, b); G = np.eye(T) - H
    # shared: donor = D with D[0] := f[0]  -> x = H S d + (H e0 e0^T + G) f, S = I - e0 e0^T
    S = np.eye(T); S[0, 0] = 0; E = np.zeros((T, T)); E[0, 0] = 1
    A_d, A_f = H @ S, H @ E + G
    v_shared = (A_d**2).sum(1) + (A_f**2).sum(1)
    # independent replacement: donor slot0 is a separate N(0,1)
    v_indep = (H**2).sum(1) + (G**2).sum(1)
    # MC check
    rng = np.random.default_rng(0); n = 200000
    d = rng.standard_normal((n, T)); f = rng.standard_normal((n, T)); d[:, 0] = f[:, 0]
    x = d @ H.T + f @ G.T
    out[name] = dict(var_shared=[round(v, 6) for v in v_shared], var_indep=[round(v, 6) for v in v_indep],
                     mc_shared=[round(v, 4) for v in x.var(0)], min_shared_frames_1_23=round(float(v_shared[1:].min()), 6),
                     frames_below_0p97=[int(i) for i in np.where(v_shared < 0.97)[0] if i > 0])
json.dump(out, sys.stdout, indent=1)
