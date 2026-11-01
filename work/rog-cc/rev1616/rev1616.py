#!/usr/bin/env python3
"""Independent re-analysis of agy-3 #1616 (task 68) from its per-clip score JSONs (commit 5b18adb).
No re-scoring of video: clips live on agy-3's machine. Recomputes (1) the MF/MC algebra with all 4 seeds
(every 3-of-4 seed triplet), (2) DOVER/DD paired stats with t one-sided bounds and ball-clustered view."""
import json, itertools, sys, math
from statistics import mean, stdev
from scipy import stats
D = sys.argv[1] if len(sys.argv) > 1 else '../../agy-3/task68_nv_scoreboard'
base = json.load(open(f'{D}/scores_baseline_held.json'))
rec = json.load(open(f'{D}/scores_recipe_midfall.json'))
ref = {'ball_1': 0, 'ball_2': 0}  # reference_dd from mf_baseline.json (raj-4 real ball_1/2 dd_binary = 0)
def get(d, arm, b, s, k): return d[f'box_{arm}_b{b}_noneg_s{s}.mp4'][k]
out = {}
# 1) MF/MC exactly as tools/nv_scoreboard/motion_fidelity.py (ddof=0, zero policy), over all triplets
def mf_for(dd_by_ball):
    mcs, dds = [], []
    for b, dd in dd_by_ball.items():
        avg = mean(dd); var = sum((x-avg)**2 for x in dd)/3; den = var+avg**2
        mcs.append(var/den if den else 0.0); dds.append(avg)
    dd_gen = mean(dds); mc = mean(mcs)
    return (1-abs(dd_gen-0))*(1-mc), mc, dd_gen
rows = []
for t1 in itertools.combinations([1,2,3,4], 3):
    for t2 in itertools.combinations([1,2,3,4], 3):
        r = {}
        for arm, d in (('ctrl', base), ('mid', rec)):
            r[arm] = mf_for({1: [get(d, arm, 1, s, 'dd_binary') for s in t1], 2: [get(d, arm, 2, s, 'dd_binary') for s in t2]})
        rows.append({'t1': t1, 't2': t2, 'mf_base': r['ctrl'][0], 'mf_rec': r['mid'][0], 'mc_base': r['ctrl'][1], 'mc_rec': r['mid'][1]})
dmf = [x['mf_rec']-x['mf_base'] for x in rows]
out['dd_binary_per_clip'] = {arm: {b: [get(d, arm, b, s, 'dd_binary') for s in (1,2,3,4)] for b in (1,2)} for arm, d in (('ctrl', base), ('mid', rec))}
out['mf_triplets'] = {'n': len(rows), 'mf_base_range': [min(x['mf_base'] for x in rows), max(x['mf_base'] for x in rows)],
    'mf_rec_range': [min(x['mf_rec'] for x in rows), max(x['mf_rec'] for x in rows)],
    'dmf_range': [min(dmf), max(dmf)], 'dmf_mean': mean(dmf), 'frac_dmf_le0': sum(v <= 0 for v in dmf)/len(dmf),
    'mc_base_range': [min(x['mc_base'] for x in rows), max(x['mc_base'] for x in rows)],
    'mc_rec_range': [min(x['mc_rec'] for x in rows), max(x['mc_rec'] for x in rows)], 'frac_mc_rec_gt_base': sum(x['mc_rec'] > x['mc_base'] for x in rows)/len(rows), 'frac_mc_rec_ge_base': sum(x['mc_rec'] >= x['mc_base'] for x in rows)/len(rows),
    'agy3_triplet': [r for r in rows if r['t1'] == (1,2,3) and r['t2'] == (1,2,3)][0]}
# 2) paired stats for continuous metrics
for k in ('dover_fused', 'dover_technical', 'dover_aesthetic', 'dd_norm', 'dd_binary'):
    d = [get(rec, 'mid', b, s, k) - get(base, 'ctrl', b, s, k) for b in (1,2) for s in (1,2,3,4)]
    n = len(d); m = mean(d); se = stdev(d)/math.sqrt(n); tq = stats.t.ppf(0.95, n-1)
    per_ball = [mean(d[:4]), mean(d[4:])]
    out[k] = {'base_mean': mean(get(base, 'ctrl', b, s, k) for b in (1,2) for s in (1,2,3,4)),
              'rec_mean': mean(get(rec, 'mid', b, s, k) for b in (1,2) for s in (1,2,3,4)),
              'delta': m, 'se': se, 'lb95_one_sided': m - tq*se, 'ub95_one_sided': m + tq*se,
              'per_ball_delta': per_ball, 'n_neg': sum(v < 0 for v in d)}
json.dump(out, open('rev1616.json', 'w'), indent=1, default=list)
print(json.dumps({k: v for k, v in out.items() if k != 'mf_triplets'}, indent=1, default=list))
print(json.dumps(out['mf_triplets'], indent=1, default=list))
