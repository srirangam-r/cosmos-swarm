"""Task 262 (rahul-api-2): does a stretched rod predict a slow pendulum? Confirmatory test of the t213 post hoc lead
(Spearman(Ldev, T) +0.47, n=23, unsigned) on FRESH pend10 clips with a SIGNED stretch. Frozen before any rodtrack
output of the E3 clips was read (see PREREG.md).

Inputs (all existing, no generation):
  rodtrack (kiro-1 t191, sha256 1740e8ec..., unchanged) series per clip: t262/rt/E3_pend10.json (+ pend11/14 secondary),
  t226/rt_P.json (t226 P arms, 24 clips, run in shift 9).
  measure_pend v1 periods: t257/meas.json (E3) and t226/p_meas.json (t226 P).
  real reference: kiro-1 t191 real.json 'real_pend10_f93' (rodtrack on the real GAUGE continuation).
Usage: python analyze262.py selftest | python analyze262.py run <out.json>
"""
import sys, json, math, numpy as np

BASE = '/home/sha/swarm-work/rahul-api-2/'
REAL = BASE + 'cosmos-swarm/work/kiro-1/t191/real.json'
T_REAL = 1.1735501872474754          # pend10 mocap period (codex-api-4 references.json, as in t257 e3seed.py)
PIV = (326, 118)                      # pend10 pivot used by kiro-1 gates_fresh G2
RNG = np.random.default_rng(262)


def lcurve(series):                   # copied from kiro-1 gates_fresh.py (theta-binned median rod length)
    th, L = np.array(series['theta']), np.array(series['L']); bins = np.arange(-20, 85, 5); c = []
    for a in bins:
        m = (th >= a - 5) & (th < a + 5); c.append(np.median(L[m]) if m.sum() else np.nan)
    return bins, np.array(c)


def stretch(series, ref):
    b, c = ref; ok = ~np.isnan(c)
    th, L = np.array(series['theta']), np.array(series['L']); m = (th >= -20) & (th <= 80)
    if m.sum() == 0: return None, None, 0
    r = L[m] / np.interp(th[m], b[ok], c[ok]) - 1
    return float(np.median(r)), float(np.median(np.abs(r))), int(m.sum())   # signed S, unsigned Ldev (= kiro-1 G3), n frames


def rows():
    ref = lcurve(json.load(open(REAL))['real_pend10_f93']['series'])
    out = []
    srcs = [('E3', BASE + 't262/rt/E3_pend10.json', BASE + 't257/meas.json'),
            ('E3s', BASE + 't262/rt/E3_pend11.json', BASE + 't257/meas.json'),
            ('E3s', BASE + 't262/rt/E3_pend14.json', BASE + 't257/meas.json'),
            ('t226', BASE + 't226/rt_P.json', BASE + 't226/p_meas.json')]
    for src, rtf, mf in srcs:
        rt = json.load(open(rtf)); meas = {m['clip'].replace('.mp4', ''): m for m in json.load(open(mf))}
        for name, r in rt.items():
            m = meas[name]; p = m['pend']; S, Ldev, n_in = stretch(r['series'], ref)
            seed = int(name.rsplit('_s', 1)[1])
            out.append(dict(clip=name, src=src, seed=seed, inp=(name.split('_')[2] if src.startswith('E3') else 'pend10'),
                            arm=(name.split('_')[2] if src == 't226' else 'E3base'),
                            S=S, Ldev=Ldev, n_in=n_in, valid_frac=r['valid_frac'], pivot_resid=r['pivot_resid_px'],
                            pivot_d=float(math.hypot(r['pivot'][0] - PIV[0], r['pivot'][1] - PIV[1])),
                            T_mp=p.get('period_s'), flag=p.get('flag'), T_rt=r.get('T'), r2_rt=r.get('r2')))
    return out


def eligible(r, period='mp'):
    if r['S'] is None or r['valid_frac'] < 0.6 or r['n_in'] < 10 or r['S'] <= -0.9: return False
    if period == 'mp': return r['flag'] == 'ok' and r['T_mp']
    return (r['r2_rt'] or 0) >= 0.8 and r['T_rt']


def spearman(x, y):
    rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
    return float(np.corrcoef(rx, ry)[0, 1]) if len(x) > 2 else float('nan')


def test(R, period='mp', nperm=10000, nboot=2000):
    R = [r for r in R if eligible(r, period)]
    n = len(R)
    if n < 3: return dict(n=n)
    T = np.array([r['T_mp'] if period == 'mp' else r['T_rt'] for r in R])
    y = np.log(T / T_REAL); S = np.array([r['S'] for r in R]); x = np.log1p(S)
    src = np.array([r['src'] for r in R]); clus = np.array([f"{r['src']}_{r['seed']}" for r in R])
    rho = spearman(S, y)
    # within-source permutation, one-sided (rho > 0)
    cnt = 0
    for _ in range(nperm):
        Sp = S.copy()
        for s in set(src):
            i = np.where(src == s)[0]; Sp[i] = S[RNG.permutation(i)]
        cnt += spearman(Sp, y) >= rho - 1e-12
    p = (cnt + 1) / (nperm + 1)
    slope = float(np.polyfit(x, y, 1)[0]) if np.ptp(x) > 0 else float('nan')
    # cluster bootstrap over (source, seed)
    U = sorted(set(clus)); br, bs = [], []
    for _ in range(nboot):
        pick = RNG.choice(U, len(U)); idx = np.concatenate([np.where(clus == u)[0] for u in pick])
        if np.ptp(x[idx]) > 0 and len(set(S[idx])) > 2:
            br.append(spearman(S[idx], y[idx])); bs.append(np.polyfit(x[idx], y[idx], 1)[0])
    unexpl = np.exp(y - 0.5 * x)                     # T / (T_real * sqrt(1+S)): slowness left after the length correction
    return dict(n=n, n_clusters=len(U), rho=rho, p_one_sided=p,
                rho_ci95=[float(np.percentile(br, 2.5)), float(np.percentile(br, 97.5))] if br else None,
                slope_logT_on_log1pS=slope, slope_ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))] if bs else None,
                pendulum_prediction_slope=0.5,
                ratio_T_real_median=float(np.exp(np.median(y))), ratio_after_length_corr_median=float(np.median(unexpl)),
                S_median=float(np.median(S)), S_iqr=[float(np.percentile(S, 25)), float(np.percentile(S, 75))],
                decision=('INCONCLUSIVE (n<8)' if n < 8 else ('SUPPORTED' if (rho > 0 and p <= 0.05) else 'NOT DETECTED')),
                clips=[dict(clip=r['clip'], S=round(r['S'], 3), T=round(float(t), 3)) for r, t in zip(R, T)])


def fisher_2x2(a, b, c, d):                         # one-sided P(X >= a), hypergeometric
    from math import comb
    n1, n2, k = a + b, c + d, a + c; tot = comb(n1 + n2, k)
    return sum(comb(n1, i) * comb(n2, k - i) for i in range(a, min(n1, k) + 1)) / tot


def run(out):
    R = rows()
    p10 = [r for r in R if r['src'] in ('E3', 't226')]
    res = dict(PRIMARY=test(p10, 'mp'),
               SEC_rodtrack_period=test(p10, 'rt'),
               SEC_E3_only=test([r for r in p10 if r['src'] == 'E3'], 'mp'),
               SEC_t226_only=test([r for r in p10 if r['src'] == 't226'], 'mp'),
               SEC_pend11_14_pivot_ok=test([r for r in R if r['src'] == 'E3s' and r['pivot_d'] < 15], 'mp'))
    # descriptive verifier table: real-speed (+-20%) vs kiro-1 G3 (Ldev < 0.2) among ok pend10 clips
    ok = [r for r in p10 if eligible(r, 'mp')]
    rs = [abs(math.log(r['T_mp'] / T_REAL)) <= math.log(1.2) for r in ok]; g3 = [r['Ldev'] < 0.2 for r in ok]
    a = sum(1 for x, g in zip(rs, g3) if x and g); b = sum(1 for x, g in zip(rs, g3) if x and not g)
    c = sum(1 for x, g in zip(rs, g3) if not x and g); d = sum(1 for x, g in zip(rs, g3) if not x and not g)
    res['SEC_verifier_G3'] = dict(realspeed_G3pass=a, realspeed_G3fail=b, slow_or_fast_G3pass=c, slow_or_fast_G3fail=d,
                                  p_one_sided_fisher=fisher_2x2(a, c, b, d) if ok else None,
                                  note='rows: G3 pass/fail; outcome real-speed; G3 uses the REAL clip L(theta) curve, so it is a diagnostic, not a first-frame-only verifier')
    res['all_rows'] = R
    json.dump(res, open(out, 'w'), indent=1)
    for k, v in res.items():
        if k != 'all_rows': print(k, {a: b for a, b in v.items() if a != 'clips'})


def selftest():
    ser = json.load(open(REAL))['real_pend10_f93']['series']; ref = lcurve(ser)
    for k in (1.0, 1.3, 0.8):
        s2 = dict(theta=ser['theta'], L=[l * k for l in ser['L']]); S, Ld, n = stretch(s2, ref)
        print(f'scale {k}: S {S:+.3f} (expect {k - 1:+.2f}) Ldev {Ld:.3f} n {n}')
        assert abs(S - (k - 1)) < 0.03
    # synthetic pendulums: T = T_real*sqrt(1+S) exactly -> slope 0.5, ratio_after_corr 1
    R = [dict(clip=f'x{i}', src='E3', seed=i, S=s, Ldev=abs(s), n_in=50, valid_frac=1, flag='ok', T_mp=T_REAL * math.sqrt(1 + s),
              T_rt=None, r2_rt=None) for i, s in enumerate(np.linspace(-0.3, 0.8, 12))]
    t = test(R, 'mp', nperm=2000, nboot=200); print({k: v for k, v in t.items() if k != 'clips'})
    assert abs(t['slope_logT_on_log1pS'] - 0.5) < 1e-6 and abs(t['ratio_after_length_corr_median'] - 1) < 1e-6 and t['p_one_sided'] < 0.01
    R2 = [dict(r, T_mp=T_REAL * 1.7 * math.exp(RNG.normal(0, 0.2))) for r in R]   # null: slow but unrelated to S
    t2 = test(R2, 'mp', nperm=2000, nboot=200); print('null', {k: v for k, v in t2.items() if k != 'clips'})
    print('SELFTEST OK')


if __name__ == '__main__':
    selftest() if sys.argv[1] == 'selftest' else run(sys.argv[2])
