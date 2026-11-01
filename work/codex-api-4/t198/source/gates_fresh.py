import json, numpy as np
R = json.load(open('real.json')); N = json.load(open('fresh.json'))
def Lcurve(s):
    th, L = np.array(s['theta']), np.array(s['L']); bins = np.arange(-20, 85, 5); c = []
    for a in bins:
        m = (th >= a - 5) & (th < a + 5); c.append(np.median(L[m]) if m.sum() else np.nan)
    return bins, np.array(c)
rows = {}
for name, r in N.items():
    ref = R['real_pend12_f101' if 'p12f101' in name else 'real_pend10_f93']
    b, c = Lcurve(ref['series']); ok = ~np.isnan(c)
    th, L = np.array(r['series']['theta']), np.array(r['series']['L']); m = (th >= -20) & (th <= 80)
    dev = float(np.median(np.abs(L[m] - np.interp(th[m], b[ok], c[ok])) / np.interp(th[m], b[ok], c[ok]))) if m.sum() else 9
    g = dict(G1=r['pivot_resid_px'] < 3, G2=float(np.hypot(r['pivot'][0] - 326, r['pivot'][1] - 118)) < 15, G3=dev < 0.2,
             G4=r['valid_frac'] >= 0.6, G5=r.get('r2', 0) >= 0.8)
    rows[name] = dict(T=r.get('T'), ci95=r.get('ci95'), r2=r.get('r2'), Ldev=dev, **g, PASS=all(g.values()))
    print(f"{name:24s} T={r.get('T') or 0:.2f} r2={r.get('r2') or 0:.2f} Ldev={dev:.2f} " + ' '.join(k for k, v in g.items() if not v), 'PASS' if all(g.values()) else '')
json.dump(rows, open('gates_fresh.json', 'w'), indent=1, default=lambda x: bool(x) if isinstance(x, np.bool_) else float(x))
