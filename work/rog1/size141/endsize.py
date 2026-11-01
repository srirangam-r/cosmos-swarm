"""endsize v1 (rog1): apparent diameter of the resting object at the end of a clip.

Method (fixed before looking at any task-141 code or result beyond the REST label):
- frames f0 and the last K=13 frames (f176..f188 for 189-frame clips), RGB float.
- change mask: max-channel |f_t - f0| > THR (35/255), restricted to the table ROI (y >= 250).
- "static" mask = pixels changed in ALL of the last K frames AND whose value varies little across them
  (per-pixel std over the K frames < 12) -> stationary new content (the resting ball and its contact shadow).
- connected components (8-conn) after 3x3 open; keep components with area >= 40 px.
- 7x7 close to merge ball fragments; the object = the LARGEST component with bbox fill >= 0.40 and aspect w/h in [0.6,1.6].
  (v1 draft picked the darkest; changed after 2 test clips (F_s1, F_s3) picked 7-11 px fragments.)
- diameter = bbox width (horizontal extent; robust to the contact shadow, which spreads mostly vertically
  below the ball in this camera). Also reports equivalent-circle diameter and bbox height.
Outputs JSON lines and a QC crop per clip.
Limitations: a dark ball on the dark breadboard may produce weak diff; such clips are flagged (no component).
"""
import sys, json, os
import numpy as np, cv2

THR, STD_MAX, K, Y0 = 35, 12, 13, 250


def read_frames(path, idxs):
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    want = set(i if i >= 0 else n + i for i in idxs)
    out, i = {}, 0
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        if i in want:
            out[i] = fr.astype(np.float32)
        i += 1
    return out, i


def measure(path, qc_dir=None):
    frames, n = read_frames(path, [0] + list(range(-K, 0)))
    f0 = frames[0]
    last = [frames[i] for i in sorted(frames) if i > 0][-K:]
    stack = np.stack(last)  # K,H,W,3
    diff = np.abs(stack - f0[None]).max(-1)  # K,H,W
    changed = (diff > THR).all(0)
    stable = stack.mean(-1).std(0) < STD_MAX
    m = (changed & stable).astype(np.uint8)
    m[:Y0] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    nc, lab, st, cen = cv2.connectedComponentsWithStats(m, 8)
    V = last[-1].max(-1)
    cands = []
    for c in range(1, nc):
        x, y, w, h, a = st[c]
        if a < 40:
            continue
        fill = a / float(w * h)
        if fill < 0.40 or not (0.6 <= w / float(h) <= 1.6):
            continue
        meanv = float(V[lab == c].mean())
        cands.append(dict(x=int(x), y=int(y), w=int(w), h=int(h), area=int(a), fill=round(fill, 3),
                          meanV=round(meanv, 1), d_eq=round(2 * np.sqrt(a / np.pi), 1)))
    cands.sort(key=lambda d: -d['area'])
    res = dict(clip=os.path.basename(path), nframes=n, n_cands=len(cands))
    if cands:
        b = cands[0]
        res.update(obj=b, d_w=b['w'], d_h=b['h'], d_eq=b['d_eq'], others=cands[1:4])
    if qc_dir:
        img = last[-1].astype(np.uint8).copy()
        for j, c in enumerate(cands[:4]):
            col = (0, 0, 255) if j == 0 else (0, 255, 255)
            cv2.rectangle(img, (c['x'], c['y']), (c['x'] + c['w'], c['y'] + c['h']), col, 1)
        cv2.imwrite(os.path.join(qc_dir, res['clip'].replace('.mp4', '_qc.jpg')), img[200:, :700])
    return res


if __name__ == '__main__':
    qc = sys.argv[1]
    os.makedirs(qc, exist_ok=True)
    for p in sys.argv[2:]:
        print(json.dumps(measure(p, qc)), flush=True)
