"""Short-window regime check: real clips cut to N s after release (~1.7-2.5 cycles), like Nano clips."""
import json, subprocess, sys, numpy as np
ref = json.load(open('../cosmos-swarm/work/raj-3/gauge_pend/pend_pseudo_cosmos_results.json')); res = {}
for ms in (2.0, 2.4, 3.0):
    r_ = []
    for i in range(1, 21):
        fps = ref[str(i)]['fps']
        r = subprocess.run(['../venv/bin/python', '-I', '../cosmos-swarm/tools/pend_acf/pend_acf.py', f'real/pend{i}.mp4', '--fps', str(fps), '--release', '--max-s', str(ms)], capture_output=True, text=True)
        m = json.loads(r.stdout); r_.append((m['period_s'] or np.nan) / ref[str(i)]['T_mocap_zc'])
    r_ = np.array(r_); res[ms] = r_.tolist()
    print(f'max_s {ms}: ratio {np.nanmean(r_):.4f} ± {np.nanstd(r_, ddof=1)/np.sqrt(20):.4f} SE, sd {np.nanstd(r_, ddof=1):.4f}, within5% {np.sum(np.abs(r_-1)<0.05)}/20, fails {np.isnan(r_).sum()}', flush=True)
json.dump(res, open('real_short_results.json', 'w'), indent=1)
