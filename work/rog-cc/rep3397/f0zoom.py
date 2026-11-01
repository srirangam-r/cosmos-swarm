# blind aid: f0 and f12 native crops (x220-340,y40-200) at 1.5x for a list of hexes, labelled by hex only
import sys, json, cv2, numpy as np, os
d, out, hexes = sys.argv[1], sys.argv[2], sys.argv[3:]
k = json.load(open(os.path.join(os.path.dirname(out), "blind", "UNBLIND_key.json")))["key"]
tiles = []
for h in hexes:
    cap = cv2.VideoCapture(os.path.join(d, k[h]["file"])); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    row = []
    for i in (0, 12, 92):
        t = cv2.resize(fr[i][40:200, 220:340], None, fx=1.5, fy=1.5)
        cv2.putText(t, f"{h} f{i}", (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        row.append(t)
    tiles.append(np.hstack(row))
cv2.imwrite(out, np.vstack(tiles) if len(tiles) <= 4 else np.hstack([np.vstack(tiles[:len(tiles)//2+len(tiles)%2]), np.vstack(tiles[len(tiles)//2+len(tiles)%2:] + ([np.zeros_like(tiles[0])] if len(tiles)%2 else []))]))
