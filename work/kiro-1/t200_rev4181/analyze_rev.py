# kiro-1 independent analysis of task-141 settle outcome with my frozen codes (mycodes.csv)
import csv, json, re, random
from collections import Counter, defaultdict
from scipy.stats import binomtest, chi2
key = json.load(open('blind_key.json'))
mine = {r['id']: r for r in csv.DictReader(open('mycodes.csv'))}
theirs = {r['id']: r for r in csv.DictReader(open('codes_merged.csv'))}
def s(e): return None if e == 'UNCLEAR' else int(e == 'REST')
rows = []
for i, name in key.items():
    m = re.match(r't141q8_(\w+)_(F|QT|N)_s(\d+)', name)
    rows.append(dict(id=i, img=m.group(1), p=m.group(2), seed=int(m.group(3)),
                     me=s(mine[i]['end_state']), them=s(theirs[i]['end_state']),
                     me5=mine[i]['end_state'], them5=theirs[i]['end_state']))
out = {}
# agreement
both = [r for r in rows if r['me'] is not None and r['them'] is not None]
a = sum(r['me'] == r['them'] for r in both); n = len(both)
po = a / n; p1 = sum(r['me'] for r in both) / n; p2 = sum(r['them'] for r in both) / n
pe = p1 * p2 + (1 - p1) * (1 - p2); kappa = (po - pe) / (1 - pe)
out['settle_agreement'] = dict(n=n, agree=a, kappa=round(kappa, 3))
out['five_class_agree'] = sum(r['me5'] == r['them5'] for r in rows)
out['disagreements'] = [(r['id'], key[r['id']], r['me5'], r['them5']) for r in rows if r['me5'] != r['them5']]
# rates per prompt, my codes
for who in ('me', 'them'):
    out[f'rate_{who}'] = {p: f"{sum(r[who] for r in rows if r['p']==p and r[who] is not None)}/{sum(1 for r in rows if r['p']==p and r[who] is not None)}" for p in ('F','QT','N')}
# F vs QT discordance, my codes, paired by (seed,img)
cell = {(r['seed'], r['img'], r['p']): r['me'] for r in rows}
up = down = 0
for sd in range(1, 11):
    for im in {r['img'] for r in rows}:
        f, q = cell.get((sd, im, 'F')), cell.get((sd, im, 'QT'))
        if f is None or q is None: continue
        if f == 0 and q == 1: up += 1
        if f == 1 and q == 0: down += 1
out['F_vs_QT_me'] = dict(F0_QT1=up, F1_QT0=down, p_exact=binomtest(up, up + down).pvalue if up + down else None)
# per-seed settle counts (my codes)
out['per_seed_me'] = {sd: f"{sum(r['me'] for r in rows if r['seed']==sd and r['me'] is not None)}/{sum(1 for r in rows if r['seed']==sd and r['me'] is not None)}" for sd in range(1, 11)}
out['per_seed_QT_me'] = {sd: f"{sum(r['me'] for r in rows if r['seed']==sd and r['p']=='QT' and r['me'] is not None)}/{sum(1 for r in rows if r['seed']==sd and r['p']=='QT' and r['me'] is not None)}" for sd in range(1, 11)}
# Cochran Q for seed: blocks = 9 (img,prompt) conditions complete across 10 seeds
conds = sorted({(r['img'], r['p']) for r in rows})
X = []
for c in conds:
    v = [cell.get((sd, c[0], c[1])) for sd in range(1, 11)]
    if None not in v: X.append(v)
k = 10; b = len(X)
Cj = [sum(x[j] for x in X) for j in range(k)]; Ri = [sum(x) for x in X]; N = sum(Ri)
Q = (k - 1) * (k * sum(c * c for c in Cj) - N * N) / (k * N - sum(r * r for r in Ri))
out['cochranQ_seed_me'] = dict(blocks=b, Q=round(Q, 2), df=k - 1, p=float(chi2.sf(Q, k - 1)))
# seed effect within QT controlled for prompt: permutation of seed labels within (img,prompt) blocks, stat = var of seed totals
def stat(M): 
    t = [sum(x[j] for x in M) for j in range(k)]; mu = sum(t) / k
    return sum((v - mu) ** 2 for v in t)
obs = stat(X); random.seed(1); ge = 0
for _ in range(5000):
    P = [random.sample(x, k) for x in X]
    ge += stat(P) >= obs
out['seed_perm_p_me'] = (ge + 1) / 5001
json.dump(out, open('rev_results.json', 'w'), indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
