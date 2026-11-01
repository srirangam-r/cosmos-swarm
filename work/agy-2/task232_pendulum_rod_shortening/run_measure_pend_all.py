#!/usr/bin/env python3
"""
Task 232: Run referee-validated measure_pend v1 on all 30 pendulum clips.
measure_pend is referee-validated on planted cases (referee_result_pend_v1.json: 100% pass).
Author: agy-2
Date: 2026-11-01
"""

import os
import sys
import glob
import json
import subprocess
import re

MEASURE_PEND = '/home/nail/swarm-work/agy-2/cosmos-swarm/tools/trk_ballfall/measure_pend.py'
CLIPS_DIR = '/home/nail/swarm-work/agy-2/t232_pendulum_data/clips'
OUT_FILE = '/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/task232_pendulum_rod_shortening/measure_pend_results.json'

def main():
    clips = sorted(glob.glob(os.path.join(CLIPS_DIR, '*.mp4')))
    print(f"Found {len(clips)} clips for measure_pend evaluation.")
    
    results = {}
    for clip in clips:
        fn = os.path.basename(clip)
        if 'base' in fn or fn.startswith('rpr_'):
            arm = 'orig'
        elif 'L70' in fn:
            arm = 'L70'
        elif 'L50' in fn:
            arm = 'L50'
        else:
            arm = 'unknown'
            
        m = re.search(r's(\d+)', fn)
        seed = int(m.group(1)) if m else None
        
        cmd = ['python3', MEASURE_PEND, clip, '--fps', '24']
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(res.stdout)
            data['arm'] = arm
            data['seed'] = seed
            data['file'] = fn
            results[fn] = data
            print(f"[{arm} s{seed}] T={data.get('period_s'):.3f}s, T_zc={data.get('period_zc_s')}, "
                  f"R2={data.get('r2'):.3f}, flag={data.get('flag')}")
        except Exception as e:
            print(f"[{arm} s{seed}] ERROR: {e}")
            results[fn] = {'arm': arm, 'seed': seed, 'file': fn, 'error': str(e)}
            
    with open(OUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved measure_pend results to {OUT_FILE}")

if __name__ == '__main__':
    main()
