"""ro-api-3 task 115: measure clips/*.mp4 with measure_pend v1 + pend_acf; contact sheets for rigidity eye check.
usage: python -I measure.py  (run from t115/; incremental, writes results.json)"""
import json, subprocess, glob, os, sys, numpy as np, cv2
from concurrent.futures import ProcessPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable
T = os.path.join(HERE, '..', 'cosmos-swarm', 'tools')
MP = os.path.join(T, 'trk_ballfall', 'measure_pend.py'); ACF = os.path.join(T, 'pend_acf', 'pend_acf.py')
QC = os.path.join(HERE, 'qc'); os.makedirs(QC, exist_ok=True)
RES = os.path.join(HERE, 'results.json')

def js(out):
    try: return json.loads(out[out.index('{'):])
    except Exception: return {}

def one(mp4):
    n = os.path.basename(mp4)[:-4]
    m = js(subprocess.run([PY, '-I', MP, mp4, '--fps', '24', '--qc', f'{QC}/{n}_mp.png'], capture_output=True, text=True).stdout)
    a = js(subprocess.run([PY, '-I', ACF, mp4, '--fps', '24', '--skip', '12', '--qc', f'{QC}/{n}_acf.png'], capture_output=True, text=True).stdout)
    c = cv2.VideoCapture(mp4); fr = []
    while 1:
        ok, f = c.read()
        if not ok: break
        fr.append(f)
    idx = list(range(0, len(fr), 4))[:24]
    t = [cv2.resize(fr[i], (277, 160)) for i in idx]
    for i, x in zip(idx, t): cv2.putText(x, str(i), (4, 18), 0, 0.6, (0, 0, 255), 2)
    t += [np.zeros_like(t[0])] * (24 - len(t))
    cv2.imwrite(f'{QC}/sheet_{n}.jpg', np.vstack([np.hstack(t[k:k + 6]) for k in range(0, 24, 6)]))
    pf = a.get('period_frames')
    return n, dict(mp_T=m.get('period_s'), mp_ci=m.get('period_ci95'), mp_zc=m.get('period_zc_s'), mp_r2=m.get('r2'),
                   mp_flag=m.get('flag'), mp_halfcyc=m.get('n_halfcycles'), mp_beta=m.get('beta'), mp_release_t=m.get('release_t'),
                   acf_T=(pf / 24 if pf else None), acf_flag=a.get('flag'), nframes=len(fr))

if __name__ == '__main__':
    res = json.load(open(RES)) if os.path.exists(RES) else {}
    todo = [p for p in sorted(glob.glob(os.path.join(HERE, 'clips', '*.mp4'))) if os.path.basename(p)[:-4] not in res]
    with ProcessPoolExecutor(8) as ex:
        for n, r in ex.map(one, todo):
            res[n] = r; print(n, r, flush=True)
    json.dump(res, open(RES, 'w'), indent=1)
