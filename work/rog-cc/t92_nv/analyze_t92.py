# Paired fast05 - base on poornima-1 task 92 clips (b1dd33/b3dd35 x s1-3), DOVER reps3 + DD (tools/nv_scoreboard).
# Pairing = same input image + same seed. SE over the 6 pairs (t, df=5) and a 2-cluster (input) view.
import json, sys, os, math, statistics as st
R = json.load(open(sys.argv[1])); real = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
rows = R if isinstance(R, list) else R.get('results', list(R.values()))
by = {os.path.basename(r['clip'])[:-4]: r for r in rows}
M = ['dover_fused', 'dover_technical', 'dover_aesthetic', 'dd_norm', 'dd_binary']
T5 = 2.015  # t(0.95, df=5) -> two-sided 90% CI
out = {'arms': {}, 'paired_fast05_minus_base': {}, 'per_pair': {}, 'real_ref_t0_windows': {}}
for arm in ['base', 'fast05']:
    out['arms'][arm] = {m: st.mean(by[f'{i}_{arm}_s{s}'][m] for i in ['b1dd33', 'b3dd35'] for s in (1, 2, 3)) for m in M}
for m in M:
    d = [by[f'{i}_fast05_s{s}'][m] - by[f'{i}_base_s{s}'][m] for i in ['b1dd33', 'b3dd35'] for s in (1, 2, 3)]
    mu, se = st.mean(d), st.stdev(d) / math.sqrt(len(d))
    byin = {i: st.mean(d[k*3:(k+1)*3]) for k, i in enumerate(['b1dd33', 'b3dd35'])}
    out['paired_fast05_minus_base'][m] = {'n_pairs': len(d), 'mean': mu, 'se': se, 'ci90': [mu - T5*se, mu + T5*se],
                                         'n_pos': sum(x > 0 for x in d), 'n_neg': sum(x < 0 for x in d), 'by_input': byin, 'per_pair': d}
for k, v in real.items():
    out['real_ref_t0_windows'][k] = {m: v[m] for m in M}
print(json.dumps(out, indent=1))
