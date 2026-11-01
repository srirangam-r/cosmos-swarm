# Task 174 readout per PREREG Addendum 3. Input: codes_blur.json (unblinded). Output: results_blur.json + stdout.
import json
from math import comb

C = json.load(open('codes_blur.json'))
S = [1, 2, 3, 4, 11, 12, 13, 14]
ARMS = ['b0', 'b05', 'b15']
KEYS = ['hover', 'fall', 'clean_fall', 'clone', 'morph', 'holder_redrawn', 'hover_strict', 'clean_strict', 'clean_lenient']
for v in C.values():  # sensitivity variants (see codes_blind.py header)
    v['hover_strict'] = int(v['hover'] and not v.get('drift_up', 0))
    v['clean_strict'] = int(v['clean_fall'] and not v.get('borderline', 0))
    v['clean_lenient'] = int(v['clean_fall'] or (v.get('borderline', 0) and v['fall']))


def g(a, s, k):
    return C[f'hrb_{a}_s{s}'][k]


def sign_p(u, d):
    n = u + d
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, i) for i in range(max(u, d), n + 1)) / 2 ** n)


res = {'totals': {}, 'paired_vs_b0': {}, 'n_per_arm': len(S)}
for a in ARMS:
    res['totals'][a] = {k: sum(g(a, s, k) for s in S) for k in KEYS}
for a in ['b05', 'b15']:
    res['paired_vs_b0'][a] = {}
    for k in ['hover', 'hover_strict', 'fall', 'clean_fall', 'clean_strict', 'clean_lenient', 'holder_redrawn']:
        u = sum(g(a, s, k) > g('b0', s, k) for s in S)
        d = sum(g(a, s, k) < g('b0', s, k) for s in S)
        res['paired_vs_b0'][a][k] = {'up': u, 'down': d, 'sign_p_two_sided': round(sign_p(u, d), 4)}
h0 = res['totals']['b0']['hover']
verdict = []
if h0 <= 2:
    verdict.append(f'UNINFORMATIVE: b0 hovers only {h0}/8 on A6000')
for a in ['b05', 'b15']:
    p = res['paired_vs_b0'][a]
    ha = res['totals'][a]['hover']
    sup = (ha <= h0 - 3 and p['hover']['up'] == 0) or (
        res['totals'][a]['clean_fall'] - res['totals']['b0']['clean_fall'] >= 3 and p['clean_fall']['down'] == 0)
    against = abs(ha - h0) <= 1
    verdict.append(f'{a}: ' + ('SUPPORT softness' if sup else 'hover within +-1 of b0' if against else 'inconclusive'))
both_against = all(abs(res['totals'][a]['hover'] - h0) <= 1 for a in ['b05', 'b15'])
res['verdict'] = verdict + (['AGAINST softness (both blur arms within +-1)'] if both_against and h0 > 2 else [])
json.dump(res, open('results_blur.json', 'w'), indent=1)
print(json.dumps(res, indent=1))
