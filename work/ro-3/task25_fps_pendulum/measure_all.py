"""ro-3 task 25: run measure_pend v1 (raj-3, referee PASS) on each sweep clip, full and with the first 12 frames trimmed
(Nano outpaints the pillarbox and reframes the camera in frames 0-12). Writes results.json + contact sheets."""
import json, subprocess, sys, glob, os, cv2, numpy as np
MP = os.path.abspath('../cosmos-swarm/tools/trk_ballfall/measure_pend.py'); PY = os.path.abspath('../venv/bin/python')
def frames(p):
    c = cv2.VideoCapture(p); out = []
    while True:
        ok, f = c.read()
        if not ok: break
        out.append(f)
    return out
def run(clip, fps, qc):
    r = subprocess.run([PY, '-I', MP, clip, '--fps', str(fps), '--qc', qc], capture_output=True, text=True)
    try: return json.loads(r.stdout[r.stdout.index('{'):])
    except Exception: return {'error': r.stderr[-300:]}
res = {}
for mp4 in sorted(glob.glob('clips/*.mp4')):
    n = os.path.basename(mp4)[:-4]; side = json.load(open(mp4[:-4] + '.json')); fps = side['fps']
    fr = frames(mp4); trim = f'qc/{n}_trim12.mp4'
    w = cv2.VideoWriter(trim, cv2.VideoWriter_fourcc(*'mp4v'), fps, (fr[0].shape[1], fr[0].shape[0]))
    for f in fr[12:]: w.write(f)
    w.release()
    idx = list(range(0, len(fr), max(1, len(fr) // 16)))[:16]
    tiles = [cv2.resize(fr[i], (416, 240)) for i in idx]
    for i, t in zip(idx, tiles): cv2.putText(t, str(i), (5, 25), 0, 0.8, (0, 0, 255), 2)
    cv2.imwrite(f'qc/sheet_{n}.jpg', np.vstack([np.hstack(tiles[k:k + 4]) for k in range(0, 16, 4)]))
    out = {}
    for tag, clip in (('full', mp4), ('trim12', trim)):
        m = run(clip, fps, f'qc/{n}_{tag}.png')
        if 'period_s' in m:
            m = {k: m[k] for k in ('period_s', 'period_ci95', 'period_zc_s', 'r2', 'n_halfcycles', 'release_frame', 'amp_px', 'flag')}
            m['period_frames'] = m['period_s'] * fps; m['period_zc_frames'] = m['period_zc_s'] * fps
        out[tag] = m
    res[n] = dict(fps=fps, seed=side['seed'], duration_template=side.get('extra_params', {}).get('use_duration_template', True), **out)
    print(n, fps, {t: (round(out[t].get('period_s', float('nan')), 3), round(out[t].get('period_frames', float('nan')), 1), out[t].get('flag')) for t in out}, flush=True)
json.dump(res, open('results.json', 'w'), indent=1)
