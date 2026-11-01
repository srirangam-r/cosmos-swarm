#!/usr/bin/env python3
"""Task 202: Independent seedshare replication & statistical audit of Task 141 q8 grid (#4181).

Applies poornima-3's seedshare methodology (eta2_seed, eta2_cond, conc_excess, permutation tests)
to the Task 141 clean single-stack (q8) grid from codes_named.csv:
10 seeds x 3 real GAUGE mid-fall frames x 3 prompts (F, QT, N).

Tests:
1. Full 9-condition grid (img x prompt): condition = (img, prm)
2. Prompt conditions (F, QT, N): condition = prm
3. Within-prompt image replication: condition = img, evaluated separately for QT, F, N
4. Pairwise prompt contrasts (F vs QT, QT vs N, F vs N)
5. Full 3-way ANOVA variance decomposition, Cochran's Q, and exact discordances.
"""

import os
import sys
import csv
import json
import random
import re
import itertools
from collections import defaultdict
import numpy as np
from scipy import stats

RNG_SEED = 20261101
R = random.Random(RNG_SEED)
np_rng = np.random.default_rng(RNG_SEED)
NPERM = int(os.environ.get("NPERM", 20000))

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CSV_PATH = os.path.join(DATA_DIR, "codes_named.csv")

def load_data():
    rows = []
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        for r in reader:
            # parse name: t141q8_b1dd33_F_s1
            parts = r['name'].split('_')
            img = parts[1]
            prm = parts[2]
            s = int(parts[3][1:])
            
            def parse_val(v):
                if v in (None, '', 'U', 'UNCLEAR', 'NA'):
                    return None
                return int(v)

            rows.append({
                'id': r['id'],
                'name': r['name'],
                'coder': r['coder'],
                'img': img,
                'prm': prm,
                's': s,
                'end_state': r['end_state'],
                'settle': parse_val(r['settle']),
                'clone01': parse_val(r['clone01']),
                'retether01': parse_val(r['retether01']),
                'vanish01': parse_val(r['vanish01']),
                'note': r.get('note', '') or '',
            })
    return rows

def build_grid(rows, outcome, cond_fn):
    """Returns dict of cond -> dict of seed -> outcome (skipping missing)."""
    g = defaultdict(dict)
    for r in rows:
        y = r[outcome]
        if y is not None:
            g[cond_fn(r)][r['s']] = int(y)
    return g

def conc_excess(g):
    same = [0, 0] # [matches, total]
    diff = [0, 0]
    conds = sorted(g.keys())
    for c1, c2 in itertools.combinations(conds, 2):
        for s1, y1 in g[c1].items():
            for s2, y2 in g[c2].items():
                tgt = same if s1 == s2 else diff
                tgt[0] += int(y1 == y2)
                tgt[1] += 1
    if same[1] == 0 or diff[1] == 0:
        return None, same, diff
    return same[0] / same[1] - diff[0] / diff[1], same, diff

def eta2(g):
    cells = [(c, s, y) for c, d in g.items() for s, y in d.items()]
    n = len(cells)
    if n == 0:
        return None, None
    mu = sum(y for *_, y in cells) / n
    sst = sum((y - mu) ** 2 for *_, y in cells)
    if sst == 0:
        return None, None
    bys = defaultdict(list)
    byc = defaultdict(list)
    for c, s, y in cells:
        bys[s].append(y)
        byc[c].append(y)
    ss_s = sum(len(v) * (sum(v) / len(v) - mu) ** 2 for v in bys.values())
    ss_c = sum(len(v) * (sum(v) / len(v) - mu) ** 2 for v in byc.values())
    return ss_s / sst, ss_c / sst

def perm_test(g, nperm=NPERM):
    ex, same, diff = conc_excess(g)
    if ex is None:
        return None, None, None
    cells = [(c, s, y) for c, d in g.items() for s, y in d.items()]
    ge = 0
    null_excesses = []
    null_eta_seeds = []
    
    # Pre-extract conditions and seeds
    cond_items = [(c, list(d.keys()), [d[s] for s in d.keys()]) for c, d in g.items()]
    
    for _ in range(nperm):
        h = {}
        for c, seeds, ys in cond_items:
            shuffled_ys = ys.copy()
            R.shuffle(shuffled_ys)
            h[c] = dict(zip(seeds, shuffled_ys))
        e, _, _ = conc_excess(h)
        null_excesses.append(e)
        s_eta, _ = eta2(h)
        if s_eta is not None:
            null_eta_seeds.append(s_eta)
        if e >= ex - 1e-12:
            ge += 1
            
    p_val = (ge + 1) / (nperm + 1)
    null_mean = float(np.mean(null_excesses))
    null_eta_mean = float(np.mean(null_eta_seeds)) if null_eta_seeds else None
    return p_val, null_mean, null_eta_mean

def run_seedshare_analysis(name, rows, outcome, cond_fn, note=""):
    g = build_grid(rows, outcome, cond_fn)
    n_cells = sum(len(d) for d in g.values())
    all_ys = [y for d in g.values() for y in d.values()]
    rate = float(np.mean(all_ys)) if all_ys else None
    
    e_seed, e_cond = eta2(g)
    ex, same, diff = conc_excess(g)
    p_perm, null_ex_mean, null_eta_mean = perm_test(g)
    
    res = {
        'analysis': name,
        'outcome': outcome,
        'n_cells': n_cells,
        'rate': round(rate, 4) if rate is not None else None,
        'agree_same_seed': f"{same[0]}/{same[1]}" if same[1] else "0/0",
        'agree_diff_seed': f"{diff[0]}/{diff[1]}" if diff[1] else "0/0",
        'p_agree_same': round(same[0]/same[1], 4) if same[1] else None,
        'p_agree_diff': round(diff[0]/diff[1], 4) if diff[1] else None,
        'conc_excess': round(ex, 4) if ex is not None else None,
        'perm_p_one_sided': round(p_perm, 5) if p_perm is not None else None,
        'null_excess_mean': round(null_ex_mean, 4) if null_ex_mean is not None else None,
        'eta2_seed': round(e_seed, 4) if e_seed is not None else None,
        'eta2_seed_null_mean': round(null_eta_mean, 4) if null_eta_mean is not None else None,
        'eta2_cond': round(e_cond, 4) if e_cond is not None else None,
        'note': note
    }
    return res

def run_anova_decomposition(rows, outcome):
    """Replicates 3-way balanced ANOVA variance decomposition."""
    IM = sorted(list({r['img'] for r in rows}))
    PR = ['F', 'QT', 'N']
    SD = sorted(list({r['s'] for r in rows}))
    Y = np.full((len(SD), len(IM), len(PR)), np.nan)
    for r in rows:
        v = r[outcome]
        if v is not None:
            Y[SD.index(r['s']), IM.index(r['img']), PR.index(r['prm'])] = float(v)
            
    nmiss = int(np.isnan(Y).sum())
    
    # Impute missing cells iteratively
    Z = Y.copy()
    if np.isnan(Z).any():
        for _ in range(50):
            cellm = np.nanmean(Z, axis=0, keepdims=True)
            seedm = np.nanmean(Z - cellm, axis=(1, 2), keepdims=True)
            fit = cellm + seedm
            Z = np.where(np.isnan(Y), fit, Y)
            
    g = Z.mean()
    mS = Z.mean(axis=(1, 2))
    mI = Z.mean(axis=(0, 2))
    mP = Z.mean(axis=(0, 1))
    mIP = Z.mean(axis=0)
    mSI = Z.mean(axis=2)
    mSP = Z.mean(axis=1)
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
    shares = {k: v / sst for k, v in ss.items()}
    
    # Discordance between prompts within seed x image
    discordance = {}
    for (p1_idx, p1), (p2_idx, p2) in itertools.combinations(enumerate(PR), 2):
        pairs = []
        for s in range(nS):
            for i in range(nI):
                y1 = Y[s, i, p1_idx]
                y2 = Y[s, i, p2_idx]
                if not np.isnan(y1) and not np.isnan(y2):
                    pairs.append((int(y1), int(y2)))
        only_first = sum(1 for a, b in pairs if a == 1 and b == 0)
        only_second = sum(1 for a, b in pairs if a == 0 and b == 1)
        concordant = sum(1 for a, b in pairs if a == b)
        # McNemar exact sign test
        n_disc = only_first + only_second
        p_exact = 2 * stats.binom.cdf(min(only_first, only_second), n_disc, 0.5) if n_disc > 0 else 1.0
        discordance[f"{p1}vs{p2}"] = {
            'only_first': only_first,
            'only_second': only_second,
            'concordant': concordant,
            'p_exact': min(1.0, float(p_exact))
        }
        
    return {
        'outcome': outcome,
        'missing': nmiss,
        'shares': shares,
        'discordance': discordance
    }

def run_seed_cluster_analysis(rows, outcome_name, nboot=20000, nperm=20000):
    seeds = sorted({r['s'] for r in rows})
    images = sorted({r['img'] for r in rows})
    prompts = ['F', 'QT', 'N']
    
    Y = np.full((len(seeds), len(images), len(prompts)), np.nan)
    for r in rows:
        v = r[outcome_name]
        if v is not None:
            Y[seeds.index(r['s']), images.index(r['img']), prompts.index(r['prm'])] = float(v)
            
    res = {'outcome': outcome_name, 'seeds': seeds, 'images': images, 'contrasts': {}}
    
    # Contrasts: (F, QT -> QT-F), (N, QT -> QT-N), (N, F -> F-N)
    for p1, p2, cname in [('F', 'QT', 'QT-F'), ('N', 'QT', 'QT-N'), ('N', 'F', 'F-N')]:
        i1 = prompts.index(p1)
        i2 = prompts.index(p2)
        D = Y[:, :, i2] - Y[:, :, i1]
        d = np.nanmean(D, axis=1) # per-seed mean difference across available images
        ok = ~np.isnan(d)
        d_ok = d[ok]
        
        pos = int(np.sum(d_ok > 0))
        neg = int(np.sum(d_ok < 0))
        zero = int(np.sum(d_ok == 0))
        
        # Exact two-sided sign test
        n_nz = pos + neg
        if n_nz > 0:
            p_sign = 2 * float(stats.binom.cdf(min(pos, neg), n_nz, 0.5))
            p_sign = min(p_sign, 1.0)
        else:
            p_sign = 1.0
            
        # Exact sign-flip test over all non-zero seeds
        obs_mean = float(np.mean(d_ok))
        diffs = d_ok[d_ok != 0]
        if len(diffs) > 0:
            flips = np.array(list(itertools.product([-1, 1], repeat=len(diffs))))
            flip_means = (flips @ np.abs(diffs)) / len(d_ok)
            p_flip = float(np.mean(np.abs(flip_means) >= np.abs(obs_mean) - 1e-9))
        else:
            p_flip = 1.0
            
        # Seed-cluster bootstrap 95% CI
        rng = np.random.default_rng(RNG_SEED)
        boot_diffs = []
        for _ in range(nboot):
            s_idx = rng.choice(len(seeds), size=len(seeds), replace=True)
            r1 = np.nanmean(Y[s_idx, :, i1])
            r2 = np.nanmean(Y[s_idx, :, i2])
            boot_diffs.append(float(r2 - r1))
        ci95 = [float(x) for x in np.percentile(boot_diffs, [2.5, 97.5])]
        
        rate1 = float(np.nanmean(Y[:, :, i1]))
        rate2 = float(np.nanmean(Y[:, :, i2]))
        
        res['contrasts'][cname] = {
            'rate_first': rate1,
            'rate_second': rate2,
            'diff': float(rate2 - rate1),
            'boot95': ci95,
            'per_seed': [round(float(x), 3) for x in d],
            'seeds_pos': pos,
            'seeds_neg': neg,
            'seeds_zero': zero,
            'p_sign_exact': p_sign,
            'p_signflip_exact': p_flip
        }
        
    # Prompt variance share permuted WITHIN SEED (one permutation shared by all images of each seed)
    def impute(arr):
        Z = arr.copy()
        if np.isnan(Z).any():
            for _ in range(50):
                cellm = np.nanmean(Z, axis=0, keepdims=True)
                seedm = np.nanmean(Z - cellm, axis=(1, 2), keepdims=True)
                Z = np.where(np.isnan(arr), cellm + seedm, arr)
        return Z

    def prompt_share(arr):
        Z = impute(arr)
        g = Z.mean()
        mP = Z.mean(axis=(0, 1))
        return Z.shape[0] * Z.shape[1] * float(((mP - g) ** 2).sum()) / float(((Z - g) ** 2).sum())

    obs_ps = prompt_share(Y)
    rng = np.random.default_rng(RNG_SEED)
    null_ps = []
    for _ in range(nperm):
        Z_p = Y.copy()
        for s in range(Z_p.shape[0]):
            Z_p[s] = Z_p[s][:, rng.permutation(3)]
        null_ps.append(prompt_share(Z_p))
    null_ps = np.array(null_ps)
    p_perm = float(((null_ps >= obs_ps - 1e-12).sum() + 1) / (nperm + 1))
    
    res['prompt_share_within_seed'] = {
        'obs': float(obs_ps),
        'null_mean': float(null_ps.mean()),
        'null95': float(np.percentile(null_ps, 95)),
        'p_cluster_perm': p_perm
    }
    return res

def main():
    rows = load_data()
    print(f"Loaded {len(rows)} clips from {CSV_PATH}")
    
    results = []
    
    # 1. Full 9-condition grid: condition = (img, prm)
    print("\n--- 1. FULL 9-CONDITION GRID (img x prm) ---")
    for o in ('settle', 'retether01', 'clone01', 'vanish01'):
        r = run_seedshare_analysis("t141 q8 grid: seed x (img x prompt)", rows, o, lambda x: f"{x['img']}_{x['prm']}")
        results.append(r)
        print(f"Outcome: {o:12s} | Rate={r['rate']} | Eta2_seed={r['eta2_seed']} (null {r['eta2_seed_null_mean']}) | Eta2_cond={r['eta2_cond']} | Conc_excess={r['conc_excess']} (p={r['perm_p_one_sided']})")

    # 2. Prompt condition only (3 conditions: F, QT, N): image ignored / pooled
    print("\n--- 2. PROMPT CONDITION ONLY (F vs QT vs N) ---")
    for o in ('settle', 'retether01', 'clone01'):
        r = run_seedshare_analysis("t141 q8: seed x prompt (pooled images)", rows, o, lambda x: f"{x['prm']}")
        results.append(r)
        print(f"Outcome: {o:12s} | Rate={r['rate']} | Eta2_seed={r['eta2_seed']} | Eta2_cond={r['eta2_cond']} | Conc_excess={r['conc_excess']} (p={r['perm_p_one_sided']})")

    # 3. Within-prompt image replication (condition = img)
    print("\n--- 3. WITHIN-PROMPT IMAGE REPLICATION ---")
    for prm in ('QT', 'F', 'N'):
        prm_rows = [x for x in rows if x['prm'] == prm]
        for o in ('settle', 'retether01', 'clone01'):
            r = run_seedshare_analysis(f"t141 q8 [{prm} arm]: seed x image (b1dd33/b2dd35/b2dd37)", prm_rows, o, lambda x: f"{x['img']}")
            results.append(r)
            print(f"Prompt: {prm:2s} | Outcome: {o:12s} | Rate={r['rate']} | Eta2_seed={r['eta2_seed']} | Conc_excess={r['conc_excess']} (p={r['perm_p_one_sided']})")

    # 4. Pairwise prompt contrasts at matched image
    print("\n--- 4. PAIRWISE PROMPT CONTRASTS (matched img) ---")
    for (p1, p2) in (('F', 'QT'), ('QT', 'N'), ('F', 'N')):
        pair_rows = [x for x in rows if x['prm'] in (p1, p2)]
        for o in ('settle', 'retether01'):
            # condition = (img, prm)
            r = run_seedshare_analysis(f"t141 q8 contrast {p1} vs {p2}: seed x ({p1}/{p2} x img)", pair_rows, o, lambda x: f"{x['img']}_{x['prm']}")
            results.append(r)
            print(f"Contrast: {p1} vs {p2:2s} | Outcome: {o:12s} | Eta2_cond={r['eta2_cond']} | Eta2_seed={r['eta2_seed']} | Conc_excess={r['conc_excess']} (p={r['perm_p_one_sided']})")

    # 5. ANOVA & Discordance Verification
    print("\n--- 5. ANOVA DECOMPOSITION & DISCORDANCE VERIFICATION ---")
    anova_res = {}
    for o in ('settle', 'retether01', 'clone01', 'vanish01'):
        a = run_anova_decomposition(rows, o)
        anova_res[o] = a
        print(f"Outcome: {o:12s} | Shares: { {k: round(v, 4) for k, v in a['shares'].items()} }")
        if 'discordance' in a:
            print(f"  Discordances: {a['discordance']}")

    # 6. Seed-Level Cluster Inference & Post-Hoc Growth Sensitivity (Review #4268 Response)
    print("\n--- 6. SEED-LEVEL CLUSTER INFERENCE & ROBUSTNESS ---")
    patt_growth = re.compile(r'grow|grew|enlarg|giant|swell|huge size', re.I)
    rows_with_growth = []
    for r in rows:
        r_c = dict(r)
        note = r.get('note', '') or ''
        has_growth = 1 if patt_growth.search(note) else 0
        r_c['growth'] = has_growth
        # clean_settle: 1 if settle==1 and no growth note; 0 if settle==0 or growth; None if settle is None
        s_val = r['settle']
        if s_val is None:
            r_c['clean_settle'] = None
        elif s_val == 1 and not has_growth:
            r_c['clean_settle'] = 1
        elif s_val == 0 or has_growth:
            r_c['clean_settle'] = 0
        else:
            r_c['clean_settle'] = None
        rows_with_growth.append(r_c)

    cluster_res = {}
    for o in ('settle', 'clean_settle'):
        c = run_seed_cluster_analysis(rows_with_growth, o, nboot=NPERM, nperm=NPERM)
        cluster_res[o] = c
        print(f"Cluster Inference for {o.upper()}:")
        for cname, cdata in c['contrasts'].items():
            print(f"  {cname}: diff={cdata['diff']:+.4f} (boot95 [{cdata['boot95'][0]:.4f}, {cdata['boot95'][1]:.4f}]), "
                  f"seeds +{cdata['seeds_pos']}/-{cdata['seeds_neg']}/0:{cdata['seeds_zero']}, "
                  f"sign p={cdata['p_sign_exact']:.5f}, sign-flip p={cdata['p_signflip_exact']:.5f}")
        ps = c['prompt_share_within_seed']
        print(f"  Prompt share within-seed: obs={ps['obs']:.4f}, null_mean={ps['null_mean']:.4f}, 95th={ps['null95']:.4f}, perm_p={ps['p_cluster_perm']:.5f}")

    output_payload = {
        'seedshare_analyses': results,
        'anova_decomposition': anova_res,
        'cluster_inference': cluster_res
    }
    
    out_json = os.path.join(os.path.dirname(__file__), "t202_seedshare_audit_results.json")
    with open(out_json, "w") as f:
        json.dump(output_payload, f, indent=2)
    print(f"\nSaved full results to {out_json}")

if __name__ == '__main__':
    main()
