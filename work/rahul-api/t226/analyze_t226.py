#!/usr/bin/env python3
"""t226 analysis (PREREG.md + Amendment 1). usage: python analyze_t226.py measures.json out.json"""
import sys, json, itertools
import numpy as np
from scipy import stats
ARMS = {'P': ['base', 'neutral', 'still', 'fast'], 'F': ['base', 'neutral', 'up', 'still'], 'H': ['base', 'neutral', 'up', 'still']}
PRIMARY = {('P', 'still'): 'ME_roi', ('P', 'fast'): 'logT_v1', ('F', 'up'): 'dy8', ('F', 'still'): 'dy8',
           ('H', 'up'): 'dyEnd', ('H', 'still'): 'dyEnd'}
STATS = {'P': ['ME_roi', 'ME_full', 'logT_v1', 'logT_w025'], 'F': ['dy8', 'ME_roi', 'ME_full', 'LM'], 'H': ['dyEnd', 'ME_roi', 'ME_full', 'LM']}


def value(r, s):
    if s == 'logT_v1':
        p = r['period_v1']; return np.log(p['period_s']) if p.get('flag') in ('ok', 'octave?') and p.get('period_s') else None
    if s == 'logT_w025':
        p = r['period_w025']; return np.log(p['period_s']) if p.get('flag') in ('ok', 'octave?') and p.get('period_s') else None
    v = r.get(s)
    return None if v is None else float(v)


def signflip_p(d):
    d = np.asarray(d, float); obs = abs(d.mean())
    allm = [abs((d * np.array(s)).mean()) for s in itertools.product([1, -1], repeat=len(d))]
    return float(np.mean([m >= obs - 1e-12 for m in allm]))


def contrast(X, a, b):
    seeds = sorted(s for s in X if X[s].get(a) is not None and X[s].get(b) is not None)
    d = np.array([X[s][a] - X[s][b] for s in seeds])
    if len(d) < 2: return dict(n=len(d))
    m, se = d.mean(), d.std(ddof=1) / np.sqrt(len(d)); tq = stats.t.ppf(0.975, len(d) - 1)
    return dict(n=len(d), mean=float(m), ci95=[float(m - tq * se), float(m + tq * se)], signflip_p=signflip_p(d),
                n_pos=int((d > 0).sum()), n_neg=int((d < 0).sum()), seeds=seeds, diffs=[float(x) for x in d])


def anova2(X, arms):
    seeds = sorted(s for s in X if all(X[s].get(a) is not None for a in arms))
    if len(seeds) < 3: return dict(n_seeds=len(seeds))
    Y = np.array([[X[s][a] for a in arms] for s in seeds]); g = Y.mean()
    ss_t = ((Y - g) ** 2).sum(); ss_p = len(seeds) * ((Y.mean(0) - g) ** 2).sum(); ss_s = len(arms) * ((Y.mean(1) - g) ** 2).sum()
    return dict(n_seeds=len(seeds), eta2_prompt=float(ss_p / ss_t), eta2_seed=float(ss_s / ss_t), resid=float((ss_t - ss_p - ss_s) / ss_t))


def main(mpath, opath):
    M = json.load(open(mpath)); out = {}
    for sc, arms in ARMS.items():
        R = [r for r in M.values() if r['scene'] == sc]
        out[sc] = {}
        for s in STATS[sc]:
            X = {}
            for r in R: X.setdefault(r['seed'], {})[r['arm']] = value(r, s)
            per_arm = {a: [X[k].get(a) for k in sorted(X)] for a in arms}
            sd = {a: float(np.std([v for v in per_arm[a] if v is not None], ddof=1)) if sum(v is not None for v in per_arm[a]) > 1 else None for a in arms}
            res = dict(per_arm=per_arm, seed_sd=sd, anova=anova2(X, arms), contrasts={})
            for c in arms[2:]:
                res['contrasts'][f'{c}-neutral'] = contrast(X, c, 'neutral'); res['contrasts'][f'{c}-base'] = contrast(X, c, 'base')
            res['contrasts']['base-neutral'] = contrast(X, 'base', 'neutral')
            # raw sign counts incl. -999 (lost above top) for the ball primaries
            if s in ('dy8', 'dyEnd'):
                res['up_lost'] = {a: sum(1 for r in R if r['arm'] == a and r.get(s + '_src') == 'lost_up') for a in arms}
                res['stay'] = {a: sum(1 for r in R if r['arm'] == a and r.get(s + '_src') == 'stay') for a in arms}
                res['missing'] = {a: sum(1 for r in R if r['arm'] == a and r.get(s + '_src') == 'missing') for a in arms}
            out[sc][s] = res
        dec = {}
        for c in arms[2:]:
            s = PRIMARY[(sc, c)]; k = out[sc][s]['contrasts'][f'{c}-neutral']; sdn = out[sc][s]['seed_sd']['neutral']
            if k.get('n', 0) < (4 if s.startswith('logT') else 2) or sdn is None: dec[c] = 'INCONCLUSIVE (too few pairs)'
            elif k['signflip_p'] <= 0.05: dec[c] = 'TEXT CONTROLS' if abs(k['mean']) > sdn else 'TEXT NUDGES'
            else: dec[c] = 'NOT DETECTED'
            dec[c] += f" [{s}: mean {k.get('mean')}, p {k.get('signflip_p')}, sd_neutral {sdn}, n {k.get('n')}]"
        out[sc]['decision'] = dec
        print(sc, json.dumps(dec, indent=1))
    json.dump(out, open(opath, 'w'), indent=1)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
