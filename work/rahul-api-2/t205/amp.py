"""rahul-api-2 task 205: does swing amplitude explain Nano's 'slow' pendulum period?

Rules fixed BEFORE computing any amplitude (only kiro-1's published T values were known):
- Input: kiro-1's published rod-angle series theta(t) (deg, image-projected, 0 = hanging) from
  work/kiro-1/t191/{nano,fresh,real}.json; gate verdicts from gates.json / gates_fresh.json (unchanged).
- My own refit (no kiro-1 code): theta = c + A exp(-g t) cos(2 pi t/T + phi); grid T in [0.3, 5] s step 0.01,
  g in [-0.6, 1.0] step 0.05 (g<0 = growing swing allowed); linear LS for c, A cos, A sin; best SSE.
- Amplitude (primary, model-light): find turning points = local extrema of the series after removing gaps
  (a sample is a max/min if it beats every valid sample within +-T/4 of it); amplitude of each consecutive
  max/min pair = |theta_max - theta_min| / 2 (independent of the centre c and of pivot offsets);
  A_hc = median over pairs; needs >= 2 pairs, else NaN.
- Large-angle factor F(A) = (2/pi) K(m=sin^2(A/2)) (rigid physical pendulum, any mass distribution).
- Amplitude-corrected ratio R_corr = (T_nano / F(A_nano)) / (T_real / F(A_real)), same input's real continuation.
  R_corr = 1 => period fully explained by the clip's own amplitude; R_raw = T_nano / T_real.
- Sets: GATE = kiro-1 gate PASS; FIT = my refit R2 >= 0.8 (looser, includes gate fails).
- Sensitivity (most generous to the amplitude hypothesis; added after seeing primary result, same run):
  A_side = median |theta| at turning points about image vertical (captures lopsided overshoot such as s24),
  A_peak = max |theta| over the clip; R_corr_side / R_corr_peak use these for BOTH Nano and real.
- Growth: g < 0 means the swing grows (energy gain); also report A_last/A_first over turning-point pairs.
"""
import json, sys, os, numpy as np
from scipy.special import ellipk
from scipy.stats import spearmanr, t as tdist

D = sys.argv[1] if len(sys.argv) > 1 else 'work/kiro-1/t191'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'work/rahul-api-2/t205/amp_results.json'

def F(Adeg):
    if not np.isfinite(Adeg) or Adeg >= 179.9: return np.nan
    return 2 / np.pi * ellipk(np.sin(np.radians(Adeg) / 2) ** 2)

def refit(t, th):
    best = None
    for T in np.arange(0.3, 5.0001, 0.01):
        w = 2 * np.pi / T
        for g in np.arange(-0.6, 1.0001, 0.05):
            e = np.exp(-g * t)
            X = np.c_[np.ones_like(t), e * np.cos(w * t), e * np.sin(w * t)]
            beta, *_ = np.linalg.lstsq(X, th, rcond=None)
            sse = float(((X @ beta - th) ** 2).sum())
            if best is None or sse < best[0]: best = (sse, T, g, beta)
    sse, T, g, beta = best
    r2 = 1 - sse / float(((th - th.mean()) ** 2).sum())
    A0 = float(np.hypot(beta[1], beta[2]))
    return dict(T=round(float(T), 3), g=round(float(g), 3), c=float(beta[0]), A0=A0,
                A_fit_mean=float(A0 * np.mean(np.exp(-g * t))), r2=r2)

def turning(t, th, T):
    h = T / 4; ext = []
    for i in range(len(t)):
        m = np.abs(t - t[i]) <= h
        if m.sum() < 3: continue
        if th[i] >= th[m].max(): ext.append((t[i], th[i], +1))
        elif th[i] <= th[m].min(): ext.append((t[i], th[i], -1))
    # collapse runs of same sign (keep the most extreme)
    out = []
    for e in ext:
        if out and out[-1][2] == e[2]:
            if (e[1] - out[-1][1]) * e[2] > 0: out[-1] = e
        else: out.append(e)
    amps = [abs(out[k][1] - out[k + 1][1]) / 2 for k in range(len(out) - 1)]
    return out, amps

def load(fn):
    p = os.path.join(D, fn)
    return json.load(open(p)) if os.path.exists(p) else {}

nano = {**load('nano.json'), **load('fresh.json')}
gates = {**load('gates.json'), **load('gates_fresh.json')}
real = load('real.json')

res = {}
for name, d in list(real.items()) + list(nano.items()):
    s = d.get('series') or {}
    t = np.array(s.get('t', []), float); th = np.array(s.get('theta', []), float)
    ok = np.isfinite(t) & np.isfinite(th); t, th = t[ok], th[ok]
    r = dict(input='pend12' if 'p12' in name else 'pend10', kiro_T=d.get('T'), kiro_r2=d.get('r2'),
             gate_pass=gates.get(name, {}).get('PASS') if name in gates else None, n=int(len(t)))
    if len(t) < 20: res[name] = r; continue
    f = refit(t, th); r.update({'my_' + k: v for k, v in f.items()})
    ext, amps = turning(t, th, f['T'])
    r['n_turn'] = len(ext); r['amps'] = [round(a, 1) for a in amps]
    r['A_hc'] = float(np.median(amps)) if len(amps) >= 2 else float('nan')
    r['A_growth'] = float(amps[-1] / amps[0]) if len(amps) >= 2 and amps[0] > 0 else float('nan')
    r['peak_abs'] = float(np.max(np.abs(th - f['c'])))
    r['F'] = F(r['A_hc'])
    r['A_side'] = float(np.median([abs(e[1]) for e in ext])) if len(ext) >= 2 else float('nan')
    r['A_peak'] = float(np.max(np.abs(th)))
    r['turn_theta'] = [round(float(e[1]), 1) for e in ext]
    res[name] = r

def realkey(inp): return 'real_pend10_f93' if inp == 'pend10' else 'real_pend12_f101'
for name, r in res.items():
    if name.startswith('real') or 'my_T' not in r: continue
    rr = res[realkey(r['input'])]
    T = r['kiro_T'] if r['kiro_T'] else r['my_T']
    r['R_raw'] = T / rr['kiro_T']
    r['R_corr'] = (T / r['F']) / (rr['kiro_T'] / rr['F']) if np.isfinite(r['F']) else float('nan')
    for k in ('side', 'peak'):
        Fn, Fr = F(r['A_' + k]), F(rr['A_' + k])
        r['R_corr_' + k] = (T / Fn) / (rr['kiro_T'] / Fr) if np.isfinite(Fn) and np.isfinite(Fr) else float('nan')
    r['R_raw_my'] = r['my_T'] / rr['my_T']
    r['R_corr_my'] = (r['my_T'] / r['F']) / (rr['my_T'] / rr['F']) if np.isfinite(r['F']) else float('nan')

def summ(names, key):
    v = np.array([res[n][key] for n in names if np.isfinite(res[n].get(key, np.nan))])
    if len(v) == 0: return None
    lv = np.log(v); m = lv.mean(); n = len(v)
    se = lv.std(ddof=1) / np.sqrt(n) if n > 1 else np.nan
    q = tdist.ppf(0.975, n - 1) if n > 1 else np.nan
    return dict(n=n, geo=float(np.exp(m)), mean=float(v.mean()), sd=float(v.std(ddof=1)) if n > 1 else None,
                ci95_logt=[float(np.exp(m - q * se)), float(np.exp(m + q * se))] if n > 1 else None,
                values=[round(float(x), 3) for x in v])

nn = [n for n in res if not n.startswith('real') and 'my_T' in res[n]]
GATE10 = [n for n in nn if res[n]['gate_pass'] and res[n]['input'] == 'pend10']
GATE12 = [n for n in nn if res[n]['gate_pass'] and res[n]['input'] == 'pend12']
FIT = [n for n in nn if res[n]['my_r2'] >= 0.8 and np.isfinite(res[n]['A_hc'])]
FIT10 = [n for n in FIT if res[n]['input'] == 'pend10']
summary = {}
for lab, S in [('GATE_pend10', GATE10), ('GATE_pend12', GATE12), ('GATE_all', GATE10 + GATE12),
               ('FIT_r2ge0.8', FIT), ('FIT_pend10', FIT10)]:
    summary[lab] = {'clips': S, 'R_raw': summ(S, 'R_raw'), 'R_corr': summ(S, 'R_corr'),
                    'R_corr_my': summ(S, 'R_corr_my'), 'A_hc': summ(S, 'A_hc'),
                    'R_corr_side': summ(S, 'R_corr_side'), 'R_corr_peak': summ(S, 'R_corr_peak'),
                    'A_side': summ(S, 'A_side'), 'A_peak': summ(S, 'A_peak')}
    if len(S) >= 4:
        a = [res[n]['A_hc'] for n in S]; T = [res[n]['R_raw'] for n in S]
        rho, p = spearmanr(a, T); summary[lab]['spearman_Ahc_vs_Rraw'] = [float(rho), float(p)]
json.dump({'rules': __doc__, 'per_clip': res, 'summary': summary}, open(OUT, 'w'), indent=1, default=float)
print('real:', {k: (res[k]['kiro_T'], res[k]['my_T'], round(res[k]['A_hc'], 1), res[k]['amps'], round(res[k]['my_r2'], 3)) for k in real})
for n in nn:
    r = res[n]
    print(f"{n:28s} pass={str(r['gate_pass'])[:1]} T={r['kiro_T']} myT={r['my_T']:.2f} r2={r['my_r2']:.2f} g={r['my_g']:+.2f} "
          f"Ahc={r['A_hc']:.0f} amps={r['amps']} Rraw={r['R_raw']:.2f} Rcorr={r['R_corr']:.2f}")
for k, v in summary.items():
    print(k, json.dumps({kk: (vv if not isinstance(vv, dict) else {x: vv[x] for x in ('n', 'geo', 'ci95_logt')}) for kk, vv in v.items() if kk != 'clips'}))
