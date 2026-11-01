#!/usr/bin/env python3
"""t226 real references: GAUGE real continuations from the same first frames, letterboxed exactly like the inputs
(dedup, 1280x720 -> 832x468 + 6 px, as kiro-1 t185 make_input.py / raj-3 midfall_realcont.py), resampled by nearest
frame to 24 fps x 93 frames so ME and dy are on Nano's time base.
usage: python make_real_t226.py <gauge_pend_video_dir> <gauge_ball_video_dir> <outdir>"""
import sys, os, json, numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__)); REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools', 'trk_ballfall')); import measure_ball as mb
pd, bd, outd = sys.argv[1:4]; os.makedirs(outd, exist_ok=True)

def lbvid(path, nmax=600):
    c = cv2.VideoCapture(path); R = []
    while len(R) < nmax:
        ok, f = c.read()
        if not ok: break
        R.append(f)
    Fd, fac = mb.dedup(np.array(R).astype(np.float32)); fps = 30.0 * fac
    out = []
    for f in Fd:
        L = np.zeros((480, 832, 3), np.uint8); L[6:474] = cv2.resize(f.clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA); out.append(L)
    return out, fps

meta = {}
for name, path, k0, inp in [('t226_P_real_s0', f'{pd}/10.mp4', 93, 'inp_pend10_mid_f93.png'),
                            ('t226_F_real_s0', f'{bd}/1.mp4', 33, 'inp_ball1_midfall_dd33.png'),
                            ('t226_H_real_s0', f'{bd}/1.mp4', 0, 'inp_ball1_f0_held.png')]:
    F, fps = lbvid(path)
    idx = [k0 + int(round(t * fps / 24.0)) for t in range(93)]
    idx = [i for i in idx if i < len(F)]
    w = cv2.VideoWriter(os.path.join(outd, name + '.mp4'), cv2.VideoWriter_fourcc(*'mp4v'), 24, (832, 480))
    for i in idx: w.write(F[i])
    w.release()
    ref = cv2.imread(os.path.join(HERE, inp)).astype(np.float32)
    meta[name] = dict(src=path, fps_dedup=fps, start=k0, n=len(idx), last_src_frame=idx[-1],
                      frame0_vs_input_MAD=float(np.abs(F[k0].astype(np.float32) - ref).mean()))
    print(name, meta[name])
json.dump(meta, open(os.path.join(outd, 'real_meta.json'), 'w'), indent=1)
