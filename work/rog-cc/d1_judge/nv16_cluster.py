#!/usr/bin/env python3
"""Paired recipe-base deltas on my reps=3 DOVER/DD scores of the 16 #1616 box clips, two ways:
(a) 8 ball x seed pairs (as #1639), (b) seed clusters: average the 2 balls within each seed, n=4, t df=3 (codex-api-1 #1988).
Also the same on agy-3's reps=1 scores (5b18adb) to show where the two re-scores differ, and |DD - real| vs the real f0/mid clips.
Usage: nv16_cluster.py nv16.json AGY3_DIR REAL_JSON OUT_JSON"""
import json, sys, os, math
from statistics import mean, stdev
T95 = {3: 2.3534, 7: 1.8946}  # one-sided 95% t quantiles
mine_p, agy_dir, real_p, out_p = sys.argv[1:5]
mine = {os.path.basename(k): v for k, v in json.load(open(mine_p)).items()}
agy = {}
for f in ('scores_baseline_held.json', 'scores_recipe_midfall.json'):
    agy.update(json.load(open(f'{agy_dir}/{f}')))
real = json.load(open(real_p))
keys = ('dover_fused', 'dover_technical', 'dover_aesthetic', 'dd_norm', 'dd_binary')
def stats(d, df):
    m = mean(d); se = stdev(d) / math.sqrt(len(d)); return {'n': len(d), 'mean': m, 'se': se, 'lb95': m - T95[df] * se, 'ub95': m + T95[df] * se, 'values': d}
out = {}
for name, src in (('mine_reps3', mine), ('agy3_reps1', agy)):
    o = {}
    for k in keys:
        pairs = {(b, s): src[f'box_mid_b{b}_noneg_s{s}.mp4'][k] - src[f'box_ctrl_b{b}_noneg_s{s}.mp4'][k] for b in (1, 2) for s in (1, 2, 3, 4)}
        p8 = stats([pairs[(b, s)] for b in (1, 2) for s in (1, 2, 3, 4)], 7)
        p4 = stats([(pairs[(1, s)] + pairs[(2, s)]) / 2 for s in (1, 2, 3, 4)], 3)
        o[k] = {'base_mean': mean(src[f'box_ctrl_b{b}_noneg_s{s}.mp4'][k] for b in (1, 2) for s in (1, 2, 3, 4)),
                'rec_mean': mean(src[f'box_mid_b{b}_noneg_s{s}.mp4'][k] for b in (1, 2) for s in (1, 2, 3, 4)),
                'pairs8': p8, 'seed_clusters4': p4}
    out[name] = o
# real input control: realmid - realf0 (same 2 balls), and real level for DD distance
out['real'] = {k: {'f0_mean': mean(real[f'realball_{b}.mp4'][k] for b in (1, 2)), 'mid_mean': mean(real[f'realmid_{b}.mp4'][k] for b in (1, 2))} for k in keys}
for k in keys: out['real'][k]['mid_minus_f0'] = out['real'][k]['mid_mean'] - out['real'][k]['f0_mean']
# DD distance to real (real clips are 93 f vs Nano 189 f; real ball is at rest after ~1.5 s, so real 189 f DD would be <= this)
for k in ('dd_norm', 'dd_binary'):
    r0, rm = out['real'][k]['f0_mean'], out['real'][k]['mid_mean']
    pairs = [abs(mine[f'box_mid_b{b}_noneg_s{s}.mp4'][k] - rm) - abs(mine[f'box_ctrl_b{b}_noneg_s{s}.mp4'][k] - r0) for b in (1, 2) for s in (1, 2, 3, 4)]
    cl = [(pairs[i] + pairs[i + 4]) / 2 for i in range(4)]
    out['mine_reps3'][k]['dist_to_real_change_pairs8'] = stats(pairs, 7)
    out['mine_reps3'][k]['dist_to_real_change_seed4'] = stats(cl, 3)
json.dump(out, open(out_p, 'w'), indent=1)
for name in ('mine_reps3', 'agy3_reps1'):
    print('==', name)
    for k in keys:
        o = out[name][k]; a, b = o['pairs8'], o['seed_clusters4']
        print(f"{k:16s} base {o['base_mean']:.4f} rec {o['rec_mean']:.4f} | 8 pairs d={a['mean']:+.4f} se={a['se']:.4f} LB={a['lb95']:+.4f} | 4 seed-clusters se={b['se']:.4f} LB={b['lb95']:+.4f} vals={[round(x,4) for x in b['values']]}")
print('== real', {k: round(v['mid_minus_f0'], 4) for k, v in out['real'].items()})
for k in ('dd_norm', 'dd_binary'):
    a = out['mine_reps3'][k]['dist_to_real_change_pairs8']; b = out['mine_reps3'][k]['dist_to_real_change_seed4']
    print(f"|{k}-real| change rec-base: {a['mean']:+.3f} se8 {a['se']:.3f} UB8 {a['ub95']:+.3f} | se4 {b['se']:.3f} UB4 {b['ub95']:+.3f}")
