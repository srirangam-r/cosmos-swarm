# Sanity check before trusting any score (lesson from #2480): frame 0 of every clip vs (a) other clips of the same input,
# (b) the task-92 base clip f0 of the same input, as-is and colour-inverted. Prints JSON.
import sys, os, glob, json, cv2, numpy as np
def f0(p):
    c = cv2.VideoCapture(p); ok, fr = c.read(); c.release()
    return cv2.resize(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), (208, 120)).astype(np.float32) if ok else None
clips = sorted(glob.glob(os.path.join(sys.argv[1], '*.mp4')))
ref_dir = sys.argv[2] if len(sys.argv) > 2 else None
F = {os.path.basename(p)[:-4]: f0(p) for p in clips}
groups = {}
for k in F: groups.setdefault(k.rsplit('_', 2)[0], []).append(k)
out = {}
for inp, ks in groups.items():
    med = np.median(np.stack([F[k] for k in ks if F[k] is not None]), 0)
    ref = None
    if ref_dir:
        r = sorted(glob.glob(os.path.join(ref_dir, f'{inp}_base_s*.mp4')))
        ref = f0(r[0]) if r else None
    for k in ks:
        d = {'mae_vs_input_median': float(np.abs(F[k] - med).mean())}
        if ref is not None:
            d['mae_vs_t92_base_f0'] = float(np.abs(F[k] - ref).mean())
            d['mae_vs_t92_base_f0_inverted'] = float(np.abs(F[k] - (255 - ref)).mean())
        out[k] = d
flag = [k for k, d in out.items() if d['mae_vs_input_median'] > 15 or d.get('mae_vs_t92_base_f0', 0) > 15]
print(json.dumps({'n': len(out), 'flagged': flag, 'clips': out}, indent=1))
