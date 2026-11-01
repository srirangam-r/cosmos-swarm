"""zoom on a blinded clip: python3 zb.py <workdir> <id> <f0,f1,..> [x0 x1 y0 y1] -> <workdir>/view/<id>_z.jpg"""
import sys, cv2, numpy as np
W, i, fr = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(',')]
x0, x1, y0, y1 = (int(v) for v in sys.argv[4:8]) if len(sys.argv) > 7 else (200, 400, 0, 300)
c = cv2.VideoCapture(f'{W}/blind/{i}.mp4'); F = []
while True:
    ok, f = c.read()
    if not ok: break
    F.append(f)
th = []
for k in fr:
    x = cv2.convertScaleAbs(F[k][y0:y1, x0:x1], alpha=2.0, beta=12); cv2.putText(x, str(k), (3, 16), 0, 0.55, (0, 255, 255), 1); th.append(x)
rows = [np.hstack(th[k:k + 10] + [np.zeros_like(th[0])] * (10 - len(th[k:k + 10]))) for k in range(0, len(th), 10)]
cv2.imwrite(f'{W}/view/{i}_z.jpg', np.vstack(rows))
