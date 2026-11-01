"""Known-answer check for readout.py, built from existing pend10_mid_f93 base clips (rahul-api t193, q8, seeds 21-30).
Arms (seed kept from the source clip):
  SAME  the source clip decoded and re-encoded (mp4v): expect ratio 1, d ~ 0, carryover r_same ~ 1
  FAST  every 2nd frame (47 f at 24 fps): the same motion played 2x fast; expect T ratio 0.5 on ok pairs
  STOP  frame 0 repeated 93 times: expect motion ~ 0 and no period
  base  the source clip as is
Usage: python -I kac.py SRC_DIR OUT_DIR   (SRC_DIR holds rpr_p10f93_base_s*.mp4)"""
import sys, os, glob, json, re
import numpy as np, cv2


def write(path, frames, fps=24):
    h, w = frames[0].shape[:2]
    vw = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
    for f in frames:
        vw.write(np.clip(f, 0, 255).astype(np.uint8))
    vw.release()


def main(src, out):
    os.makedirs(out, exist_ok=True)
    for p in sorted(glob.glob(os.path.join(src, 'rpr_p10f93_base_s*.mp4'))):
        s = int(re.search(r'_s(\d+)\.mp4$', p).group(1))
        c = cv2.VideoCapture(p); F = []
        while True:
            ok, f = c.read()
            if not ok:
                break
            F.append(f)
        arms = dict(base=None, SAME=F, FAST=F[::2], STOP=[F[0]] * len(F))
        for a, fr in arms.items():
            q = os.path.join(out, f'kac_{a}_s{s}.mp4')
            if fr is None:
                if not os.path.exists(q):
                    os.symlink(os.path.abspath(p), q)
            else:
                write(q, fr)
            json.dump(dict(name=f'kac_{a}_s{s}', seed=s, extra_params=dict(arm=a, seed=s, source=os.path.basename(p))),
                      open(q[:-4] + '.json', 'w'))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
