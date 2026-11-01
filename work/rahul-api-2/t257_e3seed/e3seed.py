"""Task 257 (rahul-api-2): does a seed's pendulum period carry across real pendulum frames? Frozen BEFORE any E3 clip
was fetched (see PREREG.md). Data: Raj's Program N E3 clips N_E3_{pend10,pend11,pend14}_s601..624 (q8, noise cpu).

  measure: measure_pend v1 (tools/trk_ballfall, planted PASS at 2e26463), UNCHANGED: trk.load(path) -> mp.measure(F, 24.0,
           tol=3.0, nboot=200, seed=0). Period usable iff flag == 'ok' (primary) ; sensitivity gate = 'relaxed'
           (t226_pend Amendment 2: ok rule with >= 40% tracked frames instead of 90%).
  analyze: Q1 primary  ICC(1) (PhysWeep SDI, eq. A1, one-way random effects, unbalanced n0) of log T on usable clips,
                       after subtracting each input's mean log T (removes the input main effect); seeds with >= 2 usable
                       inputs only. Null: permute seed labels within each input (10000 perms, rng 0) -> one-sided p.
                       Seed-bootstrap 95% CI (2000 resamples). Also Spearman of log T for each input pair.
           Q2 secondary seed bank (Good Seed protocol): rank the 24 seeds on pend10 (train) by |log(T/T_ref)| among
                       usable clips (unusable = worst, ties by ascending seed); top-6 bank. Held-out success per clip on
                       pend11/pend14 = usable AND 0.8 <= T/T_ref <= 1.2. Bank rate vs the rate of all 24 seeds; p = share
                       of all C(24,6) random 6-banks with held-out rate >= the top bank's (exact enumeration).
Usage: python -I e3seed.py measure CLIPDIR OUT.json ; python -I e3seed.py analyze OUT.json RESULT.json
       python -I e3seed.py selftest
"""
import sys, os, re, json, glob, itertools, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..', 'tools', 'trk_ballfall')))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', 't226_pend')))

# mocap crossing periods over each input's nominal 93-frame continuation (codex-api-4 references.json, task8 traces)
T_REF = {'pend10': 1.1735501872474754, 'pend11': 1.176302428, 'pend14': 1.174375575}
INPUTS = ('pend10', 'pend11', 'pend14')
SEEDS = list(range(601, 625))
NAME = re.compile(r'N_E3_(pend1[014])_s(\d+)')


def measure(clipdir, out):
    import trk, measure_pend as mp
    from readout import relaxed_ok
    rows = []
    for p in sorted(glob.glob(os.path.join(clipdir, 'N_E3_*.mp4'))):
        m = NAME.search(os.path.basename(p))
        if not m:
            continue
        r = dict(clip=os.path.basename(p), input=m.group(1), seed=int(m.group(2)))
        try:
            F = trk.load(p)
            q = mp.measure(F, 24.0, tol=3.0, nboot=200, seed=0)
            q.pop('track', None)
            r['pend'] = q
            r['relaxed'] = bool(relaxed_ok(q))
        except Exception as e:
            r['pend'] = dict(flag='fail', error=repr(e)[:200], period_s=float('nan'))
            r['relaxed'] = False
        rows.append(r)
        print(r['clip'], r['pend'].get('flag'), r['pend'].get('period_s'), flush=True)
    json.dump(rows, open(out, 'w'), indent=1, default=float)


def table(rows, gate):
    T = {}
    for r in rows:
        p = r['pend']; ok = p.get('flag') == 'ok' if gate == 'ok' else r.get('relaxed', False)
        t = p.get('period_s', float('nan'))
        if ok and t is not None and np.isfinite(t) and t > 0:
            T[(r['input'], r['seed'])] = math.log(t)
    return T


def icc1(groups):
    """One-way random-effects ICC(1) with unbalanced n0 (PhysWeep eq. A1), clipped to [0, 1]."""
    groups = [np.asarray(g, float) for g in groups if len(g) >= 2]
    k = len(groups); N = sum(len(g) for g in groups)
    if k < 2 or N - k < 1:
        return float('nan')
    grand = np.concatenate(groups).mean()
    msb = sum(len(g) * (g.mean() - grand) ** 2 for g in groups) / (k - 1)
    msw = sum(((g - g.mean()) ** 2).sum() for g in groups) / (N - k)
    n0 = (N - sum(len(g) ** 2 for g in groups) / N) / (k - 1)
    den = msb + (n0 - 1) * msw
    return float(np.clip((msb - msw) / den, 0, 1)) if den > 0 else float('nan')


def centred_groups(T):
    mu = {i: np.mean([v for (ii, s), v in T.items() if ii == i]) for i in INPUTS if any(ii == i for ii, _ in T)}
    by = {}
    for (i, s), v in T.items():
        by.setdefault(s, []).append(v - mu[i])
    return {s: g for s, g in by.items() if len(g) >= 2}


def q1(T, nperm=10000, nboot=2000):
    G = centred_groups(T)
    obs = icc1(list(G.values()))
    out = dict(n_seeds_ge2=len(G), n_clips=sum(len(g) for g in G.values()), icc1=obs)
    if len(G) < 2 or not np.isfinite(obs):
        return out
    rng = np.random.default_rng(0)
    cnt = 0
    keys = list(T)
    for _ in range(nperm):
        Tp = {}
        for i in INPUTS:
            ks = [k for k in keys if k[0] == i]
            vals = [T[k] for k in ks]
            perm = rng.permutation(len(ks))
            for k, j in zip(ks, perm):
                Tp[k] = vals[j]
        cnt += icc1(list(centred_groups(Tp).values())) >= obs
    out['perm_p'] = (cnt + 1) / (nperm + 1)
    seeds = list(G); bs = []
    for _ in range(nboot):
        pick = rng.choice(len(seeds), len(seeds), replace=True)
        bs.append(icc1([G[seeds[j]] for j in pick]))
    bs = np.array([b for b in bs if np.isfinite(b)])
    out['boot_ci95'] = [float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))] if len(bs) else None
    from scipy.stats import spearmanr
    out['spearman'] = {}
    for a, b in itertools.combinations(INPUTS, 2):
        ss = [s for s in SEEDS if (a, s) in T and (b, s) in T]
        if len(ss) >= 4:
            rho, p = spearmanr([T[(a, s)] for s in ss], [T[(b, s)] for s in ss])
            out['spearman'][f'{a}:{b}'] = dict(n=len(ss), rho=float(rho), p=float(p))
        else:
            out['spearman'][f'{a}:{b}'] = dict(n=len(ss))
    if out['n_seeds_ge2'] < 8:
        out['decision'] = 'INCONCLUSIVE (fewer than 8 seeds with >= 2 usable inputs)'
    elif obs >= 0.3 and out['perm_p'] <= 0.05:
        out['decision'] = 'CARRIES'
    elif out['perm_p'] > 0.05 and out['boot_ci95'] and out['boot_ci95'][1] < 0.3:
        out['decision'] = 'DOES NOT CARRY'
    else:
        out['decision'] = 'INCONCLUSIVE'
    return out


def q2(T, bank=6):
    def err(s):
        k = ('pend10', s)
        return abs(T[k] - math.log(T_REF['pend10'])) if k in T else float('inf')
    rank = sorted(SEEDS, key=lambda s: (err(s), s))
    top = rank[:bank]

    def succ(s, i):
        k = (i, s)
        return k in T and 0.8 <= math.exp(T[k]) / T_REF[i] <= 1.2
    per_seed = {s: sum(succ(s, i) for i in ('pend11', 'pend14')) for s in SEEDS}
    rate = lambda ss: sum(per_seed[s] for s in ss) / (2 * len(ss))
    r_top = rate(top); r_all = rate(SEEDS)
    combos = list(itertools.combinations(SEEDS, bank))
    ge = sum(rate(c) >= r_top - 1e-12 for c in combos)
    return dict(train_rank=rank, top_bank=top, n_train_usable=sum(('pend10', s) in T for s in SEEDS),
                heldout_rate_top=r_top, heldout_rate_all=r_all, exact_p=ge / len(combos), n_banks=len(combos),
                train_success_rate_all=sum(('pend10', s) in T and 0.8 <= math.exp(T[('pend10', s)]) / T_REF['pend10'] <= 1.2
                                           for s in SEEDS) / len(SEEDS))


def describe(rows, T):
    d = {}
    for i in INPUTS:
        rs = [r for r in rows if r['input'] == i]
        ts = [math.exp(v) for (ii, s), v in T.items() if ii == i]
        d[i] = dict(n=len(rs), n_usable=len(ts), T_med=float(np.median(ts)) if ts else None,
                    ratio_real_med=float(np.median(ts) / T_REF[i]) if ts else None,
                    within20=sum(0.8 <= t / T_REF[i] <= 1.2 for t in ts))
    return d


def analyze(meas, out):
    rows = json.load(open(meas))
    res = dict(T_ref=T_REF, n_clips=len(rows))
    for gate in ('ok', 'relaxed'):
        T = table(rows, gate)
        res[gate] = dict(describe=describe(rows, T), q1=q1(T), q2=q2(T),
                         per_clip={f'{i}_s{s}': math.exp(v) for (i, s), v in sorted(T.items())})
    json.dump(res, open(out, 'w'), indent=1, default=float)
    for gate in ('ok', 'relaxed'):
        r = res[gate]
        print(gate, json.dumps(r['describe']))
        print(gate, 'Q1', json.dumps({k: v for k, v in r['q1'].items()}))
        print(gate, 'Q2', json.dumps({k: v for k, v in r['q2'].items() if k != 'train_rank'}))


def selftest():
    rng = np.random.default_rng(5)
    for label, sd_seed, sd_noise in (('seed-locked', 0.5, 0.05), ('no-seed', 0.0, 0.4)):
        c = {s: rng.normal(0, sd_seed) for s in SEEDS}
        T = {(i, s): math.log(1.17) + 0.2 * k + c[s] + rng.normal(0, sd_noise)
             for k, i in enumerate(INPUTS) for s in SEEDS if rng.random() < 0.7}
        r = q1(T, nperm=500, nboot=200)
        print(label, round(r['icc1'], 3), r['perm_p'], r['decision'])
        b = q2(T)
        print('  bank', b['heldout_rate_top'], b['heldout_rate_all'], round(b['exact_p'], 3))


if __name__ == '__main__':
    cmd = sys.argv[1]
    if cmd == 'measure':
        measure(sys.argv[2], sys.argv[3])
    elif cmd == 'analyze':
        analyze(sys.argv[2], sys.argv[3])
    else:
        selftest()
