"""Readout for satswap (FROZEN before any score). Fused DOVER per cell from score.py output.
Effects per clip pair: fix = nS - nn (desaturating nphys), ctrl = pS - pp (oversaturating plain), gap = nn - pp.
6-scene cluster bootstrap (20000, seed 0) of scene means.
DECISION: saturation is a contributing cause of the nphys DOVER cost iff fix > 0 AND ctrl < 0, both 95% CIs excluding 0.
'Share' = mean(fix) / -mean(gap), reported with the achieved S closure (S_nS vs S_plain, satswap_meta.json) so a partial
colour move is not read as a full one. Otherwise: saturation is ruled out at this resolution (report CIs).
usage: python3 analyze_sat.py <scores_sat.json> <satswap_meta.json> <out.json> [fixcell ctrlcell]
Blockiness test (same rule, same pp/nn): analyze_sat.py <scores with sat_*_pp/nn and blk_*_nB/pB> - <out> nB pB
(deblocking also blurs, so a non-positive nB-nn is NOT evidence against blockiness; only a positive fix plus negative ctrl counts)."""
import sys, json, re, os, numpy as np
sc_p, meta_p, outp = sys.argv[1:4]
FX, CT = (sys.argv[4], sys.argv[5]) if len(sys.argv) > 5 else ('nS', 'pS')
S = json.load(open(sc_p)); M = json.load(open(meta_p)) if meta_p != '-' else None
def fused(v):
    for k in ('dover_fused', 'fused', 'dover'):
        if isinstance(v, dict) and k in v: return v[k] if not isinstance(v[k], dict) else v[k].get('fused')
    raise KeyError(list(v)[:10])
cell = {}
for name, v in S.items():
    m = re.search(r'(?:sat|blk)_(\d+)_(s\d)_(pp|nn|nS|pS|nB|pB)', name)
    if m: cell[(m[1] + '_' + m[2], m[3])] = fused(v)
keys = sorted({k for k, _ in cell}); scenes = sorted({k.split('_')[0] for k in keys})
D = {e: {k: f(k) for k in keys} for e, f in dict(
    gap=lambda k: cell[(k, 'nn')] - cell[(k, 'pp')], fix=lambda k: cell[(k, FX)] - cell[(k, 'nn')],
    ctrl=lambda k: cell[(k, CT)] - cell[(k, 'pp')], nS_pp=lambda k: cell[(k, FX)] - cell[(k, 'pp')]).items()}
rng = np.random.default_rng(0)
def boot(d):
    sm = np.array([np.mean([d[k] for k in keys if k.startswith(s + '_')]) for s in scenes])
    b = sm[rng.integers(0, len(sm), (20000, len(sm)))].mean(1)
    return dict(mean=float(np.mean(list(d.values()))), lo=float(np.percentile(b, 2.5)), hi=float(np.percentile(b, 97.5)),
                n_pos=int(sum(v > 0 for v in d.values())), n=len(d))
R = {e: boot(d) for e, d in D.items()}
clos = float(np.mean([(M[k]['S_nphys'] - M[k]['S_nS']) / (M[k]['S_nphys'] - M[k]['S_plain']) for k in keys])) if M else None
R['S_closure_fraction'] = clos
R['share_of_gap'] = R['fix']['mean'] / -R['gap']['mean']
R['decision'] = f'{FX} effect contributes' if (R['fix']['lo'] > 0 and R['ctrl']['hi'] < 0) else 'not shown'
R['per_clip'] = {k: {e: D[e][k] for e in D} for k in keys}
json.dump(R, open(outp, 'w'), indent=1)
for e in ('gap', 'fix', 'ctrl', 'nS_pp'): print(e, {k: round(v, 4) if isinstance(v, float) else v for k, v in R[e].items()})
print('S closure', clos, 'share', round(R['share_of_gap'], 2), '->', R['decision'])
