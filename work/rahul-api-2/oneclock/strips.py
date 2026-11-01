"""QC strips (no numbers): ball corridor x 200-360, y 60-420; row1 f0-46 every 2 f, row2 f48-92 every 2 f; half size."""
import cv2, numpy as np, sys, os
for p in sys.argv[2:]:
    c = cv2.VideoCapture(p); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    def row(idx):
        tiles = []
        for i in idx:
            t = F[i][60:420, 200:360].copy() if i < len(F) else np.zeros((360, 160, 3), np.uint8)
            cv2.putText(t, str(i), (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1); tiles.append(t)
        return np.concatenate(tiles, 1)
    img = np.concatenate([row(range(0, 47, 2)), row(range(48, 95, 2))], 0)
    img = cv2.resize(img, None, fx=0.5, fy=0.5)
    cv2.imwrite(os.path.join(sys.argv[1], os.path.basename(p)[:-4] + '.jpg'), img, [cv2.IMWRITE_JPEG_QUALITY, 85])
