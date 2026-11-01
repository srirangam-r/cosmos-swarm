"""rog-cc rep2361: real GAUGE pendulum reference windows for readout.py (positive/negative control of the readout).
Input: GAUGE-Dataset data/rigid/pendulum/video/12.mp4 (HF InternRobotics/GAUGE-Dataset; 1280x720, 30 fps container).
Letterbox to 832x468 + 6 px bars (matches ro-3's inputs: native f93 == pend12_mid_f93.png, MAE 3.2).
Windows: held f0-55 (pre-release, 56 f, no dedup); from release f56 and from mid-swing f93 (container dups dropped -> 25 fps content, 93 f).
Usage: python3 -I make_real.py 12.mp4 OUTDIR"""
import sys, os, cv2, numpy as np
src, od = sys.argv[1], sys.argv[2]; os.makedirs(od, exist_ok=True)
c = cv2.VideoCapture(src); F = []
while len(F) < 330:
    ok, f = c.read()
    if not ok: break
    o = np.zeros((480, 832, 3), np.uint8); o[6:474] = cv2.resize(f, (832, 468), interpolation=cv2.INTER_AREA); F.append(o)
def dedup(seq):
    out = [seq[0]]
    for f in seq[1:]:
        if np.abs(f.astype(np.int16) - out[-1].astype(np.int16)).mean() > 0.3: out.append(f)
    return out
def w(name, seq):
    v = cv2.VideoWriter(f'{od}/{name}.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 24, (832, 480))
    for f in seq: v.write(f)
    v.release(); print(name, len(seq))
w('real12_rest_f56', dedup(F[56:56 + 120])[:93])
w('real12_mid_f93', dedup(F[93:93 + 120])[:93])
w('real12_held_f0_55', F[0:56])
