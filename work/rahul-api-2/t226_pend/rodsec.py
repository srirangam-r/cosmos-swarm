"""Task 226 pendulum, SECONDARY period readout (Amendment 1): kiro-1 t191 rodtrack, UNVALIDATED (no planted check).
Written before the full set of t226 P clips exists; the gates are the ones fixed in Amendment 1 (t228 G4 + R2):
  valid_frac >= 0.6 (rod tracked in >= 60% of frames) and r2 >= 0.8. Period = rodtrack damped-sine T.
Seed-paired log(T_A/T_B) per contrast on seeds where BOTH clips pass, with readout.paired (d, exact sign-flip p).
Also reports T / 1.171 s (real pend10 first-8 s period, mocap; tools/trk_ballfall README) per arm.
Usage: python -I rodsec.py RODTRACK.json MEAS.json OUT.json --contrasts fast:neutral,still:neutral,...
MEAS.json (readout.py measure output) supplies the arm/seed labels from the sidecars."""
import sys, os, json, argparse
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from readout import paired  # noqa: E402

T_REAL = 1.171


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('rt'); ap.add_argument('meas'); ap.add_argument('out')
    ap.add_argument('--contrasts', required=True); ap.add_argument('--vf', type=float, default=0.6)
    ap.add_argument('--r2', type=float, default=0.8)
    a = ap.parse_args()
    rt = json.load(open(a.rt)); meas = json.load(open(a.meas))
    lab = {}
    for r in meas:
        sc = r.get('sidecar') or {}; ep = sc.get('extra_params') or {}
        if ep.get('arm') is not None and sc.get('seed') is not None:
            lab[os.path.splitext(r['clip'])[0]] = (ep['arm'], int(sc['seed']))
    per = {}; rows = {}
    for name, v in rt.items():
        if name not in lab:
            continue
        arm, seed = lab[name]
        T = v.get('T', float('nan')); vf = v.get('valid_frac', 0.0); r2 = v.get('r2', float('nan'))
        ok = bool(np.isfinite(T) and vf >= a.vf and np.isfinite(r2) and r2 >= a.r2)
        per[name] = dict(arm=arm, seed=seed, T=T, valid_frac=vf, r2=r2, L_med=v.get('L_med'), L_cv=v.get('L_cv'), gate=ok)
        rows[(arm, seed)] = float(np.log(T)) if ok else float('nan')
    arms = sorted({p['arm'] for p in per.values()})
    out = dict(gates=dict(valid_frac=a.vf, r2=a.r2), T_real=T_REAL, per_clip=per, arms={}, contrasts={})
    for arm in arms:
        T = [p['T'] for p in per.values() if p['arm'] == arm and p['gate']]
        out['arms'][arm] = dict(n=sum(p['arm'] == arm for p in per.values()), n_gate=len(T), T_gate=T,
                                T_geo=float(np.exp(np.mean(np.log(T)))) if T else None,
                                ratio_real_geo=float(np.exp(np.mean(np.log(np.array(T) / T_REAL)))) if T else None)
    for c in a.contrasts.split(','):
        A, B = c.split(':')
        out['contrasts'][c] = paired({k: v for k, v in rows.items() if k[0] in (A, B)}, A, B, 'log_T_rodtrack')
    json.dump(out, open(a.out, 'w'), indent=1)
    for arm, v in out['arms'].items():
        print(f"{arm:8s} n={v['n']} gate={v['n_gate']} T_geo={v['T_geo']} ratio_real={v['ratio_real_geo']}")
    for c, v in out['contrasts'].items():
        if v.get('n'):
            print(f"{c:14s} n={v['n']} ratio {v['ratio_geo']:.3f} d={v['d_vs_seed_spread']:.2f} p={v['signflip_p']:.3f}")
        else:
            print(f"{c:14s} n=0")


if __name__ == '__main__':
    main()
