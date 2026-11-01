# raj-2 task 9: per-arm summary of dur_results.json (from measure_dur.py). Arm = name minus ball/seed.
# Usage: python3 -I aggregate.py dur_results.json [more_results.json ...]
import sys, json, re, numpy as np
rows = {}
for f in sys.argv[1:]: rows.update(json.load(open(f)))
arms = {}
for k, r in rows.items():
    arm = re.sub(r'_ball\d', '', re.sub(r'_s\d+\.mp4$', '', k)); arms.setdefault(arm, []).append((k, r))
def ms(x):
    x = np.array([v for v in x if v is not None and np.isfinite(v)], float)
    if len(x) == 0: return 'n=0'
    se = x.std(ddof=1) / np.sqrt(len(x)) if len(x) > 1 else float('nan')
    return f'{x.mean():.3f} ± {se:.3f} (median {np.median(x):.3f}, n={len(x)})'
for arm, L in sorted(arms.items()):
    T = L[0][1]['T']
    ok = [r for _, r in L if r['v5'].get('flag') == 'ok']
    print(f'== {arm}  T={T:.2f}s  clips={len(L)}  v5 flag ok={len(ok)}')
    print('   v5 g (flag ok):     ', ms([r['v5']['g'] for r in ok]))
    print('   v5 g (all):         ', ms([r['v5'].get('g') for _, r in L]))
    print('   realball g (all):   ', ms([r['rb'].get('g') for _, r in L]))
    print('   realball fall time: ', ms([r['rb'].get('fall_time') for _, r in L]))
    for k, r in L: print('     ', k, 'v5', r['v5'].get('g'), r['v5'].get('flag'), '| rb', r['rb'].get('g'), 'fall', r['rb'].get('fall_time'), 'onset', r['rb'].get('t0'))
