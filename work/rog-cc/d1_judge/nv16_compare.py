#!/usr/bin/env python3
"""Independent DOVER/DD re-score of the 16 #1616 box clips (my install, dover_reps=3) vs agy-3's scores (5b18adb, reps=1).
Usage: nv16_compare.py nv16.json AGY3_DIR OUTDIR
(1) per-clip agreement (my - agy3) for each metric; (2) re-runs the #1639 paired analysis (rev1616.py) on MY scores."""
import json, sys, os, math, subprocess
from statistics import mean, stdev
mine_p, agy_dir, outdir = sys.argv[1:4]
os.makedirs(outdir, exist_ok=True)
mine = json.load(open(mine_p))
mine = {os.path.basename(k): v for k, v in mine.items()}
agy = {}
for f in ('scores_baseline_held.json', 'scores_recipe_midfall.json'):
    agy.update(json.load(open(f'{agy_dir}/{f}')))
keys = ('dover_fused', 'dover_technical', 'dover_aesthetic', 'dd_norm', 'dd_binary')
out = {'n_clips_mine': len(mine), 'per_clip': {}, 'agreement': {}}
for c in sorted(mine):
    if c not in agy: print('not in agy3:', c, file=sys.stderr); continue
    out['per_clip'][c] = {k: {'mine': mine[c][k], 'agy3': agy[c][k], 'mine_rep_sd': mine[c].get(k + '_sd')} for k in keys}
for k in keys:
    d = [v[k]['mine'] - v[k]['agy3'] for v in out['per_clip'].values()]
    a = [v[k]['agy3'] for v in out['per_clip'].values()]; m = [v[k]['mine'] for v in out['per_clip'].values()]
    ma, mm = mean(a), mean(m)
    cov = sum((x - ma) * (y - mm) for x, y in zip(a, m)); r = cov / math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mm) ** 2 for y in m)) if len(set(a)) > 1 and len(set(m)) > 1 else None
    out['agreement'][k] = {'n': len(d), 'mean_diff': mean(d), 'sd_diff': stdev(d), 'max_abs_diff': max(abs(x) for x in d), 'pearson_r': r}
# split my scores into rev1616.py's expected layout and re-run the paired analysis on them
split = {'scores_baseline_held.json': {c: v for c, v in mine.items() if c.startswith('box_ctrl')},
         'scores_recipe_midfall.json': {c: v for c, v in mine.items() if c.startswith('box_mid')}}
for f, v in split.items(): json.dump(v, open(f'{outdir}/{f}', 'w'), indent=1)
rev = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rev1616', 'rev1616.py')
subprocess.run([sys.executable, rev, os.path.abspath(outdir)], cwd=outdir, check=True, stdout=subprocess.DEVNULL)
out['paired_on_my_scores'] = json.load(open(f'{outdir}/rev1616.json'))
json.dump(out, open(f'{outdir}/nv16_compare.json', 'w'), indent=1, default=list)
print(json.dumps(out['agreement'], indent=1))
for k in keys:
    p = out['paired_on_my_scores'][k]
    print(k, 'base %.4f rec %.4f delta %.4f se %.4f LB %.4f per_ball %s n_neg %d' % (p['base_mean'], p['rec_mean'], p['delta'], p['se'], p['lb95_one_sided'], [round(x, 4) for x in p['per_ball_delta']], p['n_neg']))
print('MF triplets:', json.dumps({k: v for k, v in out['paired_on_my_scores']['mf_triplets'].items() if k != 'agy3_triplet'}, default=list))
