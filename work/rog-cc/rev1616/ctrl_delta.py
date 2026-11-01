#!/usr/bin/env python3
"""Input-only control for #1616: real GAUGE ball1/2 starting at f0 vs at the mid-fall frame (t=1.32/1.40 s,
agy-3's dedup frames 33/35 at 25 fps). Both are 93 f at 24 fps, built with the same ffmpeg recipe:
`-ss T -vf scale=832:480,fps=24 -frames:v 93 -c:v libx264 -crf 18`. Prints mid - f0 per ball for DOVER/DD."""
import json, sys
d = json.load(open(sys.argv[1]))
ks = ('dover_fused', 'dover_technical', 'dover_aesthetic', 'dd_norm', 'dd_binary')
out = {}
for b in (1, 2):
    f0 = [v for k, v in d.items() if k.endswith(f'realball_{b}.mp4')][0]
    mid = [v for k, v in d.items() if k.endswith(f'realmid_{b}.mp4')][0]
    out[f'ball{b}'] = {k: {'f0': f0[k], 'mid': mid[k], 'delta': mid[k] - f0[k]} for k in ks}
out['mean_delta'] = {k: sum(out[f'ball{b}'][k]['delta'] for b in (1, 2)) / 2 for k in ks}
json.dump(out, open(sys.argv[2], 'w'), indent=1) if len(sys.argv) > 2 else None
print(json.dumps(out, indent=1))
