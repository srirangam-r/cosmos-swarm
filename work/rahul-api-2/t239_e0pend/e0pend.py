"""Task 239 (rahul-api-2): does noise.device=cpu make the same seed's PENDULUM clip the same across GPU types?
Independent replication of Raj #4786 (E0) on pend10_mid_f93. Own code (not raj-noise/analyze.py). Frozen before fetch.

Clips: REF = rahul-api's t226_P_base_s101..106 (noise cpu; s101-104 a6k, s105-106 a100).
       L40 = my t239_P_base_l40s_cpu_s101..106 (identical params, pinned to l40s-0..3).
       CUDA = my t239_P_base_l40s_cuda_s101, s102 (same params minus the noise key: torch CUDA RNG).
Per pair of clips (full-res gray, frames 1..92; frame 0 is the conditioning frame):
  mae      mean |gray_a - gray_b|
  mae_t    per-frame MAE curve (does the divergence grow with time?)
  r_me     Pearson r of the ROI motion curves (readout.py motion(): mean |dgray| in the pivot disk)
Per clip: measure_pend v1 period (planted PASS) and flag.
Groups: SAME = L40 cpu vs REF same seed (6 pairs); CUDA = L40 cuda vs REF same seed (2 pairs);
        DIFF = every different-seed pair among the 12 cpu clips (60 pairs; split by same / cross GPU type).
Decision (frozen):
  IDENTITY REPLICATES if every SAME pair's mae < the minimum DIFF mae AND median SAME mae < 0.5 x median DIFF mae.
  PERIOD CARRIES if every SAME pair where both clips have a finite measure_pend period agrees within 10%
    (|T_a/T_b - 1| < 0.10), with >= 4 such pairs; reported alongside the DIFF-pair |dlog T| distribution.
  CUDA control is expected at DIFF level (median CUDA mae > 0.5 x median DIFF mae). If it is not, the switch did
    not matter on this stack and the SAME result can't be credited to the CPU noise.
Usage: python -I e0pend.py REF_DIR L40_DIR OUT.json"""
import sys, os, json, itertools
import numpy as np, cv2

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', 't226_pend')))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, '..', '..', '..', 'tools', 'trk_ballfall')))
import measure_pend as mp  # noqa: E402
import trk  # noqa: E402
from readout import motion  # noqa: E402


def gray(path, maxf=93):
    c = cv2.VideoCapture(path); G = []
    while len(G) < maxf:
        ok, f = c.read()
        if not ok:
            break
        G.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32))
    return np.array(G)


def main():
    ref, l40, outp = sys.argv[1:4]
    clips = {}
    for s in range(101, 107):
        clips[('ref', s)] = os.path.join(ref, f't226_P_base_s{s}.mp4')
        clips[('l40', s)] = os.path.join(l40, f't239_P_base_l40s_cpu_s{s}.mp4')
    for s in (101, 102):
        clips[('cuda', s)] = os.path.join(l40, f't239_P_base_l40s_cuda_s{s}.mp4')
    clips = {k: v for k, v in clips.items() if os.path.exists(v)}
    G = {k: gray(v) for k, v in clips.items()}
    gpu = {}
    for k, v in clips.items():
        sc = os.path.splitext(v)[0] + '.json'
        gpu[k] = json.load(open(sc)).get('endpoint', '?') if os.path.exists(sc) else '?'
    per = {}
    for k, v in clips.items():
        F = trk.load(v)
        try:
            p = mp.measure(F, 24.0, nboot=50)
            T, flag = float(p['period_s']), p['flag']
        except Exception as e:  # noqa: BLE001
            T, flag = float('nan'), 'fail'
        per[f'{k[0]}_s{k[1]}'] = dict(path=os.path.basename(v), endpoint=gpu[k], T=T, flag=flag,
                                      me_curve=[float(x) for x in motion(G[k][..., None].repeat(3, -1))])

    def pair(a, b):
        n = min(len(G[a]), len(G[b]))
        d = np.abs(G[a][1:n] - G[b][1:n]).reshape(n - 1, -1).mean(1)
        ca = np.array(per[f'{a[0]}_s{a[1]}']['me_curve']); cb = np.array(per[f'{b[0]}_s{b[1]}']['me_curve'])
        m = min(len(ca), len(cb))
        Ta, Tb = per[f'{a[0]}_s{a[1]}']['T'], per[f'{b[0]}_s{b[1]}']['T']
        return dict(a=f'{a[0]}_s{a[1]}', b=f'{b[0]}_s{b[1]}', ep_a=gpu[a], ep_b=gpu[b], mae=float(d.mean()),
                    mae_t=[float(x) for x in d], r_me=float(np.corrcoef(ca[:m], cb[:m])[0, 1]),
                    dlogT=float(abs(np.log(Ta / Tb))) if np.isfinite(Ta) and np.isfinite(Tb) else float('nan'))

    same = [pair(('l40', s), ('ref', s)) for s in range(101, 107) if ('l40', s) in G and ('ref', s) in G]
    cuda = [pair(('cuda', s), ('ref', s)) for s in (101, 102) if ('cuda', s) in G and ('ref', s) in G]
    cpu = [k for k in G if k[0] in ('ref', 'l40')]
    diff = [pair(a, b) for a, b in itertools.combinations(cpu, 2) if a[1] != b[1]]
    for p in diff:
        p['cross_type'] = p['ep_a'][:3] != p['ep_b'][:3]

    def summ(ps, key):
        v = np.array([p[key] for p in ps if np.isfinite(p[key])])
        return dict(n=int(len(v)), median=float(np.median(v)) if len(v) else None,
                    min=float(v.min()) if len(v) else None, max=float(v.max()) if len(v) else None)

    res = dict(per_clip={k: {kk: vv for kk, vv in v.items() if kk != 'me_curve'} for k, v in per.items()},
               same=same, cuda=cuda, diff=diff, summary={})
    for name, ps in (('same', same), ('cuda', cuda), ('diff', diff),
                     ('diff_same_type', [p for p in diff if not p['cross_type']]),
                     ('diff_cross_type', [p for p in diff if p['cross_type']])):
        res['summary'][name] = {k: summ(ps, k) for k in ('mae', 'r_me', 'dlogT')}
    S, D, C = res['summary']['same']['mae'], res['summary']['diff']['mae'], res['summary']['cuda']['mae']
    ident = bool(S['n'] and D['n'] and S['max'] < D['min'] and S['median'] < 0.5 * D['median'])
    fin = [p for p in same if np.isfinite(p['dlogT'])]
    carries = bool(len(fin) >= 4 and all(abs(np.exp(p['dlogT']) - 1) < 0.10 for p in fin))
    switch = bool(C['n'] and D['n'] and C['median'] > 0.5 * D['median'])
    res['decision'] = dict(identity_replicates=ident, period_carries=carries, n_period_pairs=len(fin),
                           cuda_switch_matters=switch)
    json.dump(res, open(outp, 'w'), indent=1)
    print(json.dumps(res['summary'], indent=1)); print(res['decision'])
    for p in same + cuda:
        print(f"{p['a']:14s} {p['ep_a']:8s} vs {p['b']:12s} {p['ep_b']:8s} mae {p['mae']:.2f} r_me {p['r_me']:.3f} "
              f"T {per[p['a']]['T']:.3f}/{per[p['b']]['T']:.3f} ({per[p['a']]['flag']}/{per[p['b']]['flag']})")


if __name__ == '__main__':
    main()
