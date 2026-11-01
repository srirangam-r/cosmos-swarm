#!/usr/bin/env python3
"""Reproduce comparator matching and uncertainty edge cases with fabricated scores."""
import json, pathlib, subprocess, sys, tempfile
root = pathlib.Path(__file__).resolve().parents[3]
compare = root / 'tools/nv_scoreboard/compare.py'

def run(args):
    p = subprocess.run([sys.executable, str(compare), *map(str, args)], text=True, capture_output=True)
    return {'exit': p.returncode, 'output': json.loads(p.stdout) if p.returncode == 0 else p.stderr.strip()}

with tempfile.TemporaryDirectory() as td:
    d = pathlib.Path(td)
    def scorefile(name, rows):
        out = {}
        for i, (image, seed, value) in enumerate(rows):
            side = d / f'{name}_{i}.json'
            side.write_text(json.dumps({'image': image, 'seed': seed, 'prompt': 'p', 'fps': 24}))
            out[str(i)] = {'clip': f'ball_{name}_{i}.mp4', 'sidecar': str(side), 'dover_fused': value}
        path = d / f'{name}.json'; path.write_text(json.dumps(out)); return path
    # Two distinct source images have the same basename. Reordered after entries make
    # FIFO match different images, reversing the individual paired differences.
    a = scorefile('before', [('/A/frame.png', 1, 10), ('/B/frame.png', 1, 20)])
    b = scorefile('after', [('/B/frame.png', 1, 21), ('/A/frame.png', 1, 11)])
    # All repeated samples use the same seed, so this is repeatability, not seed noise.
    n = scorefile('noise', [('/A/frame.png', 7, 0), ('/A/frame.png', 7, 2)])
    # Ten paired replicates on one input cannot establish generality over inputs.
    ca = scorefile('cluster_before', [('/A/only.png', i, 10) for i in range(10)])
    cb = scorefile('cluster_after', [('/A/only.png', i, 11) for i in range(10)])
    print(json.dumps({'basename_collision':run(['paired',a,b]), 'duplicate_seed':run(['noise',n]), 'one_image_ten_seeds':run(['paired',ca,cb])}, indent=2))
