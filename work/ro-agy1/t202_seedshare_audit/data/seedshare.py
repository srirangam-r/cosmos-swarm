#!/usr/bin/env python3
"""Seed share of Nano's discrete outcomes, from frozen codes other agents already published.

Question (task 141 / scout-1 #3835 P3): in existing crossed designs that run the
same seed under several conditions (CFG level, image edit, input recording), how
much of the binary outcome does the seed fix, compared with the condition?

Statistics, per dataset x outcome (condition = everything except the seed):
  * eta2_seed, eta2_cond: two-way linear-probability sums of squares (descriptive).
  * conc_excess = P(agree | same seed, different condition) - P(agree | different
    seed, different condition).  0 under "seed carries nothing".
  * seed-excess permutation p: seed labels shuffled within each condition
    (keeps every condition's outcome rate), 20000 draws, one-sided.
Negative control: the same seed IDs on a different stack (t157 H100/UniPC vs t158
q8/Karras) draw different noise, so same-ID agreement across stacks should be at
chance (conc_excess ~ 0).
No video was viewed or regenerated; codes are taken as published (see README).
"""
import json, itertools, random, sys, os
from collections import defaultdict

D = sys.argv[1] if len(sys.argv) > 1 else 'data'
R = random.Random(20261101)
NPERM = int(os.environ.get("NPERM", 20000))


def load_t158():
    O = json.load(open(f'{D}/t158/codes_O_frozen.json'))
    A = json.load(open(f'{D}/t158/codes_A.json'))
    key = json.load(open(f'{D}/t158/author_KEY.json'))
    pk = json.load(open(f'{D}/t158/private_key.json'))
    rows = []
    for bid, c in O.items():
        nm = os.path.basename(key[bid])[:-4]          # t158_O_w4_s1
        _, arm, w, s = nm.split('_')
        w = 6 if nm.startswith('t139_') else int(w[1:])   # t139_O_ball1_sN = the guidance-6 arm
        rows.append(dict(ds='t158', stack='q8', arm='O', w=w, s=int(s[1:]), img='ball1_O',
                         clone=c['clone'], fall=c['any_fall'], hold=c['hold'], clean_fall=c['clean_fall']))
    for oid, c in A.items():
        nm = pk[oid]['name']; sc = pk[oid]['sidecar']
        s = int(nm.rsplit('_s', 1)[1]); w = int(round(sc['guidance']))
        rows.append(dict(ds='t158', stack='q8', arm='A', w=w, s=s, img='ball1_A',
                         clone=c['clone'], fall=c['fall'], hold=c['hold'], clean_fall=c['clean_fall']))
    return rows


def load_t157():
    rows = []
    for r in json.load(open(f'{D}/t157/unblinded.json')):
        b = lambda k: None if r[k] is None else int(bool(r[k]))
        rows.append(dict(ds='t157', stack='h100', arm=r['arm'], w=r['w'], s=r['s'], img='ball1_' + r['arm'],
                         clone=b('clone'), fall=b('fall'), hold=int(bool(r['levitate'])), clean_fall=b('clean_fall')))
    return rows


def load_t160():
    rows = []
    for f in ('codes.json', 'codes_cross.json', 'codes_proxyctl.json'):
        for nm, c in json.load(open(f'{D}/t160/{f}')).items():
            parts = nm.split('_')
            s = int(parts[-1][1:])
            if parts[0] == 'hr':
                arm, img = parts[1], parts[2]
            else:                                         # hrx_mine / hrx_t139 / hrx_mineproxy
                arm, img = 'A', parts[1]
            # 'hold' = original never descends (held in jaws or hovering), as rahul-api #3787 defines lock
            hold = int(c['fall'] == 0 and c['carry'] == 0 and c['clean_fall'] == 0)
            rows.append(dict(ds='t160', stack='q8', arm=arm, w=6, s=s, img=img,
                             clone=c['clone'], fall=c['fall'], hold=hold, clean_fall=c['clean_fall']))
    return rows


def grid(rows, outcome, condkey):
    """-> dict cond -> dict seed -> y (missing dropped)"""
    g = defaultdict(dict)
    for r in rows:
        y = r[outcome]
        if y is None:
            continue
        g[condkey(r)][r['s']] = int(y)
    return g


def conc_excess(g):
    same = [0, 0]; diff = [0, 0]
    conds = sorted(g)
    for c1, c2 in itertools.combinations(conds, 2):
        for s1, y1 in g[c1].items():
            for s2, y2 in g[c2].items():
                tgt = same if s1 == s2 else diff
                tgt[0] += (y1 == y2); tgt[1] += 1
    if same[1] == 0 or diff[1] == 0:
        return None, same, diff
    return same[0] / same[1] - diff[0] / diff[1], same, diff


def eta2(g):
    cells = [(c, s, y) for c, d in g.items() for s, y in d.items()]
    n = len(cells); mu = sum(y for *_, y in cells) / n
    sst = sum((y - mu) ** 2 for *_, y in cells)
    if sst == 0:
        return None, None
    bys = defaultdict(list); byc = defaultdict(list)
    for c, s, y in cells:
        bys[s].append(y); byc[c].append(y)
    ss_s = sum(len(v) * (sum(v) / len(v) - mu) ** 2 for v in bys.values())
    ss_c = sum(len(v) * (sum(v) / len(v) - mu) ** 2 for v in byc.values())
    return ss_s / sst, ss_c / sst


def perm_p(g, obs):
    """-> (one-sided p for conc_excess, null mean of eta2_seed)"""
    if obs is None:
        return None, None
    ge = 0; e2 = []
    for _ in range(NPERM):
        h = {}
        for c, d in g.items():
            seeds = list(d); ys = [d[s] for s in seeds]; R.shuffle(ys)
            h[c] = dict(zip(seeds, ys))
        e, *_ = conc_excess(h)
        ge += (e >= obs - 1e-12)
        es, _ = eta2(h)
        if es is not None:
            e2.append(es)
    return (ge + 1) / (NPERM + 1), (sum(e2) / len(e2) if e2 else None)


def analyse(name, rows, outcome, condkey, note=''):
    g = grid(rows, outcome, condkey)
    g = {c: d for c, d in g.items() if d}
    ex, same, diff = conc_excess(g)
    es, ec = eta2(g)
    nseed = len({s for d in g.values() for s in d}); n = sum(len(d) for d in g.values())
    rate = sum(y for d in g.values() for y in d.values()) / n
    p, e2null = perm_p(g, ex)
    # per-seed pattern string, for eyeballing
    seeds = sorted({s for d in g.values() for s in d})
    pat = {str(s): ''.join('.' if s not in g[c] else str(g[c][s]) for c in sorted(g)) for s in seeds}
    out = dict(analysis=name, outcome=outcome, n_clips=n, n_seeds=nseed, n_conds=len(g), rate=round(rate, 3),
               conds=[str(c) for c in sorted(g)], agree_same_seed=f'{same[0]}/{same[1]}',
               agree_diff_seed=f'{diff[0]}/{diff[1]}',
               conc_excess=None if ex is None else round(ex, 3), perm_p_one_sided=None if p is None else round(p, 4),
               eta2_seed=None if es is None else round(es, 3),
               eta2_seed_null_mean=None if e2null is None else round(e2null, 3), eta2_cond=None if ec is None else round(ec, 3),
               seed_patterns=pat, note=note)
    return out


def main():
    t158 = load_t158(); t157 = load_t157(); t160 = load_t160()
    res = []
    OUT = ('clone', 'fall', 'hold', 'clean_fall')
    # 1. Within one coder, one image, one stack: seed x guidance
    for arm in ('O', 'A'):
        for o in OUT:
            res.append(analyse(f't158 q8 arm {arm}: seed x CFG', [r for r in t158 if r['arm'] == arm], o,
                               lambda r: f"w{r['w']}"))
            res.append(analyse(f't157 H100 arm {arm}: seed x CFG', [r for r in t157 if r['arm'] == arm], o,
                               lambda r: f"w{r['w']}"))
    # 2. Within one coder and stack, across image edits: t160 hr_ = 4 edits x 2 recordings x seeds 11-15
    for o in OUT:
        res.append(analyse('t160 q8: seed x (edit O/E/A/K x recording v8/v15)',
                           [r for r in t160 if r['img'] in ('v8', 'v15')], o, lambda r: f"{r['arm']}_{r['img']}",
                           note='eye codes, not blind (rahul-api #3787)'))
    # 3. Across image (O vs A) at matched w, same stack -- different coders in t158
    for o in OUT:
        res.append(analyse('t158 q8: O vs A image at matched seed & w (different coders)',
                           [r for r in t158 if r['w'] in (2, 6, 8)], o, lambda r: f"{r['arm']}_w{r['w']}",
                           note='O and A coded by different coders (#3800)'))
        res.append(analyse('t157 H100: O vs A image at matched seed & w (same coders)', t157, o,
                           lambda r: f"{r['arm']}_w{r['w']}"))
    # 4. NEGATIVE CONTROL: same seed id, different stack -> different noise. Pair t157 with t158 (seeds 1-6).
    for arm in ('O', 'A'):
        for o in OUT:
            rr = [r for r in t157 + t158 if r['arm'] == arm and r['s'] <= 6 and r['w'] in (2, 6, 8)]
            # condition = stack x w; only cross-stack pairs are informative, so restrict pairs below
            g = grid(rr, o, lambda r: (r['stack'], r['w']))
            gx = {c: d for c, d in g.items() if d}
            # cross-stack-only concordance
            same = [0, 0]; diff = [0, 0]
            for c1 in [c for c in gx if c[0] == 'q8']:
                for c2 in [c for c in gx if c[0] == 'h100']:
                    for s1, y1 in gx[c1].items():
                        for s2, y2 in gx[c2].items():
                            t = same if s1 == s2 else diff
                            t[0] += (y1 == y2); t[1] += 1
            ex = same[0] / same[1] - diff[0] / diff[1] if same[1] and diff[1] else None
            # permutation: shuffle seeds within each condition
            ge = 0
            for _ in range(NPERM):
                h = {}
                for c, d in gx.items():
                    seeds = list(d); ys = [d[s] for s in seeds]; R.shuffle(ys); h[c] = dict(zip(seeds, ys))
                sm = [0, 0]; df = [0, 0]
                for c1 in [c for c in h if c[0] == 'q8']:
                    for c2 in [c for c in h if c[0] == 'h100']:
                        for s1, y1 in h[c1].items():
                            for s2, y2 in h[c2].items():
                                t = sm if s1 == s2 else df
                                t[0] += (y1 == y2); t[1] += 1
                e = sm[0] / sm[1] - df[0] / df[1]
                ge += (e >= ex - 1e-12)
            res.append(dict(analysis=f'NEG CONTROL cross-stack same seed id, arm {arm} (t157 H100 vs t158 q8, w2/6/8, s1-6)',
                            outcome=o, agree_same_seed=f'{same[0]}/{same[1]}', agree_diff_seed=f'{diff[0]}/{diff[1]}',
                            conc_excess=None if ex is None else round(ex, 3), perm_p_one_sided=round((ge + 1) / (NPERM + 1), 4),
                            note='different coders across stacks; seed ids share no noise across stacks'))
    # 5. Cross-input, within q8, seeds shared by t160 cross/proxy sets and t158/t160 (different coders/edits)
    for o in ('clone', 'hold', 'fall'):
        rr = [r for r in t158 if r['w'] == 6 and r['s'] in (1, 2, 3, 4)] + \
             [r for r in t160 if r['img'] in ('mine', 't139', 'mineproxy') and r['s'] in (1, 2, 3, 4)]
        res.append(analyse('q8 seeds 1-4 across inputs: t158 O/A w6 + t160 hrx mine/t139/mineproxy', rr, o,
                           lambda r: f"{r['ds']}_{r['arm']}_{r['img']}", note='mixed coders'))
        rr = [r for r in t160 if r['s'] in (11, 12, 13, 14)]
        res.append(analyse('q8 seeds 11-14 across all t160 inputs (8 hr_ + 3 hrx)', rr, o,
                           lambda r: f"{r['arm']}_{r['img']}", note='one coder, not blind'))
    json.dump(res, open('seedshare_results.json', 'w'), indent=1)
    for r in res:
        print(f"{r['analysis'][:78]:78s} {r['outcome']:10s} rate={r.get('rate','')!s:6s} "
              f"same={r['agree_same_seed']:8s} diff={r['agree_diff_seed']:9s} excess={r['conc_excess']!s:7s} "
              f"p={r['perm_p_one_sided']!s:7s} eta2_seed={r.get('eta2_seed','')!s:6s} null={r.get('eta2_seed_null_mean','')!s:6s} eta2_cond={r.get('eta2_cond','')!s}")


if __name__ == '__main__':
    main()
