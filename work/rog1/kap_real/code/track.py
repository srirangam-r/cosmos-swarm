# rog1 kap: track the dark ball on the light plank in real GAUGE bouncing-ball videos.
# bg = per-pixel median of frames 0-9 (ball still held high). Ball = largest dark-change blob in lower half.
import cv2, numpy as np, json, sys, glob, os
src = sys.argv[1]; out = sys.argv[2]
res = {}
for vp in sorted(glob.glob(os.path.join(src, 'video', '*.mp4')), key=lambda p: int(os.path.basename(p)[:-4])):
    cid = os.path.basename(vp)[:-4]
    cap = cv2.VideoCapture(vp); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    fr = np.array(fr); H, W = fr.shape[1:]
    # duplicate flags (25 fps content in 30 fps container)
    d = np.array([np.abs(fr[i].astype(int) - fr[i-1]).mean() for i in range(1, len(fr))])
    dup = [False] + [bool(v) for v in (d < 0.1 * np.median(d))]
    bg = np.median(fr[:10], axis=0).astype(np.int16)
    trk = []
    for i, g in enumerate(fr):
        diff = bg - g.astype(np.int16)          # positive where frame darker than bg
        m = (diff > 40).astype(np.uint8)
        m[:int(H * 0.45)] = 0                   # ignore gripper / upper scene
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        n, lab, st, cen = cv2.connectedComponentsWithStats(m)
        best = None
        for k in range(1, n):
            x, y, w, h, a = st[k]
            if a < 300 or a > 6000 or w > 3 * h or h > 3 * w: continue
            if best is None or a > best[4]: best = (x, y, w, h, a, *cen[k])
        trk.append(None if best is None else [float(best[5]), float(best[6]), int(best[2]), int(best[3]), int(best[4])])
    res[cid] = {'n': len(fr), 'W': W, 'H': H, 'dup': dup, 'trk': trk}
    vis = sum(t is not None for t in trk)
    print(cid, len(fr), 'visible', vis, 'first', next((i for i, t in enumerate(trk) if t), None),
          'last', max((i for i, t in enumerate(trk) if t), default=None), flush=True)
json.dump(res, open(out, 'w'))
