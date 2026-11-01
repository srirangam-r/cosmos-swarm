"""kiro-1 task 206: is Nano's slow pendulum period explained by its own swing amplitude?

A rigid pendulum's period grows with amplitude: T(a)/T0 = 2 K(sin(a/2)) / pi (K = complete elliptic integral of
the first kind, m = k^2). Anchor: the real GAUGE pend10 continuation from f93 (same camera, same rodtrack code) has
T_real = 1.170 s at its measured amplitude a_real. For a Nano clip with amplitude a, a real pendulum of the same
length would have T_pred(a) = T_real * F(a) / F(a_real). Compare with the measured T.

Inputs: rodtrack JSONs from task 191 (theta(t) series in projected image degrees, 0 = hanging) and its gate files.
Amplitude definitions (all on projected image angle; same camera for real and Nano, so projection biases are shared):
  half_p2p  = (p98 - p2) / 2 of theta
  maxside   = max(|p98 - c|, |p2 - c|), c = median-free centre from the damped fit (generous: larger amplitude)
  fit_A0    = |A| of the damped sinusoid c + A exp(-g t) cos(2 pi t/T + phi) at t = 0 (fit at the stored T)
Selection: pend10_f93 clips only (k175 pend_mid*, k185 p10f93, k191 p10f93) with fit R^2 >= 0.8. Gate PASS reported.
Usage: python3 amp.py <t191 dir> out.json
"""
import sys, json, numpy as np
from scipy.special import ellipk
from scipy.stats import spearmanr


def F(a_deg):
    a = np.radians(min(a_deg, 179.0))
    return 2 * ellipk(np.sin(a / 2) ** 2) / np.pi


def damped_fit(t, th, T):
    best = None
    for g in np.linspace(0, 1.5, 31):
        w = 2 * np.pi / T
        X = np.c_[np.ones_like(t), np.exp(-g * t) * np.cos(w * t), np.exp(-g * t) * np.sin(w * t)]
        b, *_ = np.linalg.lstsq(X, th, rcond=None)
        r = th - X @ b
        if best is None or (r @ r) < best[0]:
            best = (r @ r, g, b)
    _, g, b = best
    return dict(c=b[0], A0=float(np.hypot(b[1], b[2])), gamma=float(g))


def amps(v):
    s = v['series']; t = np.array(s['t']); th = np.array(s['theta'])
    f = damped_fit(t, th, v['T'])
    hi, lo = np.percentile(th, 98), np.percentile(th, 2)
    return dict(half_p2p=(hi - lo) / 2, maxside=max(abs(hi - f['c']), abs(lo - f['c'])), fit_A0=f['A0'],
                centre=f['c'], gamma=f['gamma'])


def main(d, out):
    D, G = {}, {}
    for f in ['nano.json', 'fresh.json', 'real.json']: D.update(json.load(open(f'{d}/{f}')))
    for f in ['gates.json', 'gates_fresh.json']: G.update(json.load(open(f'{d}/{f}')))
    real = D['real_pend10_f93']; ra = amps(real); Treal = real['T']
    rows = []
    for k, v in D.items():
        if k.startswith('real') or 'T' not in v: continue
        if not (k.startswith('k175_pend_mid') or 'p10f93' in k): continue
        if v['r2'] < 0.8: continue
        a = amps(v); r = dict(clip=k, T=v['T'], r2=v['r2'], PASS=G.get(k, {}).get('PASS'))
        for m in ['half_p2p', 'maxside', 'fit_A0']:
            r[m] = a[m]
            r['Tpred_' + m] = Treal * F(a[m]) / F(ra[m])
            r['ratio_' + m] = v['T'] / r['Tpred_' + m]
        rows.append(r)
    res = dict(real=dict(T=Treal, **ra), clips=rows, summary={})
    for sel, name in [(rows, 'all_r2ge0.8'), ([r for r in rows if r['PASS']], 'gate_PASS')]:
        T = np.array([r['T'] for r in sel]); sm = {'n': len(sel), 'raw_ratio_mean': float((T / Treal).mean()),
                                                     'raw_ratio_se': float((T / Treal).std(ddof=1) / np.sqrt(len(sel)))}
        for m in ['half_p2p', 'maxside', 'fit_A0']:
            x = np.array([r['ratio_' + m] for r in sel]); A = np.array([r[m] for r in sel])
            rho, p = spearmanr(A, T)
            sm[m] = dict(amp_mean=float(A.mean()), amp_real=float(ra[m]), ratio_mean=float(x.mean()),
                         ratio_se=float(x.std(ddof=1) / np.sqrt(len(x))), spearman_T_vs_amp=float(rho), p=float(p),
                         amp_needed_for_mean_raw_ratio=float(amp_needed(ra[m], (T / Treal).mean())))
        res['summary'][name] = sm
    json.dump(res, open(out, 'w'), indent=1)
    print(f"real: T={Treal} " + ' '.join(f"{m}={ra[m]:.1f}" for m in ['half_p2p', 'maxside', 'fit_A0']))
    for r in rows:
        print(f"{r['clip']:24s} T={r['T']:.2f} PASS={str(r['PASS']):5s} " +
              ' '.join(f"{m}={r[m]:5.1f}->Tpred {r['Tpred_' + m]:.2f} (x{r['ratio_' + m]:.2f})" for m in
                       ['half_p2p', 'maxside', 'fit_A0']))
    print(json.dumps(res['summary'], indent=1))


def amp_needed(a_real, ratio):
    target = ratio * F(a_real)
    for a in np.arange(a_real, 179.01, 0.1):
        if F(a) >= target: return a
    return 180.0


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
