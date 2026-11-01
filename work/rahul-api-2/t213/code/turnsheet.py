"""Contact sheet of native frames near each turning point, with rodtrack's tracked rod (pivot->tip) drawn. QC only."""
import sys, json, numpy as np, cv2
res = json.load(open(sys.argv[1])); amp = json.load(open(sys.argv[2]))['per_clip']; out = sys.argv[3]
for name in sys.argv[4:]:
    r = res[name]; p = np.array(r['pivot']); s = r['series']; t = np.array(s['t']); th = np.array(s['theta']); L = np.array(s['L'])
    cap = cv2.VideoCapture(f'clips/{name}.mp4'); F = []
    while True:
        ok, f = cap.read()
        if not ok: break
        F.append(f)
    # frames: every 4th frame f0..f92, cropped around pivot
    tiles = []
    for i in range(0, min(len(F), 93), 4):
        im = F[i].copy(); k = np.where(np.isclose(t * 24, i))[0]
        cv2.circle(im, tuple(int(v) for v in p), 4, (0, 0, 255), -1)
        if len(k):
            a = np.radians(th[k[0]]); tip = p + L[k[0]] * np.array([-np.sin(a), np.cos(a)])
            cv2.line(im, tuple(int(v) for v in p), tuple(int(v) for v in tip), (0, 255, 0), 1)
            lab = f'f{i} {th[k[0]]:+.0f}'
        else: lab = f'f{i} --'
        c = im[0:330, 140:520]; cv2.putText(c, lab, (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        tiles.append(c)
    rows = [np.hstack(tiles[j:j + 6] + [np.zeros_like(tiles[0])] * (6 - len(tiles[j:j + 6]))) for j in range(0, len(tiles), 6)]
    sheet = np.vstack(rows); sheet = cv2.resize(sheet, None, fx=0.6, fy=0.6)
    cv2.imwrite(f'{out}/{name}_sheet.jpg', sheet, [cv2.IMWRITE_JPEG_QUALITY, 80])
    print(name, 'turning', amp[name].get('turn_theta'))
