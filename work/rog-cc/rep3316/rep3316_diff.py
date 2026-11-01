# Blind visual aid: per row, crop f76, f92, |f92-f76|x4, |f84-f76|x4, |f92-f84|x4. Labels hex+row only.
import sys, os, random, numpy as np, cv2
sys.path.insert(0, 'cosmos-swarm/work/rog-cc/rep3316')
import rep3316 as R
C = R.collect('endstate/clips'); rng = random.Random(3316); rows = []
for k in sorted(C):
    d = C[k]; arms = ["F", "R", "N"]; rng.shuffle(arms); hx = "%06x" % rng.getrandbits(24)
    for lab, a in zip("ABC", arms):
        F = R.read(d[a]); x0, y0, x1, y1 = R.CROP
        g = lambda i: F[i][y0:y1, x0:x1].astype(np.int16)
        df = lambda i, j: np.clip(np.abs(g(i) - g(j)) * 4, 0, 255).astype(np.uint8)
        ts = [g(76).astype(np.uint8), g(92).astype(np.uint8), df(92, 76), df(84, 76), df(92, 84)]
        ts = [cv2.resize(t, (160, 220)) for t in ts]
        r = np.hstack(ts); cv2.putText(r, f"{hx} {lab}", (3, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        rows.append(r); rows.append(np.full((4, r.shape[1], 3), 255, np.uint8))
half = len(rows) // 2
cv2.imwrite('rep3316_zoom/diff_1.jpg', np.vstack(rows[:half]), [cv2.IMWRITE_JPEG_QUALITY, 85])
cv2.imwrite('rep3316_zoom/diff_2.jpg', np.vstack(rows[half:]), [cv2.IMWRITE_JPEG_QUALITY, 85])
