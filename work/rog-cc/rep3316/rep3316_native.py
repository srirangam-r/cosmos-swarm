import sys, os, random, numpy as np, cv2
sys.path.insert(0, 'cosmos-swarm/work/rog-cc/rep3316')
import rep3316 as R
want = {('668313','A'),('668313','C'),('d2e60f','B'),('a48f63','B')}
C = R.collect('endstate/clips'); rng = random.Random(3316); rows = []
for k in sorted(C):
    d = C[k]; arms = ["F", "R", "N"]; rng.shuffle(arms); hx = "%06x" % rng.getrandbits(24)
    for lab, a in zip("ABC", arms):
        if (hx, lab) not in want: continue
        F = R.read(d[a]); ts = []
        for i in range(4, 41, 3):
            t = cv2.resize(F[i][0:330, 100:520], (168, 132)); cv2.putText(t, f"{hx}{lab}{i}", (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1); ts.append(t)
        rows.append(np.hstack(ts))
cv2.imwrite('rep3316_zoom/native_early.jpg', np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 85])
