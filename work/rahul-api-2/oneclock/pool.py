"""pool.py (task 162, Amendment 3): combine score.py outputs (seeds 21-50 on q8, seeds 51-110 on brev-p6k) and report
seed-clustered geo-mean rho1 with the same bootstrap as score.py (5000 draws, rng seed 0), for each part and pooled.
Usage: python3 -I pool.py out.json q8=score_all_s21-50.json brev=score_amd3.json"""
import sys, json, numpy as np
def summ(clips):
    by = {}
    for r in clips:
        if r['rho1'] and r['rho1'] > 0: by.setdefault(int(r['clip'].split('_s')[-1].split('.')[0]), []).append(np.log(r['rho1']))
    L = np.array([np.mean(v) for v in by.values()]); s = dict(n_clips_scored=len(clips), n_seeds=int(len(L)),
        how={h: sum(r['how'] == h for r in clips) for h in sorted({r['how'] for r in clips})})
    if len(L):
        rng = np.random.default_rng(0); bs = [rng.choice(L, len(L)).mean() for _ in range(5000)]
        s.update(geo_mean_rho1=float(np.exp(L.mean())), ci95=[float(np.exp(np.percentile(bs, 2.5))), float(np.exp(np.percentile(bs, 97.5)))],
                 seeds_above_1=int((L > 0).sum()), seeds_below_1=int((L < 0).sum()),
                 per_seed={int(k): round(float(np.exp(np.mean(v))), 3) for k, v in sorted(by.items())})
    return s
out, parts = sys.argv[1], dict(a.split('=', 1) for a in sys.argv[2:])
C = {k: json.load(open(v))['clips'] for k, v in parts.items()}
res = {k: summ(v) for k, v in C.items()}; res['pooled'] = summ([r for v in C.values() for r in v])
res['inputs'] = parts
print(json.dumps(res, indent=1)); json.dump(res, open(out, 'w'), indent=1)
