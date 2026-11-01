#!/usr/bin/env python3
"""QC overlay: for F/H clips, draw the measured firstfall track (cy from measures json, cx not stored -> mark at seed x)
on frames 0,4,8,16,32,48,64,84,92 cropped to the ball corridor. usage: qc_track.py measures.json clip_dir out_dir [names...]"""
import sys, os, json
import numpy as np, cv2
M = json.load(open(sys.argv[1])); cd, od = sys.argv[2], sys.argv[3]; os.makedirs(od, exist_ok=True)
names = sys.argv[4:] or [k for k in M if M[k]['scene'] in 'FH']
FR = [0, 4, 8, 16, 32, 48, 64, 84, 92]
for n in names:
    r = M[n]; c = cv2.VideoCapture(os.path.join(cd, n + '.mp4')); F = []
    while True:
        ok, f = c.read()
        if not ok: break
        F.append(cv2.resize(f, (832, 480)) if f.shape[:2] != (480, 832) else f)
    cy = r['cy']; tiles = []
    for k in FR:
        f = F[min(k, len(F) - 1)].copy()
        y = cy[k] if k < len(cy) else None
        if y is not None: cv2.circle(f, (284, int(y)), 12, (0, 0, 255), 2)
        cv2.line(f, (300, int(r['y0'])), (320, int(r['y0'])), (0, 255, 0), 2)
        t = f[0:480, 180:400]; cv2.putText(t, f'f{k}', (2, 14), 0, 0.5, (0, 255, 255), 1); tiles.append(t)
    sheet = np.hstack(tiles)
    hdr = np.zeros((24, sheet.shape[1], 3), np.uint8)
    cv2.putText(hdr, f"{n} dy8={r.get('dy8') if r.get('dy8') is None else round(r['dy8'])} ({r.get('dy8_src')}) dyEnd={r.get('dyEnd') if r.get('dyEnd') is None else round(r['dyEnd'])} ({r.get('dyEnd_src')})", (4, 17), 0, 0.55, (255, 255, 255), 1)
    cv2.imwrite(os.path.join(od, n + '.jpg'), cv2.resize(np.vstack([hdr, sheet]), None, fx=0.7, fy=0.7), [cv2.IMWRITE_JPEG_QUALITY, 80])
print('ok', len(names))
