"""Task 158 coding view: python3 compose.py <workdir> <id> [<id> ...] -> <workdir>/view/<id>.jpg
Brightened corridor x190-430, y0-440 (f0-40 every frame, then every 4th), plus whole frames every 8th (brightened).
Reads only the blinded hard link <workdir>/blind/<id>.mp4, so no arm/w/seed label is shown."""
import sys, cv2, numpy as np
W = sys.argv[1]
for i in sys.argv[2:]:
    c = cv2.VideoCapture(f'{W}/blind/{i}.mp4'); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(cv2.convertScaleAbs(f, alpha=1.7, beta=10))
    idx = list(range(0, 41)) + list(range(44, len(F), 4)); th = []
    for k in idx:
        t = cv2.resize(F[k][0:440, 190:430], (120, 220)); cv2.putText(t, str(k), (2, 12), 0, 0.4, (0, 255, 255), 1); th.append(t)
    while len(th) % 10: th.append(np.zeros_like(th[0]))
    top = np.vstack([np.hstack(th[k:k + 10]) for k in range(0, len(th), 10)])
    fu = []
    for k in range(0, len(F), 8):
        t = cv2.resize(F[k], (205, 118)); cv2.putText(t, str(k), (2, 12), 0, 0.4, (0, 255, 255), 1); fu.append(t)
    while len(fu) % 6: fu.append(np.zeros_like(fu[0]))
    bot = np.vstack([np.hstack(fu[k:k + 6]) for k in range(0, len(fu), 6)])
    bot = np.hstack([bot, np.zeros((bot.shape[0], top.shape[1] - bot.shape[1], 3), np.uint8)]) if bot.shape[1] < top.shape[1] else bot[:, :top.shape[1]]
    cv2.imwrite(f'{W}/view/{i}.jpg', np.vstack([top, bot]), [cv2.IMWRITE_JPEG_QUALITY, 88])
