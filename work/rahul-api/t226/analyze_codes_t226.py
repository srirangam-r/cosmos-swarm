#!/usr/bin/env python3
"""t226 blind event codes (PREREG 'Blind event codes' + Amendment 3), written before any code exists.
usage: analyze_codes_t226.py <blind_key.json> <out.json> <coder>=<codes.json> [<coder>=<codes.json> ...]
codes.json: {"<ID>": "<CODE>"} for all strips. Steps:
 1. control accuracy per coder on the 7 known-answer strips (flag a coder with >= 2 misses);
 2. agreement on the 72 t226 clips: Cohen's kappa per coder pair, Fleiss' kappa if >= 3 coders;
 3. majority code per clip (ties -> OTHER), with all coders and without flagged coders;
 4. per scene x arm: count of the text-described event (P: STILL; F/H: UP and STILL) + full code table;
 5. exact McNemar paired by seed: each counter-event arm C vs neutral (primary) and vs base, on C's event."""
import sys, json, itertools
from math import comb
from collections import Counter

CTRL = {'P_kaReal': 'SWING', 'P_kaFrozen': 'STILL', 'F_kaReal': 'DOWN', 'F_kaFrozen': 'STILL', 'F_kaUp': 'UP',
        'H_kaReal': 'DOWN', 'H_kaFrozen': 'STILL'}
MENU = {'P': {'SWING', 'STILL', 'OTHER'}, 'F': {'DOWN', 'UP', 'STILL', 'OTHER'}, 'H': {'DOWN', 'UP', 'STILL', 'OTHER'}}
ARMS = {'P': ['base', 'neutral', 'still', 'fast'], 'F': ['base', 'neutral', 'up', 'still'], 'H': ['base', 'neutral', 'up', 'still']}
EVENT = {('P', 'still'): 'STILL', ('F', 'up'): 'UP', ('F', 'still'): 'STILL', ('H', 'up'): 'UP', ('H', 'still'): 'STILL'}
SEEDS = [101, 102, 103, 104, 105, 106]


def mcnemar(b, c):
    n = b + c
    return 1.0 if n == 0 else min(1.0, 2 * sum(comb(n, k) for k in range(min(b, c) + 1)) / 2 ** n)


def cohen(a, b):
    n = len(a); po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b); pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n ** 2
    return None if pe == 1 else (po - pe) / (1 - pe)


def fleiss(rows):  # rows: list of per-item code lists (same number of raters)
    m = len(rows[0]); N = len(rows); cats = sorted({c for r in rows for c in r})
    P = [(sum(r.count(k) ** 2 for k in cats) - m) / (m * (m - 1)) for r in rows]
    p = [sum(r.count(k) for r in rows) / (N * m) for k in cats]
    Pb, Pe = sum(P) / N, sum(x * x for x in p)
    return None if Pe == 1 else (Pb - Pe) / (1 - Pe)


def majority(codes):
    c = Counter(codes).most_common()
    return c[0][0] if len(c) == 1 or c[0][1] > c[1][1] else 'OTHER'


def main(keyp, outp, specs):
    key = json.load(open(keyp)); coders = {}
    for s in specs:
        name, path = s.split('=', 1)
        coders[name] = {k.strip().upper(): str(v).strip().upper() for k, v in json.load(open(path)).items()}
    names = sorted(coders); res = {'coders': names}
    clip = {bid: n[len('t226_'):] for bid, n in key.items()}
    # completeness + menu check
    res['problems'] = {c: {'missing': sorted(b for b in key if b not in coders[c]),
                           'off_menu': sorted(b for b in key if b in coders[c] and coders[c][b] not in MENU[clip[b][0]])}
                       for c in names}
    # 1. controls
    ctrl_ids = {bid: clip[bid] for bid in key if clip[bid] in CTRL}
    res['controls'] = {}
    for c in names:
        miss = [ctrl_ids[b] for b in ctrl_ids if coders[c].get(b) != CTRL[ctrl_ids[b]]]
        res['controls'][c] = {'correct': len(ctrl_ids) - len(miss), 'of': len(ctrl_ids), 'missed': sorted(miss),
                              'flagged': len(miss) >= 2}
    flagged = [c for c in names if res['controls'][c]['flagged']]
    # 2. agreement on t226 clips
    ids = sorted(b for b in key if clip[b] not in CTRL and all(b in coders[c] for c in names))
    res['n_clips_coded_by_all'] = len(ids)
    res['cohen_kappa'] = {f'{a}|{b}': cohen([coders[a][i] for i in ids], [coders[b][i] for i in ids])
                          for a, b in itertools.combinations(names, 2)}
    res['raw_agreement'] = {f'{a}|{b}': sum(coders[a][i] == coders[b][i] for i in ids) / len(ids)
                            for a, b in itertools.combinations(names, 2)}
    res['fleiss_kappa'] = fleiss([[coders[c][i] for c in names] for i in ids]) if len(names) >= 3 else None
    # 3-5. per coder-set
    sets = {'all': names}
    if flagged and len(names) - len(flagged) >= 1:
        sets['unflagged'] = [c for c in names if c not in flagged]
    for sk, cs in sets.items():
        maj = {}
        for b in key:
            if clip[b] in CTRL: continue
            got = [coders[c][b] for c in cs if b in coders[c]]
            if got: maj[clip[b]] = majority(got)
        R = {'majority': maj, 'table': {}, 'event_counts': {}, 'mcnemar': {}}
        for sc in 'PFH':
            for arm in ARMS[sc]:
                cs_ = [maj.get(f'{sc}_{arm}_s{s}') for s in SEEDS]
                R['table'][f'{sc}_{arm}'] = dict(Counter(x for x in cs_ if x))
                for ev in sorted({v for (s2, _), v in EVENT.items() if s2 == sc}):
                    R['event_counts'][f'{sc}_{arm}:{ev}'] = f'{sum(x == ev for x in cs_)}/{sum(x is not None for x in cs_)}'
        for (sc, arm), ev in EVENT.items():
            for ref in ('neutral', 'base'):
                b = c_ = 0; pairs = 0
                for s in SEEDS:
                    x, y = maj.get(f'{sc}_{arm}_s{s}'), maj.get(f'{sc}_{ref}_s{s}')
                    if x is None or y is None: continue
                    pairs += 1; b += (x == ev and y != ev); c_ += (x != ev and y == ev)
                R['mcnemar'][f'{sc}_{arm}_vs_{ref}:{ev}'] = {'pairs': pairs, 'C_only': b, 'ref_only': c_, 'p_exact': mcnemar(b, c_)}
        res[f'codes_{sk}'] = R
    json.dump(res, open(outp, 'w'), indent=1)
    print(json.dumps({k: res[k] for k in ('controls', 'cohen_kappa', 'fleiss_kappa', 'n_clips_coded_by_all')}, indent=1))
    for sk in sets:
        print(sk, json.dumps(res[f'codes_{sk}']['event_counts']), json.dumps(res[f'codes_{sk}']['mcnemar'], indent=0))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
