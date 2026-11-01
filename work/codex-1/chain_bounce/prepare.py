#!/usr/bin/env python3
"""Prepare continuation and equal-duration control requests from shared clips."""
import hashlib
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[3]
here = Path(__file__).resolve().parent
source = root / 'work/ro-1/fps_sweep/ballF'
clips = {1: source / 'ball_F_ball1_fps24_93f_s1.mp4',
         2: source / 's2/ball_F_ball1_fps24_93f_s2.mp4'}
real = root / 'work/ro-1/fps_sweep/gauge_ball1_dd33_832x480.png'
jobs = []
for seed, clip in clips.items():
    sidecar = json.loads(clip.with_suffix('.json').read_text())
    seam = here / 'inputs' / f'seed{seed}_frame92.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(clip), '-vf',
                    'select=eq(n\\,92)', '-frames:v', '1', str(seam)], check=True)
    for arm, frames, img in [('chain_tail', 93, seam), ('long_control', 185, real)]:
        jobs.append(dict(name=f'{arm}_s{seed}', image=str(img), prompt=sidecar['prompt'],
                         negative_prompt=None, width=832, height=480, num_frames=frames,
                         fps=24, steps=35, guidance=6.0, flow_shift=10.0, seed=seed,
                         extra_params={'client': 'codex-1'}))
    print(f'seed {seed}: source sha256={hashlib.sha256(clip.read_bytes()).hexdigest()} '
          f'seam sha256={hashlib.sha256(seam.read_bytes()).hexdigest()}')
print(f'real input sha256={hashlib.sha256(real.read_bytes()).hexdigest()}')
(here / 'jobs.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in jobs))
