#!/usr/bin/env python3
"""Task 98 release proxy for GAUGE ball1 frame-0 clips (832x480).

Per clip:
  plank_dark[t]  = # pixels inside the plank (bright wood in frame 0) that are dark (<DARK) in frame t
                   -> a black ball that reaches the plank makes a dark blob there. A clip counts as RELEASED if
                      plank_dark >= MINPX for >= 3 consecutive frames.
  grip_diff[t]   = mean |gray_t - gray_0| in the ball's start box (in the gripper).
  f0_psnr        = PSNR(decoded frame 0, conditioning image); f1_4_psnr = mean PSNR of frames 1-4 vs image.
Also writes a contact sheet (every 3rd frame, first 48 frames) per clip for eye-checking.
Usage: python analyze.py IMAGE.png OUT.json clip1.mp4 [clip2.mp4 ...]  (real 1280x720 clips are letterboxed)
"""
import json, sys
import cv2
import numpy as np

DARK, BRIGHT, MINPX = 70, 150, 40
PLANK_BOX = (150, 300, 410, 425)   # x0, y0, x1, y1 (plank strip in the 832x480 GAUGE ball1 frame)
BALL_BOX = (262, 98, 305, 140)     # ball held in the gripper at frame 0


def read(path):
    cap = cv2.VideoCapture(path); fr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if f.shape[:2] != (480, 832):  # real GAUGE 1280x720 -> 832x468 + 6 px pads (GAUGE App. C.1.1)
            f = cv2.resize(f, (832, 468), interpolation=cv2.INTER_AREA)
            f = cv2.copyMakeBorder(f, 6, 6, 0, 0, cv2.BORDER_CONSTANT, value=0)
        fr.append(f)
    return fr


def psnr(a, b):
    m = np.mean((a.astype(np.float32) - b.astype(np.float32)) ** 2)
    return float(10 * np.log10(255 ** 2 / max(m, 1e-6)))


def main():
    img = cv2.imread(sys.argv[1]); out = sys.argv[2]; res = {}
    g0 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    x0, y0, x1, y1 = PLANK_BOX
    plank = np.zeros_like(g0, bool); plank[y0:y1, x0:x1] = g0[y0:y1, x0:x1] > BRIGHT
    bx0, by0, bx1, by1 = BALL_BOX
    for p in sys.argv[3:]:
        fr = read(p)
        gs = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in fr]
        pd = [int(((g < DARK) & plank).sum()) for g in gs]
        def blob(g):
            m = ((g < DARK) & plank).astype(np.uint8)
            n, _, st, _ = cv2.connectedComponentsWithStats(m)
            return int(st[1:, cv2.CC_STAT_AREA].max()) if n > 1 else 0
        bl = [blob(g) for g in gs]
        gd = [float(np.abs(g[by0:by1, bx0:bx1].astype(float) - g0[by0:by1, bx0:bx1]).mean()) for g in gs]
        run, best, first = 0, 0, None
        for t, v in enumerate(pd):
            run = run + 1 if v >= MINPX else 0
            if run >= 3 and first is None:
                first = t - 2
            best = max(best, run)
        res[p.split('/')[-1]] = dict(
            n=len(fr), released=first is not None, first_plank_frame=first, max_plank_dark=max(pd),
            max_blob=max(bl), plank_dark_frames=sum(v >= MINPX for v in pd), grip_diff_max=round(max(gd), 1),
            grip_diff_late=round(float(np.mean(gd[-20:])), 1),
            f0_psnr=round(psnr(fr[0], img), 2), f1_4_psnr=round(float(np.mean([psnr(f, img) for f in fr[1:5]])), 2))
        sheet = [cv2.resize(fr[t], (277, 160)) for t in range(0, min(48, len(fr)), 3)]
        sheet += [np.zeros_like(sheet[0])] * (-len(sheet) % 4)
        rows = [np.hstack(sheet[i:i + 4]) for i in range(0, len(sheet), 4)]
        cv2.imwrite(p.rsplit('.', 1)[0] + '_sheet.jpg', np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])
        print(p.split('/')[-1], res[p.split('/')[-1]], flush=True)
    json.dump(res, open(out, 'w'), indent=1)


if __name__ == '__main__':
    main()
