# blind aid: native crop x190-370,y60-420 of frames a..b (step s) for one hex, labelled by hex only
import sys, json, cv2, numpy as np, os
d, out, h, a, b = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
s = int(sys.argv[6]) if len(sys.argv) > 6 else 1
k = json.load(open(os.path.join(os.path.dirname(out), "blind", "UNBLIND_key.json")))["key"]
cap = cv2.VideoCapture(os.path.join(d, k[h]["file"])); fr = []
while True:
    ok, f = cap.read()
    if not ok: break
    fr.append(f)
tiles = []
for i in range(a, b + 1, s):
    t = fr[i][60:420, 190:370].copy()
    cv2.putText(t, f"{h} f{i}", (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
    tiles.append(t)
rows = [np.hstack(tiles[j:j+10] + [np.zeros_like(tiles[0])] * (10 - len(tiles[j:j+10]))) for j in range(0, len(tiles), 10)]
cv2.imwrite(out, np.vstack(rows))
