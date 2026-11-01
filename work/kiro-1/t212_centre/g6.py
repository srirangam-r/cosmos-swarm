"""kiro-1 task 212: does the slow period survive a swing-centred-on-vertical gate (G6)? Response to rahul-api-2 #4312.
G6 (fixed in task 212 description before computing): damped-fit centre c within TOL (10 deg) of the real continuation's
centre for the same input, AND the swing crosses the real equilibrium by >=10 deg on both sides:
p2(theta) < c_real - 10 and p98(theta) > c_real + 10. Sensitivity: TOL 5 / 15 deg.
Sets: (a) G1-G5 PASS + G6; (b) fit R^2 >= 0.8 + G6. Inputs: task-191 rodtrack series (projected image degrees).
Uncertainty: clip SE and seed-level SE (pend10 seeds 4-7 have base/n/r arms; average per seed first)."""
import json, re, sys, numpy as np
sys.path.insert(0, '../t206_amplitude'); from amp import damped_fit

D, G = {}, {}
for f in ['nano.json', 'fresh.json', 'real.json']: D.update(json.load(open(f'inputs/{f}')))
for f in ['gates.json', 'gates_fresh.json']: G.update(json.load(open(f'inputs/{f}')))

def geo(v):
    t = np.array(v['series']['t']); th = np.array(v['series']['theta'])
    c = damped_fit(t, th, v['T'])['c']
    return c, float(np.percentile(th, 2)), float(np.percentile(th, 98))

real = {'p10': D['real_pend10_f93'], 'p12': D['real_pend12_f101']}
rc = {k: geo(v) for k, v in real.items()}
rows = []
for k, v in D.items():
    if k.startswith('real') or 'T' not in v: continue
    inp = 'p12' if 'p12' in k else 'p10'
    c, lo, hi = geo(v); cr = rc[inp][0]
    seed = int(re.search(r'_s(\d+)$', k).group(1))
    rows.append(dict(clip=k, inp=inp, seed=seed, T=v['T'], ratio=v['T'] / real[inp]['T'], r2=v['r2'],
                     PASS=bool(G[k]['PASS']), centre=c, p2=lo, p98=hi, dc=c - cr,
                     cross=bool(lo < cr - 10 and hi > cr + 10)))

def summ(sel):
    if not sel: return dict(n=0)
    x = np.array([r['ratio'] for r in sel]); seeds = sorted({r['seed'] for r in sel})
    sm = np.array([np.mean([r['ratio'] for r in sel if r['seed'] == s]) for s in seeds])
    se = lambda a: float(a.std(ddof=1) / np.sqrt(len(a))) if len(a) > 1 else None
    return dict(n=len(sel), n_seeds=len(seeds), ratio_mean=float(x.mean()), clip_se=se(x),
                seed_mean=float(sm.mean()), seed_se=se(sm), min=float(x.min()), max=float(x.max()),
                n_fast=int((x < 1).sum()), clips=[r['clip'] for r in sel])

out = dict(real={k: dict(T=real[k]['T'], centre=rc[k][0], p2=rc[k][1], p98=rc[k][2]) for k in rc}, clips=rows, summary={})
for tol in [5, 10, 15]:
    for inp in ['p10', 'p12']:
        R = [r for r in rows if r['inp'] == inp]
        g6 = lambda r: abs(r['dc']) <= tol and r['cross']
        out['summary'][f'{inp}_tol{tol}'] = {
            'G1-5': summ([r for r in R if r['PASS']]),
            'G1-5+G6': summ([r for r in R if r['PASS'] and g6(r)]),
            'r2>=0.8': summ([r for r in R if r['r2'] >= 0.8]),
            'r2>=0.8+G6': summ([r for r in R if r['r2'] >= 0.8 and g6(r)]),
            'r2>=0.8, G6 fail': summ([r for r in R if r['r2'] >= 0.8 and not g6(r)])}
json.dump(out, open('results.json', 'w'), indent=1)
print('real', out['real'])
for r in sorted(rows, key=lambda r: (r['inp'], r['clip'])):
    if r['r2'] >= 0.8 or r['PASS']:
        print(f"{r['clip']:24s} T={r['T']:.2f} x{r['ratio']:.2f} r2={r['r2']:.2f} PASS={r['PASS']!s:5s} c={r['centre']:6.1f} dc={r['dc']:6.1f} p2={r['p2']:6.1f} p98={r['p98']:6.1f} cross={r['cross']}")
for k, s in out['summary'].items():
    print(k, {a: {b: (round(c, 3) if isinstance(c, float) else c) for b, c in v.items() if b != 'clips'} for a, v in s.items()})

# Exploratory (added after seeing G6 table): does tilt predict period? pend10, R^2 >= 0.8.
from scipy.stats import spearmanr
R = [r for r in rows if r['inp'] == 'p10' and r['r2'] >= 0.8]
rho, p = spearmanr([abs(r['dc']) for r in R], [r['ratio'] for r in R])
out['exploratory_spearman_absdc_vs_ratio_p10_r2ge0.8'] = dict(rho=float(rho), p=float(p), n=len(R))
json.dump(out, open('results.json', 'w'), indent=1)
print('spearman |dc| vs ratio', rho, p, len(R))
