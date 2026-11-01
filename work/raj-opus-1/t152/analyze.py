"""Task 152 analysis: join per-clip PhyFPS (run_vc.py output) with task-139 firstfall g and eye codes.
Usage: python3 analyze.py vc_t139.json vc_ref.json > summary.txt   (writes summary.json)
- Reference check: real GAUGE clips (dedup 25 fps physical rate) should read ~25; demo clips have known fps.
- Fall set: task-139 clips with eye-coded clean_fall=1 and a firstfall fit (fall_px >= 50, flag ok/weak, r2 >= 0.95).
- One-clock prediction: g_meas = 9.81 * (24/PhyFPS)^2  ->  log g vs log PhyFPS slope -2, and g*(PhyFPS/24)^2 ~ 9.81.
  Spearman rho(PhyFPS, g) should be negative."""
import json, sys, math, os
import numpy as np
from scipy import stats
H = os.path.dirname(os.path.abspath(__file__)) + '/../t139'
V = json.load(open(sys.argv[1])); R = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
C = json.load(open(f'{H}/codes.json'))
out = {'ref': {k: {'avg': v['avg_phyfps'], 'seg_sd': float(np.std([s[1] for s in v['segments']]))} for k, v in R.items()}}
def win_mean(v, a, b):  # mean PhyFPS over windows whose 30-frame span overlaps [a,b]
    s = [p for st, p in v['segments'] if st <= b and st + 29 >= a]
    return float(np.mean(s)) if s else float('nan')
rows = []
for k, v in V.items():
    if not k.startswith('t139_'): continue
    ff = json.load(open(f'{H}/ff_json/{k}.json')); c = C.get(k, {})
    clean = int(c.get('fall', 0) and not c.get('descent_artifact', 0))
    ok = clean and ff.get('fall_px', 0) >= 50 and ff.get('flag') in ('ok', 'weak') and (ff.get('r2') or 0) >= 0.95 and ff.get('g', 0) > 0
    rows.append(dict(clip=k, arm=k.split('_')[1], seed=k.split('_')[3], clean=clean, use=int(bool(ok)),
                     g=ff.get('g'), flag=ff.get('flag'), r2=ff.get('r2'), onset=ff.get('motion_frame'), impact=ff.get('impact_frame'),
                     phy_all=v['avg_phyfps'], phy_first=v['segments'][0][1],
                     phy_fall=win_mean(v, ff.get('motion_frame') or 0, ff.get('impact_frame') or 0),
                     phy_late=win_mean(v, 40, 92)))
out['clips'] = rows
for arm in 'OAG':
    a = [r['phy_all'] for r in rows if r['arm'] == arm]
    out[f'arm_{arm}_phy_all'] = [round(float(np.mean(a)), 2), round(float(np.std(a, ddof=1) / len(a) ** .5), 2), len(a)] if a else None
U = [r for r in rows if r['use']]
out['n_fall'] = len(U)
for key in ('phy_all', 'phy_first', 'phy_fall'):
    x = np.array([r[key] for r in U]); g = np.array([r['g'] for r in U])
    if len(U) >= 4:
        rho, p = stats.spearmanr(x, g)
        sl = stats.linregress(np.log(x), np.log(g))
        corr = g * (x / 24) ** 2
        out[key] = dict(spearman_rho=round(float(rho), 3), p=round(float(p), 4), loglog_slope=round(float(sl.slope), 2),
                        slope_se=round(float(sl.stderr), 2), g_mean=round(float(g.mean()), 2),
                        g_retimed_mean=round(float(corr.mean()), 2), g_retimed_sd=round(float(corr.std(ddof=1)), 2),
                        phy_mean=round(float(x.mean()), 1), phy_sd=round(float(x.std(ddof=1)), 1))
json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), 'summary.json'), 'w'), indent=1)
print(json.dumps({k: v for k, v in out.items() if k != 'clips'}, indent=1))
for r in sorted(U, key=lambda r: r['g']):
    print(f"{r['clip']:18s} g={r['g']:.2f} flag={r['flag']} onset={r['onset']} phy_all={r['phy_all']:.1f} first={r['phy_first']:.1f} fall={r['phy_fall']:.1f}")
