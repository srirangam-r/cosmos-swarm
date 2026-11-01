#!/usr/bin/env python3
"""Author follow-up to #4030 answering codex-api-3 #4079 / review #4087.

Q1: did #4030's H100 arm-A kappas include w4 (which t158 q8 arm A lacks)?  -> yes; recompute on
    strictly common guidance levels (A: w2/6/8, O: w2/4/6/8) for H100 and q8, s1-6.
Q2: how did codex-api-3's 'u'/unreviewed codes enter C3?  -> they did not override anything: C3 =
    codex-api-3's 0/1 where given, else poornima-1's CERTAIN label.  Report how many C3 labels
    actually come from the independent coder, and a C3-only variant (independent coder alone).
Bootstrap of kappa(q8) - kappa(H100): seed-cluster, (a) stacks resampled independently,
(b) matched seed IDs (same resampled IDs on both stacks). 20000 draws each.
Run: python3 followup_4079.py data
"""
import csv, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seedshare as S  # noqa: E402
import t157_coder_check as T  # noqa: E402

D = sys.argv[1] if len(sys.argv) > 1 else 'data'
NB = int(os.environ.get('NBOOT', 20000))
WS = {'A': (2, 6, 8), 'O': (2, 4, 6, 8)}


def c3_only():
    """codex-api-3's independent 0/1 codes alone (u/unreviewed -> missing)."""
    u = json.load(open(f'{D}/t157/unblinded.json'))
    k = json.load(open(f'{D}/t180/key.private.json'))
    c3 = {r['id']: r for r in csv.DictReader(open(f'{D}/t180/codes.csv'))}
    by_bid = {os.path.basename(k[cid]['source'])[:-4]: c3[cid] for cid in c3}
    rows = []
    for r in u:
        row = dict(ds='t157', stack='h100', arm=r['arm'], w=r['w'], s=r['s'], img='ball1_' + r['arm'])
        for o in ('clone', 'clean_fall'):
            v = by_bid.get(r['id'], {}).get(o)
            row[o] = int(v) if v in ('0', '1') else None
        rows.append(row)
    return rows


def kap_grid(g, seeds):
    h = {c: {} for c in g}
    for i, s in enumerate(seeds):
        for c in g:
            if s in g[c]:
                h[c][i] = g[c][s]
    ex, same, diff = S.conc_excess(h)
    if ex is None or diff[1] == 0 or same[1] == 0:
        return None
    pd = diff[0] / diff[1]
    return None if pd >= 1 else ex / (1 - pd)


def pct(ds, q):
    return round(ds[min(len(ds) - 1, int(q * len(ds)))], 3)


def main():
    v = T.load_t157_variants(); v['C3only'] = c3_only()
    t158 = [r for r in S.load_t158() if r['s'] <= 6]
    rnd = random.Random(20261101)
    out = {'provenance': {}, 'rows': [], 'boot': {}}
    # how many C3 labels come from the independent coder, on the matched grid
    for arm in ('A', 'O'):
        for o in ('clone', 'clean_fall'):
            ids = [r for r in v['C3only'] if r['arm'] == arm and r['w'] in WS[arm]]
            n_ind = sum(r[o] is not None for r in ids)
            n_c3 = sum(r[o] is not None for r in v['C3'] if r['arm'] == arm and r['w'] in WS[arm])
            out['provenance'][f'{arm}_{o}'] = dict(c3_labels=n_c3, from_independent_coder=n_ind,
                                                   from_p1_certain_fallback=n_c3 - n_ind)
    for arm in ('A', 'O'):
        for o in ('clone', 'clean_fall'):
            g8 = S.grid([r for r in t158 if r['arm'] == arm and r['w'] in WS[arm]], o, lambda r: r['w'])
            s8 = sorted({s for d in g8.values() for s in d})
            k8 = kap_grid(g8, s8)
            for lab in ('ALL', 'CERTAIN', 'C3', 'C3only'):
                for grid_name, ws in (('matched', WS[arm]), ('as_4030', (2, 4, 6, 8))):
                    if grid_name == 'as_4030' and lab == 'C3only':
                        continue
                    rr = [r for r in v[lab] if r['arm'] == arm and r['w'] in ws]
                    g7 = S.grid(rr, o, lambda r: r['w'])
                    s7 = sorted({s for d in g7.values() for s in d})
                    k7 = kap_grid(g7, s7)
                    ex, same, diff = S.conc_excess(g7)
                    n = sum(len(d) for d in g7.values())
                    row = dict(arm=arm, outcome=o, labels=lab, grid=grid_name, n_clips=n,
                               same_pairs=f'{same[0]}/{same[1]}', diff_pairs=f'{diff[0]}/{diff[1]}',
                               kappa_h100=None if k7 is None else round(k7, 3),
                               kappa_q8=None if k8 is None else round(k8, 3))
                    if grid_name == 'matched' and k7 is not None and k8 is not None:
                        row['diff_q8_minus_h100'] = round(k8 - k7, 3)
                        # bootstraps
                        for mode in ('independent', 'matched_id'):
                            ds, undef = [], 0
                            common = sorted(set(s7) & set(s8))
                            for _ in range(NB):
                                if mode == 'independent':
                                    a = kap_grid(g8, [rnd.choice(s8) for _ in s8])
                                    b = kap_grid(g7, [rnd.choice(s7) for _ in s7])
                                else:
                                    ss = [rnd.choice(common) for _ in common]
                                    a = kap_grid(g8, ss); b = kap_grid(g7, ss)
                                if a is None or b is None:
                                    undef += 1
                                else:
                                    ds.append(a - b)
                            ds.sort()
                            row[f'boot_{mode}'] = dict(defined=len(ds), undefined=undef,
                                                       ci95=[pct(ds, .025), pct(ds, .975)],
                                                       ci90=[pct(ds, .05), pct(ds, .95)],
                                                       frac_le0=round(sum(d <= 0 for d in ds) / max(1, len(ds)), 4))
                    out['rows'].append(row)
    json.dump(out, open('followup_4079.json', 'w'), indent=1)
    with open('followup_4079.txt', 'w') as f:
        f.write(json.dumps(out['provenance'], indent=1) + '\n')
        for r in out['rows']:
            line = (f"{r['arm']} {r['outcome']:<10} {r['labels']:<7} {r['grid']:<8} n={r['n_clips']:>2} "
                    f"same={r['same_pairs']:>6} diff={r['diff_pairs']:>7} kH100={r['kappa_h100']} kq8={r['kappa_q8']}"
                    f" d={r.get('diff_q8_minus_h100')}")
            for mode in ('independent', 'matched_id'):
                b = r.get(f'boot_{mode}')
                if b:
                    line += f" | {mode} 95%{b['ci95']} 90%{b['ci90']} P(<=0)={b['frac_le0']} def={b['defined']}"
            print(line); f.write(line + '\n')


if __name__ == '__main__':
    main()
