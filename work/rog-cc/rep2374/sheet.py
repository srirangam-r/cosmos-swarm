# Contact sheet: agy-3 #2374 ROIs overlaid on GAUGE task-24 eval clips (frames 0,8,16,30,60,92).
import cv2, sys, json, numpy as np
CL = sys.argv[1]; OUT = sys.argv[2]; ids = sys.argv[3].split(',')
ROIS = {'grip': (90,150,260,320), 'corr': (160,320,250,330), 'plank': (330,410,240,340)}  # y0,y1,x0,x1 as given in #2374
FR = [0, 8, 16, 30, 60, 92]
rows = []
for cid in ids:
    cap = cv2.VideoCapture(f'{CL}/{cid}.mp4'); fs = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fs.append(f)
    tiles = []
    for i in FR:
        f = fs[min(i, len(fs)-1)].copy()
        for nm,(y0,y1,x0,x1) in ROIS.items():
            cv2.rectangle(f, (x0,y0), (x1,y1), (0,0,255), 2); cv2.putText(f, nm, (x0+2,y0+14), 0, 0.45, (0,0,255), 1)
        cv2.putText(f, f'{cid} f{i}', (8,470), 0, 0.7, (0,255,0), 2)
        tiles.append(cv2.resize(f, (416,240)))
    rows.append(np.hstack(tiles))
cv2.imwrite(OUT, np.vstack(rows), [cv2.IMWRITE_JPEG_QUALITY, 80])
print(fs[0].shape, len(fs))
