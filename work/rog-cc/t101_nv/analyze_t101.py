# Paired arm - base on poornima-1 task-101 clips (names <input>_<arm>_s<seed>), DOVER reps3 + DD (tools/nv_scoreboard).
# Pairing = same input image + same seed. t(n-1) two-sided 90% CI over pairs, plus per-input means (2 clusters).
import json, sys, os, math, statistics as st
from scipy.stats import t as T
R = json.load(open(sys.argv[1]))
rows = R if isinstance(R, list) else R.get('results', list(R.values()))
by = {os.path.basename(r['clip'])[:-4]: r for r in rows}
M = ['dover_fused', 'dover_technical', 'dover_aesthetic', 'dd_norm', 'dd_binary']
key = {k: k.rsplit('_', 2) for k in by}
arms = sorted({a for _, a, _ in key.values()}); inputs = sorted({i for i, _, _ in key.values()})
out = {'arms': {}, 'paired_vs_base': {}, 'n_clips': len(by)}
for a in arms:
    ks = [k for k, (i, aa, s) in key.items() if aa == a]
    out['arms'][a] = {'n': len(ks), **{m: st.mean(by[k][m] for k in ks) for m in M}}
for a in arms:
    if a == 'base': continue
    res = {}
    pairs = sorted((i, s) for (i, aa, s) in key.values() if aa == a and f'{i}_base_{s}' in by)
    for m in M:
        d = [by[f'{i}_{a}_{s}'][m] - by[f'{i}_base_{s}'][m] for i, s in pairs]
        if len(d) < 2: continue
        mu, se = st.mean(d), st.stdev(d) / math.sqrt(len(d)); tc = T.ppf(0.95, len(d) - 1)
        res[m] = {'n_pairs': len(d), 'mean': mu, 'se': se, 'ci90': [mu - tc*se, mu + tc*se],
                  'n_pos': sum(x > 0 for x in d), 'n_neg': sum(x < 0 for x in d),
                  'by_input': {i: st.mean(x for (ii, _), x in zip(pairs, d) if ii == i) for i in inputs if any(ii == i for ii, _ in pairs)},
                  'per_pair': dict(zip([f'{i}_{s}' for i, s in pairs], d))}
    out['paired_vs_base'][a] = res
print(json.dumps(out, indent=1))
