import cv2, numpy as np, sys
p, out = sys.argv[1], sys.argv[2]; step = int(sys.argv[3]) if len(sys.argv) > 3 else 2
c = cv2.VideoCapture(p); fr = []
while 1:
    ok, f = c.read()
    if not ok: break
    fr.append(f)
idx = list(range(0, len(fr), step))[:48]
t = []
for i in idx:
    x = cv2.resize(fr[i][0:330, 170:430], (130, 165)); cv2.putText(x, str(i), (2, 14), 0, 0.45, (0, 0, 255), 1); t.append(x)
t += [np.zeros_like(t[0])] * (-len(t) % 12)
cv2.imwrite(out, np.vstack([np.hstack(t[k:k + 12]) for k in range(0, len(t), 12)]))
