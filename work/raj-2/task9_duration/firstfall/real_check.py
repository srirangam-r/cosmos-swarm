"""raj-2: firstfall v1 on REAL GAUGE drops at Cosmos resolution (raj-3 pseudo_cosmos transform: dedup, letterbox 832x468+6 px),
auto seed, fixed 539.8 px/m; reference = raj-3 mocap v5 estimator (pseudo_cosmos_results.json g_mocap_v5)."""
import sys, json, numpy as np, cv2
repo = sys.argv[1]; root = sys.argv[2]; outd = sys.argv[3]
sys.path.insert(0, repo + '/tools/realball'); sys.path.insert(0, repo + '/tools/trk_ballfall')
import trk, measure_ball as mb, firstfall as ff
ref = json.load(open(repo + '/work/raj-3/pseudo_cosmos/pseudo_cosmos_results.json'))['per_clip']
res = {}
for i in range(1, 23):
    p = f'{outd}/gauge{i}_lb832.mp4'
    F = trk.load(f'{root}/video/{i}.mp4'); F, fac = mb.dedup(F); fps = 30.0 * fac
    w = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(*'mp4v'), fps, (832, 480))
    for f in F:
        L = np.zeros((480, 832, 3), np.uint8); L[6:474] = cv2.resize(f.clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA); w.write(L)
    w.release()
    G = trk.load(p)
    try:
        r, tr = ff.measure(G, fps, ppm=539.8, nboot=100); ff.qc_png(f'{outd}/gauge{i}_ffqc.png', G, tr, r)
    except Exception as e:
        res[i] = dict(err=repr(e)); print(i, 'ERR', e, flush=True); continue
    gm = ref[str(i)].get('g_mocap_v5') if str(i) in ref else None
    r['g_mocap_v5'] = gm; r['ratio'] = r['g'] / gm if gm else None
    res[i] = {k: v for k, v in r.items() if k != 'method'}
    print(i, r['flag'], round(r['g'], 3), r['g_ci95'], 'ratio', r['ratio'] and round(r['ratio'], 3), 'Tfall', round(r['fall_time_s'], 3), 'd_ratio', round(r['d_ratio'], 2), flush=True)
ok = [r for r in res.values() if 'err' not in r and r['flag'] == 'ok' and r['ratio']]
rat = np.array([r['ratio'] for r in ok])
summ = dict(n_ok=len(ok), n=len(res), ratio_mean=float(rat.mean()) if len(rat) else None, ratio_se=float(rat.std(ddof=1) / np.sqrt(len(rat))) if len(rat) > 1 else None,
            ratio_sd=float(rat.std(ddof=1)) if len(rat) > 1 else None, ratio_median=float(np.median(rat)) if len(rat) else None,
            within10=int((abs(rat - 1) < 0.1).sum()))
print(summ)
json.dump(dict(method=ff.VERSION, ppm=539.8, summary=summ, per_clip=res), open(f'{outd}/firstfall_gauge_real.json', 'w'), indent=1, default=float)
