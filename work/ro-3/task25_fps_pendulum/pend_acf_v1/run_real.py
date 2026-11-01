import json, subprocess, numpy as np
ref = json.load(open('../cosmos-swarm/work/raj-3/gauge_pend/pend_pseudo_cosmos_results.json'))
out = {}
for i in range(1, 21):
    fps = ref[str(i)]['fps']
    r = subprocess.run(['../venv/bin/python', '-I', '../cosmos-swarm/tools/pend_acf/pend_acf.py', f'real/pend{i}.mp4', '--fps', str(fps), '--release', '--qc', f'qc/real{i}.png'], capture_output=True, text=True)
    m = json.loads(r.stdout); m['T_mocap_zc'] = ref[str(i)]['T_mocap_zc']; m['ratio'] = (m['period_s'] or np.nan) / m['T_mocap_zc']
    m['release_t_raj3'] = ref[str(i)]['release_t_video']
    out[i] = m; print(i, m['flag'], round(m['period_s'] or 0, 4), round(m['T_mocap_zc'], 4), round(m['ratio'], 4), 'rel', m['release_frame'], round(m['release_t_raj3']*fps), 'cyc', round(m.get('cycles_in_clip', 0), 1), flush=True)
json.dump(out, open('real_results.json', 'w'), indent=1)
r = np.array([o['ratio'] for o in out.values()]); ok = np.array([o['flag'] == 'ok' for o in out.values()])
print(f'all: {np.nanmean(r):.4f} ± {np.nanstd(r, ddof=1)/np.sqrt(len(r)):.4f} SE, sd {np.nanstd(r, ddof=1):.4f}, within5% {np.sum(np.abs(r-1)<0.05)}/20')
print(f'ok ({ok.sum()}): {np.nanmean(r[ok]):.4f} sd {np.nanstd(r[ok], ddof=1):.4f}')
