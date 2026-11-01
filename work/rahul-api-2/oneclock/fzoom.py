"""Per-frame zoom for borderline QC (no numbers): frames a..b step 1, corridor x200-360 y60-420, rows of 12. usage: fzoom.py out.jpg clip.mp4 a b"""
import cv2, numpy as np, sys
out, p, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
c = cv2.VideoCapture(p); F = []
while True:
    ok, f = c.read()
    if not ok: break
    F.append(f)
tiles = []
for i in range(a, b + 1):
    t = F[i][60:420, 200:360].copy(); cv2.putText(t, str(i), (3, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 1); tiles.append(t)
while len(tiles) % 12: tiles.append(np.zeros_like(tiles[0]))
img = np.concatenate([np.concatenate(tiles[k:k+12], 1) for k in range(0, len(tiles), 12)], 0)
cv2.imwrite(out, img, [cv2.IMWRITE_JPEG_QUALITY, 88])
