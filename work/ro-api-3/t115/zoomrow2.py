import cv2, numpy as np, sys
out = sys.argv[1]; rows = []
for p in sys.argv[2:]:
    c = cv2.VideoCapture(p); fr = []
    while 1:
        ok, f = c.read()
        if not ok: break
        fr.append(f)
    t = [cv2.resize(fr[i][0:330, 170:430], (120, 152)) for i in range(2, 50, 4)]
    lab = np.zeros((152, 110, 3), np.uint8); cv2.putText(lab, p.split('/')[-1][3:-4], (2, 76), 0, 0.33, (255, 255, 255), 1)
    rows.append(np.hstack([lab] + t))
cv2.imwrite(out, np.vstack(rows))
