"""Task 228 POST HOC (not preregistered): rod regrowth per arm, same-seed period carry-over, slope over R2>=0.8 clips."""
import json, numpy as np
R = json.load(open('results.json'))['rows']; INL = json.load(open('inp/input_rodlen.json'))
IN = {'orig': INL['orig']['L_tan_px'], 'L70': INL['L70']['L_tan_px'], 'L50': INL['L50']['L_tan_px']}
OFF = 131.856 - IN['orig']
out = {}
for arm in ('orig', 'L70', 'L50'):
    v = [r for r in R.values() if r['arm'] == arm]
    tracked = [r for r in v if r['L_med'] and r['G4']]   # >=60% valid frames
    Lm = np.array([r['L_med'] for r in tracked])
    out[arm] = dict(input_tan_px=IN[arm], n_tracked_G4=len(tracked), L_med_px_median=float(np.median(Lm)) if len(Lm) else None,
                    L_med_over_orig_input_median=float(np.median(Lm) / IN['orig']) if len(Lm) else None,
                    n_r2=sum((r['r2'] or 0) >= 0.8 for r in v), n_pass=sum(r['PASS'] for r in v))
# same-seed carry-over (R2>=0.8 in both)
pairs = {}
for arm in ('L70', 'L50'):
    pr = []
    for s in range(21, 31):
        a = [r for r in R.values() if r['arm'] == arm and r['seed'] == s][0]; o = [r for r in R.values() if r['arm'] == 'orig' and r['seed'] == s][0]
        if (a['r2'] or 0) >= 0.8 and (o['r2'] or 0) >= 0.8:
            Lr = (a['L_med'] + OFF) / (o['L_med'] + OFF)
            pr.append(dict(seed=s, T_orig=o['T'], T_arm=a['T'], ratio=a['T'] / o['T'], Leff_ratio=Lr, law_pred=float(np.sqrt(Lr))))
    pairs[arm] = pr
out['same_seed_pairs_r2'] = pairs
# slope over all R2>=0.8 clips (any gates), seed-cluster bootstrap
P = [r for r in R.values() if (r['r2'] or 0) >= 0.8 and r['L_med']]
x = np.log([r['L_med'] + OFF for r in P]); y = np.log([r['T'] for r in P]); sd = np.array([r['seed'] for r in P])
sl = float(np.polyfit(x, y, 1)[0]); rng = np.random.default_rng(1); us = np.unique(sd); bs = []
for _ in range(5000):
    idx = np.concatenate([np.nonzero(sd == s)[0] for s in rng.choice(us, len(us))])
    if np.ptp(x[idx]) > 0.05: bs.append(np.polyfit(x[idx], y[idx], 1)[0])
out['slope_r2_clips'] = dict(n=len(P), n_seeds=len(us), slope=sl, ci95=[float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))])
# seed effect on T among R2>=0.8 clips: share of log-T variance explained by seed
yy = {}; [yy.setdefault(r['seed'], []).append(np.log(r['T'])) for r in P]
multi = {s: v for s, v in yy.items() if len(v) >= 2}
allv = np.concatenate(list(multi.values())); within = np.concatenate([np.array(v) - np.mean(v) for v in multi.values()])
out['seed_share_logT'] = dict(seeds_with_2plus=sorted(multi), n=len(allv), share=float(1 - (within ** 2).sum() / ((allv - allv.mean()) ** 2).sum()))
json.dump(out, open('posthoc.json', 'w'), indent=1); print(json.dumps(out, indent=1))
