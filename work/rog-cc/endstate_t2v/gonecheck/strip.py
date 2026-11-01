import sys, cv2, numpy as np
# usage: strip.py out.jpg clip1 clip2 ... ; rows = clips, cols = frames 0..92 step 8 (plus 92)
FR = list(range(0, 93, 8)) + [92]
FR = sorted(set(FR)); TW, TH = 160, 92
rows = []
for p in sys.argv[2:]:
    cap = cv2.VideoCapture(p); fr = {}; i = 0
    while True:
        ok, x = cap.read()
        if not ok: break
        if i in FR: fr[i] = cv2.resize(x, (TW, TH), interpolation=cv2.INTER_AREA)
        i += 1
    r = np.concatenate([fr.get(f, np.zeros((TH, TW, 3), np.uint8)) for f in FR], axis=1)
    lab = np.zeros((14, r.shape[1], 3), np.uint8); cv2.putText(lab, p.split('/')[-1], (2, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)
    rows += [lab, r]
cv2.imwrite(sys.argv[1], np.concatenate(rows, axis=0), [cv2.IMWRITE_JPEG_QUALITY, 85])
print(FR)
