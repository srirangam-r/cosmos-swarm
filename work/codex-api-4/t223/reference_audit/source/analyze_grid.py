#!/usr/bin/env python3
"""Task 141, clean single-stack (q8) grid: 10 seeds x 3 images x 3 prompts, every clip on q8 (same noise per seed).

Outcome y per clip: continuous (e.g. log late_motion) or binary (eye codes).
Variance shares (balanced crossed design, sums of squares):
  seed (S), image (I), prompt (P), I×P, S×I, S×P, residual (S×I×P).
  Tests: permutation of seed labels within each image×prompt cell (for S and S-interactions),
  of prompt labels within each seed×image unit (for P), 5000 draws. Seed-bootstrap 95% CI of each share.
Binary extras: Cochran's Q for seed (blocks = 9 conditions) and for prompt (blocks = 30 seed×image units);
  McNemar-style discordance between prompts within seed×image; per-seed outcome rates.
Usage: analyze_grid.py --feat feat_q8 [--codes codes_merged.csv --outcome settle] [--log] [--json out.json]
"""
import argparse, glob, json, re, csv, itertools
import numpy as np
from scipy import stats

ap = argparse.ArgumentParser()
ap.add_argument('--feat', default='feat_q8')
ap.add_argument('--codes', default=None)
ap.add_argument('--outcome', default='late_motion')
ap.add_argument('--log', action='store_true')
ap.add_argument('--perm', type=int, default=5000)
ap.add_argument('--boot', type=int, default=2000)
ap.add_argument('--json', default=None)
a = ap.parse_args()
rng = np.random.default_rng(1410)
rows = {}
for fj in glob.glob(f'{a.feat}/*.feat.json'):
    j = json.load(open(fj))
    m = re.match(r't141(?:q8)?_(\w+?)_(F|QT|N)_s(\d+)', j['name'])
    j.update(img=m.group(1), prm=m.group(2), s=int(m.group(3)))
    assert j['endpoint'].startswith('q8-'), j
    rows[j['name']] = j
if a.codes:
    for r in csv.DictReader(open(a.codes)):
        if r['name'] in rows:
            rows[r['name']].update(r)
IM = sorted({r['img'] for r in rows.values()}); PR = ['F', 'QT', 'N']; SD = sorted({r['s'] for r in rows.values()})
Y = np.full((len(SD), len(IM), len(PR)), np.nan)
for r in rows.values():
    v = r.get(a.outcome)
    if v in (None, '', 'U', 'UNCLEAR', 'NA'):
        continue
    Y[SD.index(r['s']), IM.index(r['img']), PR.index(r['prm'])] = float(v)
if a.log:
    Y = np.log(Y)
nmiss = int(np.isnan(Y).sum())
binary = set(np.unique(Y[~np.isnan(Y)])) <= {0.0, 1.0}
print(f'outcome={a.outcome} log={a.log} binary={binary} grid={Y.shape} missing={nmiss}')

def impute(Y):
    # fill missing cells by additive fit (seed + cell) so SS decomposition stays balanced; report missing count
    Z = Y.copy()
    if np.isnan(Z).any():
        for _ in range(50):
            cellm = np.nanmean(Z, axis=0, keepdims=True); seedm = np.nanmean(Z - cellm, axis=(1, 2), keepdims=True)
            fit = cellm + seedm
            Z = np.where(np.isnan(Y), fit, Y)
    return Z

def shares(Y):
    Z = impute(Y); g = Z.mean()
    mS = Z.mean(axis=(1, 2)); mI = Z.mean(axis=(0, 2)); mP = Z.mean(axis=(0, 1))
    mIP = Z.mean(axis=0); mSI = Z.mean(axis=2); mSP = Z.mean(axis=1)
    nS, nI, nP = Z.shape
    ss = {}
    ss['seed'] = nI * nP * ((mS - g) ** 2).sum()
    ss['image'] = nS * nP * ((mI - g) ** 2).sum()
    ss['prompt'] = nS * nI * ((mP - g) ** 2).sum()
    ss['image×prompt'] = nS * ((mIP - mI[:, None] - mP[None, :] + g) ** 2).sum()
    ss['seed×image'] = nP * ((mSI - mS[:, None] - mI[None, :] + g) ** 2).sum()
    ss['seed×prompt'] = nI * ((mSP - mS[:, None] - mP[None, :] + g) ** 2).sum()
    sst = ((Z - g) ** 2).sum()
    ss['residual(S×I×P)'] = sst - sum(ss.values())
    return {k: v / sst for k, v in ss.items()}, sst

obs, sst = shares(Y)
print('variance shares:', {k: round(v, 3) for k, v in obs.items()})
# permutation tests
def perm_seed(Y):
    Z = Y.copy()
    for i in range(Z.shape[1]):
        for p in range(Z.shape[2]):
            Z[:, i, p] = Z[rng.permutation(Z.shape[0]), i, p]
    return Z
def perm_prompt(Y):
    Z = Y.copy()
    for s in range(Z.shape[0]):
        for i in range(Z.shape[1]):
            Z[s, i, :] = Z[s, i, rng.permutation(Z.shape[2])]
    return Z
ns = np.array([shares(perm_seed(Y))[0]['seed'] for _ in range(a.perm)])
npm = np.array([shares(perm_prompt(Y))[0]['prompt'] for _ in range(a.perm)])
p_seed = float(((ns >= obs['seed']).sum() + 1) / (a.perm + 1)); p_prompt = float(((npm >= obs['prompt']).sum() + 1) / (a.perm + 1))
print(f"seed share {obs['seed']:.3f} (perm null mean {ns.mean():.3f}, 95th {np.percentile(ns,95):.3f}) p={p_seed:.4f}")
print(f"prompt share {obs['prompt']:.3f} (perm null mean {npm.mean():.3f}, 95th {np.percentile(npm,95):.3f}) p={p_prompt:.4f}")
# bootstrap over seeds
bs = []
for _ in range(a.boot):
    idx = rng.integers(0, Y.shape[0], Y.shape[0])
    bs.append(shares(Y[idx])[0])
ci = {k: [float(np.percentile([b[k] for b in bs], 2.5)), float(np.percentile([b[k] for b in bs], 97.5))] for k in obs}
print('seed-bootstrap 95% CI:', {k: [round(x, 3) for x in v] for k, v in ci.items()})
# seed ICC-like: correlation of seed-centred residual across conditions (mean pairwise r between conditions over seeds)
Z = impute(Y); R = Z - Z.mean(axis=0, keepdims=True)
C = R.reshape(R.shape[0], -1)
rs = [np.corrcoef(C[:, i], C[:, j])[0, 1] for i, j in itertools.combinations(range(C.shape[1]), 2) if C[:, i].std() > 0 and C[:, j].std() > 0]
print(f'mean between-condition correlation of seed residuals: {np.mean(rs):.3f} (n pairs {len(rs)})')
out = dict(outcome=a.outcome, log=a.log, binary=bool(binary), missing=nmiss, shares=obs, p_seed=p_seed, p_prompt=p_prompt,
           null_seed_mean=float(ns.mean()), null_prompt_mean=float(npm.mean()), ci=ci, mean_cond_r=float(np.mean(rs)) if rs else None,
           seeds=SD, images=IM, prompts=PR)
print('prompt means:', dict(zip(PR, np.nanmean(Y, axis=(0, 1)).round(3))), 'image means:', dict(zip(IM, np.nanmean(Y, axis=(0, 2)).round(3))))
print('per-seed means:', dict(zip(SD, np.nanmean(Y, axis=(1, 2)).round(2))))
if binary:
    def cochran(M):  # M: blocks x treatments, complete rows only
        M = M[~np.isnan(M).any(axis=1)]
        k = M.shape[1]; T = M.sum(axis=0); Ri = M.sum(axis=1); N = M.sum()
        den = k * N - (Ri ** 2).sum()
        Q = (k - 1) * (k * (T ** 2).sum() - N ** 2) / den if den > 0 else float('nan')
        return float(Q), int(k - 1), float(stats.chi2.sf(Q, k - 1)) if den > 0 else float('nan'), int(M.shape[0])
    q_seed = cochran(Y.reshape(Y.shape[0], -1).T)        # blocks = 9 conditions, treatments = seeds
    q_prompt = cochran(Y.transpose(0, 1, 2).reshape(-1, Y.shape[2]))  # blocks = seed×image, treatments = prompts
    print(f'Cochran Q seed: Q={q_seed[0]:.2f} df={q_seed[1]} p={q_seed[2]:.4g} (blocks {q_seed[3]})')
    print(f'Cochran Q prompt: Q={q_prompt[0]:.2f} df={q_prompt[1]} p={q_prompt[2]:.4g} (blocks {q_prompt[3]})')
    disc = {}
    for p1, p2 in itertools.combinations(range(3), 2):
        A = Y[:, :, p1].ravel(); B = Y[:, :, p2].ravel(); ok = ~np.isnan(A) & ~np.isnan(B)
        b = int(((A == 1) & (B == 0) & ok).sum()); c = int(((A == 0) & (B == 1) & ok).sum())
        disc[f'{PR[p1]}vs{PR[p2]}'] = dict(only_first=b, only_second=c, concordant=int(ok.sum() - b - c),
                                          p_exact=float(stats.binomtest(b, b + c).pvalue) if b + c else 1.0)
    print('prompt discordance (seed×image units):', disc)
    print('rate by prompt:', dict(zip(PR, np.nanmean(Y, axis=(0, 1)).round(3))))
    out.update(cochran_seed=q_seed, cochran_prompt=q_prompt, discordance=disc)
    print('per-seed x condition table (rows seeds; cols image|prompt):')
    for si, s in enumerate(SD):
        print(f'  s{s:<3d}', ' '.join('.' if np.isnan(v) else str(int(v)) for v in Y[si].ravel()))
if a.json:
    json.dump(out, open(a.json, 'w'), indent=1)
