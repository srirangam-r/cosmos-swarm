"""ro-3 task 25: run pend_acf (--skip 12) on every clip in clips/ (+ ro-3 clips from srv/out_srv not yet copied),
build merged table: name, num_frames, fps, seed, arm, P_frames, P/N, cycles per clip, flag. Writes acf_table.json."""
import json, subprocess, glob, os, sys
PY = os.path.abspath('../venv/bin/python'); ACF = os.path.abspath('../cosmos-swarm/tools/pend_acf/pend_acf.py')
old = json.load(open('acf_table.json')) if os.path.exists('acf_table.json') else {}
rows = {}
for mp4 in sorted(glob.glob('clips/*.mp4')):
    n = os.path.basename(mp4)[:-4]
    side = json.load(open(mp4[:-4] + '.json')); fps = side['fps']; N = side.get('num_frames')
    if n in old and old[n].get('N') == N:
        rows[n] = old[n]; continue
    os.makedirs('qc_acf', exist_ok=True)
    r = subprocess.run([PY, '-I', ACF, mp4, '--fps', str(fps), '--skip', '12', '--qc', f'qc_acf/{n}.png'],
                       capture_output=True, text=True)
    try: m = json.loads(r.stdout[r.stdout.index('{'):])
    except Exception: m = {'error': r.stderr[-300:]}
    P = m.get('period_frames')
    arm = 'base'
    if '_p' in n: arm = n.split('_p')[1].split('_')[0]
    if side.get('extra_params', {}).get('use_duration_template') is False: arm = 'nodur'
    rows[n] = dict(N=N, fps=fps, seed=side.get('seed'), arm=arm, P_frames=P, P_over_N=(P / N if P and N else None),
                   cycles_after_skip=((N - 12) / P if P else None), P_s=(P / fps if P else None), flag=m.get('flag'), raw=m)
    print(n, N, fps, arm, P and round(P, 1), P and round(P / N, 3), m.get('flag'), flush=True)
json.dump(rows, open('acf_table.json', 'w'), indent=1)
