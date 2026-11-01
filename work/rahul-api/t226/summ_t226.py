import json, sys
R = json.load(open(sys.argv[1]))
for sc in ('P', 'F', 'H'):
    print('==', sc, json.dumps(R[sc]['decision'], indent=0))
    for s, res in R[sc].items():
        if s == 'decision': continue
        print(' ', s, 'anova', {k: (round(v, 3) if isinstance(v, float) else v) for k, v in res['anova'].items()})
        print('    per_arm', {a: [None if v is None else round(v, 2) for v in vs] for a, vs in res['per_arm'].items()})
        print('    sd', {a: (None if v is None else round(v, 2)) for a, v in res['seed_sd'].items()})
        for c, k in res['contrasts'].items():
            if 'mean' in k: print('    ', c, 'n', k['n'], 'mean %.3f ci [%.3f, %.3f] p %.3f +%d/-%d' % (k['mean'], *k['ci95'], k['signflip_p'], k['n_pos'], k['n_neg']))
            else: print('    ', c, k)
