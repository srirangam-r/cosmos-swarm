#!/usr/bin/env python3
"""t226 Amendment 3: known-answer control clips mixed (random IDs) into the blind strip set, to check coder accuracy.
They are NOT part of any t226 analysis (measure/analyze read clips/ only). Usage: make_ctrl_t226.py <real_dir> <out_dir>
  P_kaReal   real GAUGE pend10 continuation from f93 (expected SWING)
  P_kaFrozen input frame x 93 (STILL)
  F_kaReal   real ball-1 continuation from dd33 (DOWN)
  F_kaFrozen input frame x 93 (STILL)
  F_kaUp     synthetic: the input's ball patch moved straight up 7 px/frame until it leaves the top edge, over a
             ball-free background (input, with the ball box replaced by real frame 20 where that box is empty) (UP)
  H_kaReal   real ball-1 from frame 0: gripper holds, then releases ~f29, ball falls to the plank (DOWN)
  H_kaFrozen input frame x 93 (STILL)"""
import sys, os
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
N = 93


def read(p):
    c = cv2.VideoCapture(p); out = []
    while True:
        ok, f = c.read()
        if not ok: return out
        out.append(f)


def write(p, F):
    w = cv2.VideoWriter(p, cv2.VideoWriter_fourcc(*'mp4v'), 24, (832, 480))
    for f in F: w.write(f)
    w.release()


def main(real_dir, out):
    os.makedirs(out, exist_ok=True)
    inp = {s: cv2.imread(os.path.join(HERE, f)) for s, f in
           [('P', 'inp_pend10_mid_f93.png'), ('F', 'inp_ball1_midfall_dd33.png'), ('H', 'inp_ball1_f0_held.png')]}
    for s in 'PFH':
        write(os.path.join(out, f't226_{s}_kaFrozen.mp4'), [inp[s]] * N)
        write(os.path.join(out, f't226_{s}_kaReal.mp4'), read(os.path.join(real_dir, f't226_{s}_real_s0.mp4')))
    # synthetic UP on the F input; ball centre (284,150), D = 21 px
    real = read(os.path.join(real_dir, 't226_F_real_s0.mp4'))
    cx, cy, r = 284, 150, 14
    bg = inp['F'].copy(); box = (slice(cy - 20, cy + 21), slice(cx - 20, cx + 21))
    bg[box] = real[20][box]
    patch = inp['F'][cy - r:cy + r + 1, cx - r:cx + r + 1].copy()
    yy, xx = np.mgrid[-r:r + 1, -r:r + 1]; m = ((xx ** 2 + yy ** 2) <= 11 ** 2).astype(np.float32)
    m = cv2.GaussianBlur(m, (5, 5), 1.0)[..., None]
    F = []
    for t in range(N):
        f = bg.copy(); y = cy - 7 * t
        y0, y1 = y - r, y + r + 1
        if y1 > 0:
            a, b = max(y0, 0), y1
            pa = patch[a - y0:b - y0]; ma = m[a - y0:b - y0]
            reg = f[a:b, cx - r:cx + r + 1].astype(np.float32)
            f[a:b, cx - r:cx + r + 1] = (ma * pa + (1 - ma) * reg).astype(np.uint8)
        F.append(f)
    write(os.path.join(out, 't226_F_kaUp.mp4'), F)
    print('controls written to', out)


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
