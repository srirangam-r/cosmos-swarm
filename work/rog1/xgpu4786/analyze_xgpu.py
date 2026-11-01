"""rog1 replication of #4786 (CPU-drawn noise -> same clip across GPU types). Frozen before any clip was fetched.

Clips: xg_wood_<ep>_<cpu|cuda>_s<seed>.mp4 (+ .json sidecar) in DIR. Endpoints int-a100 / puget21 / laptop5090.
Feature: gray, frames 1..92, downscaled 1/8 with area interpolation (104x60), Gaussian blur sigma 1.
Metric: mean |diff| in gray levels (0-255) over all frames/pixels.
Groups:
  SAME  = same seed, cpu noise, different endpoint     (prediction: << DIFF)
  DIFF  = different seed, cpu noise, any endpoint pair (reference)
  CUDA  = cuda s301 on X vs cpu s301 on another endpoint, and cuda s301 int-a100 vs cuda s301 puget21
Decision (fixed): replicated if max(SAME) < min(DIFF) and median(SAME) < 0.5*median(DIFF).
Also report: sidecar evidence that noise.device=cpu was applied, and late motion
(mean |frame diff| over last 24 frame pairs) correlation across endpoints for same seed.
"""
import sys, json, glob, os, itertools, statistics as st
import numpy as np, cv2

D = sys.argv[1]


def feat(p):
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        g = cv2.cvtColor(f, cv2.COLOR_BGR2GRAY)
        g = cv2.resize(g, (104, 60), interpolation=cv2.INTER_AREA).astype(np.float32)
        fr.append(cv2.GaussianBlur(g, (0, 0), 1.0))
    return np.stack(fr)


clips = {}
for p in sorted(glob.glob(os.path.join(D, 'xg_wood_*.mp4'))):
    n = os.path.basename(p)[:-4]; _, _, ep, mode, s = n.split('_')
    sc = json.load(open(p[:-4] + '.json')) if os.path.exists(p[:-4] + '.json') else {}
    clips[n] = dict(ep=ep, mode=mode, seed=int(s[1:]), f=feat(p), side=sc)

out = {'n_clips': len(clips), 'sidecar_noise': {}, 'pairs': []}
for n, c in clips.items():
    s = json.dumps(c['side'])
    out['sidecar_noise'][n] = {'has_noise_key': '"noise"' in s, 'endpoint': c['side'].get('endpoint'),
                               'excerpt': [k for k in ('noise', 'server') if k in c['side']]}


def mae(a, b):
    m = min(len(a), len(b)); return float(np.abs(a[1:m] - b[1:m]).mean())


def late(c):
    f = c['f']; return float(np.abs(np.diff(f[-25:], axis=0)).mean())


G = {'SAME': [], 'DIFF': [], 'CUDA': []}
for a, b in itertools.combinations(sorted(clips), 2):
    A, B = clips[a], clips[b]
    if A['mode'] == 'cpu' and B['mode'] == 'cpu':
        g = 'SAME' if (A['seed'] == B['seed'] and A['ep'] != B['ep']) else ('DIFF' if A['seed'] != B['seed'] else None)
    elif 301 == A['seed'] == B['seed'] and A['ep'] != B['ep']:
        g = 'CUDA'
    else:
        g = None
    if g is None: continue
    v = mae(A['f'], B['f']); G[g].append(v); out['pairs'].append([a, b, g, round(v, 3)])
out['summary'] = {k: (dict(n=len(v), median=st.median(v), min=min(v), max=max(v)) if v else None) for k, v in G.items()}
if G['SAME'] and G['DIFF']:
    out['replicated'] = bool(max(G['SAME']) < min(G['DIFF']) and st.median(G['SAME']) < 0.5 * st.median(G['DIFF']))
out['late_motion'] = {n: round(late(c), 4) for n, c in clips.items()}
json.dump(out, open(os.path.join(D, 'xgpu_result.json'), 'w'), indent=1)
print(json.dumps(out['summary'], indent=1), out.get('replicated'))
