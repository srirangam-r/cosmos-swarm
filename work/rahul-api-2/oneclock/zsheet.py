"""QC zoom sheet (no numbers): 2 clips per jpg; per clip frames 0-46 step 2 at full res, corridor x200-360 y60-420, 2 rows x 12.
usage: zsheet.py outdir prefix clip1.mp4 clip2.mp4 ..."""
import cv2, numpy as np, sys, os
out, pre, files = sys.argv[1], sys.argv[2], sys.argv[3:]
def clipimg(p):
    c = cv2.VideoCapture(p); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(f)
    rows = []
    for r in range(2):
        tiles = []
        for i in range(24 * r, 24 * r + 24, 2):
            t = F[i][60:420, 200:360].copy()
            cv2.putText(t, str(i), (3, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1); tiles.append(t)
        rows.append(np.concatenate(tiles, 1))
    bar = np.zeros((26, rows[0].shape[1], 3), np.uint8)
    cv2.putText(bar, os.path.basename(p)[:-4], (4, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 1)
    return np.concatenate([bar] + rows, 0)
for k in range(0, len(files), 2):
    cv2.imwrite(os.path.join(out, f'{pre}{k//2:02d}.jpg'), np.concatenate([clipimg(f) for f in files[k:k+2]], 0), [cv2.IMWRITE_JPEG_QUALITY, 88])
