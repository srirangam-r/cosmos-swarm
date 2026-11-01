"""ro-3 task 99: pendulum-ROI crop strips + motion energy per clip (eye-coding aid; not a physics measure).
ROI = x 240:420, y 90:300 (832x480 frame) covering axle, rod and bob in GAUGE pendulum side view."""
import glob, os, json, sys, numpy as np, cv2
X0, X1, Y0, Y1 = 240, 420, 90, 300
os.makedirs('qc', exist_ok=True); out = {}
G = sys.argv[1] if len(sys.argv) > 1 else 'out/*.mp4'; J = sys.argv[2] if len(sys.argv) > 2 else 'roi_motion.json'
for mp4 in sorted(glob.glob(G)):
    n = os.path.basename(mp4)[:-4]; c = cv2.VideoCapture(mp4); F = []
    while 1:
        ok, f = c.read()
        if not ok: break
        F.append(f[Y0:Y1, X0:X1])
    F = np.array(F); g = F.mean(-1)
    e = np.abs(np.diff(g, axis=0)).mean((1, 2))  # mean |frame diff| in ROI, grey levels
    out[n] = dict(n=len(F), motion_early=float(e[:24].mean()), motion_late=float(e[-24:].mean()), motion_all=float(e.mean()))
    strip = [F[i].copy() for i in range(0, len(F), 4)][:24]
    for i, s in zip(range(0, len(F), 4), strip): cv2.putText(s, str(i), (3, 18), 0, 0.6, (0, 0, 255), 2)
    strip += [np.zeros_like(F[0])] * (24 - len(strip))
    cv2.imwrite(f'qc/roi_{n}.jpg', np.vstack([np.hstack(strip[k:k + 12]) for k in (0, 12)]))
    print(n, {k: round(v, 2) for k, v in out[n].items()})
json.dump(out, open(J, 'w'), indent=1)
