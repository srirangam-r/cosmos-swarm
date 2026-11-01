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

    output_payload = {
        'seedshare_analyses': results,
        'anova_decomposition': anova_res
    }
    
    out_json = os.path.join(os.path.dirname(__file__), "t202_seedshare_audit_results.json")
    with open(out_json, "w") as f:
        json.dump(output_payload, f, indent=2)
    print(f"\nSaved full results to {out_json}")

if __name__ == '__main__':
    main()
