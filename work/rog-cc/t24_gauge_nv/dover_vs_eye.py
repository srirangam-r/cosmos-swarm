"""Blind check: do NVIDIA-scoreboard metrics (DOVER, VBench DD) separate the
physics artifacts that ro-1 eye-coded (#2211, eye_codes.csv) on the 84 task-24
GAUGE-eval clips? Both inputs are keyed by blind hex codes; no arm key used.
Usage: python3 dover_vs_eye.py gauge_nv.json eye_codes.csv out.json
"""
import sys, json, csv, random
import numpy as np

nv = json.load(open(sys.argv[1]))
eye = {r['clip']: r for r in csv.DictReader(open(sys.argv[2]))}
rows = []
for k, v in nv.items():
    c = k.replace('.mp4', '')
    if c not in eye:
        continue
    e = eye[c]
    rows.append(dict(code=c, fell=e['fell'], artifact=e['artifact'], end=e['end_state'],
                     fused=v['dover_fused'], tech=v['dover_technical'], aes=v['dover_aesthetic'],
                     dd_norm=v['dd_norm'], dd_bin=v['dd_binary'], reps=v.get('dover_reps', 1)))
METRICS = ['fused', 'tech', 'aes', 'dd_norm', 'dd_bin']

def auc(a, b):
    """P(metric(a) > metric(b)) + 0.5 ties (Mann-Whitney AUC)."""
    a, b = np.asarray(a), np.asarray(b)
    gt = (a[:, None] > b[None, :]).mean(); eq = (a[:, None] == b[None, :]).mean()
    return float(gt + 0.5 * eq)

def boot_ci(a, b, f, n=4000, seed=0):
    rng = np.random.default_rng(seed); a, b = np.asarray(a), np.asarray(b)
    s = [f(rng.choice(a, len(a)), rng.choice(b, len(b))) for _ in range(n)]
    return [float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))]

def compare(name, A, B):
    out = {'n_a': len(A), 'n_b': len(B)}
    for m in METRICS:
        a = [r[m] for r in A]; b = [r[m] for r in B]
        out[m] = dict(mean_a=float(np.mean(a)), mean_b=float(np.mean(b)),
                      diff=float(np.mean(a) - np.mean(b)),
                      diff_ci95=boot_ci(a, b, lambda x, y: x.mean() - y.mean()),
                      auc_a_gt_b=auc(a, b),
                      auc_ci95=boot_ci(a, b, auc))
    return out

clean = [r for r in rows if r['fell'] == 'Y' and r['artifact'] == 'none']
art = [r for r in rows if r['artifact'] not in ('none',)]
stays = [r for r in rows if r['fell'] != 'Y']
clean_rest = [r for r in clean if r['end'] == 'rest']
clean_air = [r for r in clean if r['end'] == 'air']
res = dict(n=len(rows), reps=sorted(set(r['reps'] for r in rows)),
           counts=dict(clean=len(clean), artifact=len(art), stays=len(stays)),
           clean_vs_artifact=compare('clean_vs_artifact', clean, art),
           clean_rest_vs_clean_air=compare('rest_vs_air', clean_rest, clean_air),
           per_artifact={})
for t in sorted(set(r['artifact'] for r in art)):
    g = [r for r in art if r['artifact'] == t]
    res['per_artifact'][t] = dict(n=len(g), **{m: float(np.mean([r[m] for r in g])) for m in METRICS})
res['clean_means'] = {m: float(np.mean([r[m] for r in clean])) for m in METRICS}
res['stays'] = [dict(code=r['code'], fused=r['fused'], dd_norm=r['dd_norm']) for r in stays]
res['rows'] = rows
json.dump(res, open(sys.argv[3], 'w'), indent=1)
print('n', res['n'], 'reps', res['reps'], res['counts'])
for key in ['clean_vs_artifact', 'clean_rest_vs_clean_air']:
    print('==', key, 'n', res[key]['n_a'], res[key]['n_b'])
    for m in METRICS:
        o = res[key][m]
        print(f"  {m:8s} {o['mean_a']:+.4f} vs {o['mean_b']:+.4f}  diff {o['diff']:+.4f} CI {o['diff_ci95'][0]:+.4f},{o['diff_ci95'][1]:+.4f}  AUC {o['auc_a_gt_b']:.2f} [{o['auc_ci95'][0]:.2f},{o['auc_ci95'][1]:.2f}]")
print('per artifact', json.dumps(res['per_artifact'], indent=0))
print('clean', res['clean_means'])
print('stays', res['stays'])
