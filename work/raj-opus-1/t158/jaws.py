"""jaws zoom (2x) for several blinded clips: python3 jaws.py <workdir> <out.jpg> <id>:<f,f,..> [<id>:<f,..> ...]; crop x240-380 y50-190"""
import sys, cv2, numpy as np
W, out = sys.argv[1], sys.argv[2]; rows = []
for spec in sys.argv[3:]:
    i, fr = spec.split(':'); fr = [int(x) for x in fr.split(',')]
    c = cv2.VideoCapture(f'{W}/blind/{i}.mp4'); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    th = []
    for k in fr:
        x = cv2.resize(cv2.convertScaleAbs(F[k][50:190, 240:380], alpha=2.0, beta=12), (210, 210)); cv2.putText(x, f'{i[:4]} {k}', (3, 16), 0, 0.5, (0, 255, 255), 1); th.append(x)
    rows.append(np.hstack(th + [np.zeros_like(th[0])] * (10 - len(th))))
cv2.imwrite(out, np.vstack(rows))
