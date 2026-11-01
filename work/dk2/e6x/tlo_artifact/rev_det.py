# Cross-GPU determinism: H100 (dk2-e6b) vs q8 (raj) E6 stage-A clips, same frozen driver, CPU noise. usage: python3 -I rev_det.py H100_DIR Q8_DIR
import sys, glob, os, json, cv2, numpy as np
def frames(p):
    c = cv2.VideoCapture(p); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f.astype(np.float32))
    return np.stack(F)
out = {}
for h in sorted(glob.glob(os.path.join(sys.argv[1], "A_rec*.mp4"))):
    q = os.path.join(sys.argv[2], os.path.basename(h))
    if not os.path.exists(q): continue
    a, b = frames(h), frames(q); n = min(len(a), len(b))
    d = np.abs(a[:n] - b[:n]).mean(axis=(1, 2, 3))
    out[os.path.basename(h)] = dict(n_frames=[len(a), len(b)], mae_all=float(d.mean()), mae_f0=float(d[0]), mae_last=float(d[-1]),
                                    max_abs=float(np.abs(a[:n] - b[:n]).max()), bit_identical=bool((a[:n] == b[:n]).all()))
print(json.dumps(out, indent=1))
