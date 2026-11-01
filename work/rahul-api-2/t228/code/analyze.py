"""Task 228 analysis, as fixed in PREREG.md (d347353).

usage: analyze.py rodtrack_out.json real.json input_rodlen.json out.json
rodtrack_out.json keys: rpr_p10f93_base_s<seed> (orig) and r220_p10f93_<arm>_s<seed>.
"""
import json
import re
import sys

import numpy as np

rt_fn, real_fn, inlen_fn, out_fn = sys.argv[1:5]
RT = json.load(open(rt_fn))
REAL = json.load(open(real_fn))['real_pend10_f93']
INL = json.load(open(inlen_fn))
SCALE = {'orig': 1.0, 'L70': INL['L70']['scale_vs_orig'], 'L50': INL['L50']['scale_vs_orig']}
FRAC = {'orig': 1.0, 'L70': 0.7, 'L50': 0.5}
IN_TAN = {'orig': INL['orig']['L_tan_px'], 'L70': INL['L70']['L_tan_px'], 'L50': INL['L50']['L_tan_px']}
BOB_OFF = 131.856 - INL['orig']['L_tan_px']     # PREREG: 20.1 px
T_REAL = 1.170


def Lcurve(s):
    th, L = np.array(s['theta']), np.array(s['L'])
    bins = np.arange(-20, 85, 5)
    c = [np.median(L[(th >= a - 5) & (th < a + 5)]) if ((th >= a - 5) & (th < a + 5)).sum() else np.nan for a in bins]
    return bins, np.array(c)


rb, rc = Lcurve(REAL['series'])
ok = ~np.isnan(rc)
rows = {}
for name, r in RT.items():
    if name.startswith('rpr_p10f93_base_s'):
        arm, seed = 'orig', int(name.split('_s')[-1])
    else:
        m = re.match(r'r220_p10f93_(L\d+)_s(\d+)', name)
        if not m:
            continue
        arm, seed = m.group(1), int(m.group(2))
    th, L = np.array(r['series']['theta']), np.array(r['series']['L'])
    sel = (th >= -20) & (th <= 80)
    ref = np.interp(th[sel], rb[ok], rc[ok]) * SCALE[arm]
    dev = float(np.median(np.abs(L[sel] - ref) / ref)) if sel.sum() else 9.0
    g = dict(G1=r['pivot_resid_px'] < 3, G2=float(np.hypot(r['pivot'][0] - 326, r['pivot'][1] - 118)) < 15, G3=dev < 0.2,
             G4=r['valid_frac'] >= 0.6, G5=(r.get('r2') or 0) >= 0.8)
    Lmed = r.get('L_med')
    rows[name] = dict(arm=arm, seed=seed, T=r.get('T'), r2=r.get('r2'), ci95=r.get('ci95'), Ldev=dev,
                      L_med=Lmed, L_med_over_input=(Lmed / IN_TAN[arm]) if Lmed else None,
                      L_med_over_orig_input=(Lmed / IN_TAN['orig']) if Lmed else None,
                      regrown=bool(Lmed and Lmed >= 0.9 * IN_TAN['orig'] and arm != 'orig'),
                      **{k: bool(v) for k, v in g.items()}, PASS=bool(all(g.values())))

rng = np.random.default_rng(228)


def gm(x):
    return float(np.exp(np.mean(np.log(x))))


def arm_ratio(sel_key, arm, nb=20000):
    a = np.array([v['T'] for v in rows.values() if v['arm'] == arm and v[sel_key] and v['T']])
    o = np.array([v['T'] for v in rows.values() if v['arm'] == 'orig' and v[sel_key] and v['T']])
    if len(a) < 2 or len(o) < 2:
        return dict(n_arm=len(a), n_orig=len(o), ratio=None)
    R = gm(a) / gm(o)
    bs = [gm(rng.choice(a, len(a))) / gm(rng.choice(o, len(o))) for _ in range(nb)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return dict(n_arm=len(a), n_orig=len(o), gm_arm=gm(a), gm_orig=gm(o), ratio=R, ci95=[float(lo), float(hi)],
                law_pred=float(np.sqrt(FRAC[arm])), T_arm=a.tolist(), T_orig=o.tolist(),
                nano_over_real_arm=gm(a) / (T_REAL * np.sqrt(FRAC[arm])), nano_over_real_orig=gm(o) / T_REAL)


def decide(res):
    if res.get('ratio') is None:
        return 'insufficient PASS clips'
    lo, hi = res['ci95']
    if hi < 0.84:
        return 'period shortens with length' + (' (CI includes law 0.707)' if lo <= 0.707 <= hi else ' (CI excludes law 0.707)')
    if lo > 0.84:
        return 'template-like (insensitive to length)'
    return 'inconclusive'


out = dict(rows=rows, bob_offset_px=BOB_OFF)
for key in ('PASS', 'G5'):
    out[f'primary_{key}'] = {arm: arm_ratio(key, arm) for arm in ('L70', 'L50')}
out['decision_L50'] = decide(out['primary_PASS']['L50'])
out['decision_L50_G5only'] = decide(out['primary_G5']['L50'])

# (a) seed-paired
paired = {}
for arm in ('L70', 'L50'):
    pr = []
    for s in range(21, 31):
        a = [v for v in rows.values() if v['arm'] == arm and v['seed'] == s]
        o = [v for v in rows.values() if v['arm'] == 'orig' and v['seed'] == s]
        if a and o and a[0]['PASS'] and o[0]['PASS']:
            pr.append(dict(seed=s, log_ratio=float(np.log(a[0]['T'] / o[0]['T']))))
    paired[arm] = dict(pairs=pr, n=len(pr), n_neg=sum(p['log_ratio'] < 0 for p in pr),
                       gm_ratio=float(np.exp(np.mean([p['log_ratio'] for p in pr]))) if pr else None)
out['paired'] = paired

# (b) slope of log T on log L_eff over PASS clips, seed-cluster bootstrap
P = [v for v in rows.values() if v['PASS'] and v['T'] and v['L_med']]
if len(P) >= 4:
    x = np.log(np.array([v['L_med'] + BOB_OFF for v in P])); y = np.log(np.array([v['T'] for v in P]))
    seeds = np.array([v['seed'] for v in P])
    slope = float(np.polyfit(x, y, 1)[0])
    us = np.unique(seeds); bs = []
    for _ in range(5000):
        pick = rng.choice(us, len(us))
        idx = np.concatenate([np.nonzero(seeds == s)[0] for s in pick])
        if np.ptp(x[idx]) > 0.05:
            bs.append(np.polyfit(x[idx], y[idx], 1)[0])
    out['slope_logT_logL'] = dict(n=len(P), slope=slope, ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
json.dump(out, open(out_fn, 'w'), indent=1)
for k in ('primary_PASS', 'primary_G5'):
    for arm, v in out[k].items():
        print(k, arm, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk not in ('T_arm', 'T_orig')})
print('decision L50:', out['decision_L50'], '| G5-only:', out['decision_L50_G5only'])
print('paired:', {a: (p['n'], p['n_neg'], p['gm_ratio']) for a, p in paired.items()})
print('slope:', out.get('slope_logT_logL'))
for n, v in sorted(rows.items(), key=lambda kv: (kv[1]['arm'], kv[1]['seed'])):
    print(f"{v['arm']:4s} s{v['seed']} T={v['T'] or 0:.2f} r2={v['r2'] or 0:.2f} Ldev={v['Ldev']:.2f} Lmed/in={v['L_med_over_input'] or 0:.2f} "
          + ' '.join(k for k in ('G1', 'G2', 'G3', 'G4', 'G5') if not v[k]) + (' PASS' if v['PASS'] else ''))
