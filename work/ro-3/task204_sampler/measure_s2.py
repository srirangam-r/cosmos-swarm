"""ro-3 task 99: measure fetched clips in out/ with measure_pend v1 (full) + pend_acf; contact sheets; paired mid/rest table."""
import json, subprocess, glob, os, numpy as np, cv2
R = '/home/rohith/swarm-work/ro-3'; PY = R + '/venv/bin/python'
MP = R + '/cosmos-swarm/tools/trk_ballfall/measure_pend.py'; ACF = R + '/cosmos-swarm/tools/pend_acf/pend_acf.py'
os.makedirs('qc_s2', exist_ok=True); res = json.load(open('results_sampler.json')) if os.path.exists('results_sampler.json') else {}
def js(out):
    try: return json.loads(out[out.index('{'):])
    except Exception: return {}
for mp4 in sorted(glob.glob('out_s2/*.mp4')):
    n = os.path.basename(mp4)[:-4]
    if n in res: continue
    m = js(subprocess.run([PY, '-I', MP, mp4, '--fps', '24', '--qc', f'qc_s2/{n}_mp.png'], capture_output=True, text=True).stdout)
    a = js(subprocess.run([PY, '-I', ACF, mp4, '--fps', '24', '--skip', '0', '--qc', f'qc_s2/{n}_acf.png'], capture_output=True, text=True).stdout)
    c = cv2.VideoCapture(mp4); fr = []
    while 1:
        ok, f = c.read()
        if not ok: break
        fr.append(f)
    idx = list(range(0, len(fr), 6))[:16]; t = [cv2.resize(fr[i], (416, 240)) for i in idx]
    for i, x in zip(idx, t): cv2.putText(x, str(i), (5, 25), 0, 0.8, (0, 0, 255), 2)
    t += [np.zeros_like(t[0])] * (16 - len(t))
    cv2.imwrite(f'qc_s2/sheet_{n}.jpg', np.vstack([np.hstack(t[k:k + 4]) for k in range(0, 16, 4)]))
    res[n] = dict(mp_T=m.get('period_s'), mp_ci=m.get('period_ci95'), mp_zc=m.get('period_zc_s'), mp_r2=m.get('r2'), mp_flag=m.get('flag'),
                  mp_halfcyc=m.get('n_halfcycles'), mp_amp=m.get('amp_px'), acf_T=(a.get('period_frames') or 0) / 24 or None, acf_flag=a.get('flag'))
    print(n, res[n], flush=True)
json.dump(res, open('results_sampler.json', 'w'), indent=1)
real = {k: v['period_s'] for k, v in json.load(open('inputs/pick.json')).items()}
for clip in ('10', '11'):
    for s in (1, 2, 3):
        r, m = res.get(f'ms_pend{clip}_rest_s{s}', {}), res.get(f'ms_pend{clip}_mid_s{s}', {})
        print(clip, s, 'real', round(real[clip], 3), 'rest', r.get('mp_T'), r.get('mp_flag'), 'mid', m.get('mp_T'), m.get('mp_flag'))
