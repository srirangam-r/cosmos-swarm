# Blind zoom sheets: reproduces rep3316.py's shuffle (rng 3316) internally; outputs only hex + row letter, never arm names.
import sys, os, random, numpy as np, cv2
sys.path.insert(0, 'cosmos-swarm/work/rog-cc/rep3316')
import rep3316 as R
C = R.collect('endstate/clips'); rng = random.Random(3316)
for k in sorted(C):
    d = C[k]; arms = ["F", "R", "N"]; rng.shuffle(arms); hx = "%06x" % rng.getrandbits(24)
    assert os.path.exists(f'rep3316_blind/{hx}.jpg'), hx
    rest_rows, art_rows = [], []
    for lab, a in zip("ABC", arms):
        F = R.read(d[a]); x0, y0, x1, y1 = R.CROP
        tiles = []
        for i in range(76, 93, 2):
            t = F[i][y0:y1, x0:x1].copy(); cv2.putText(t, f"{lab}{i}", (3, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2); tiles.append(t)
        rest_rows.append(np.hstack(tiles)); rest_rows.append(np.full((6, rest_rows[-1].shape[1], 3), 255, np.uint8))
        fr = []
        for i in list(range(0, 92, 8)) + [92]:
            t = cv2.resize(F[i], (277, 160)); cv2.putText(t, f"{lab}{i}", (3, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2); fr.append(t)
        art_rows += [np.hstack(fr[:6]), np.hstack(fr[6:12]), np.full((6, 277*6, 3), 255, np.uint8)]
    cv2.imwrite(f'rep3316_zoom/{hx}_rest.jpg', np.vstack(rest_rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    cv2.imwrite(f'rep3316_zoom/{hx}_art.jpg', np.vstack(art_rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(hx, 'ok')
