"""Blind strips at step 3 (f2..92, 31 frames) for finer temporal view; random ids, key separate."""
import cv2, numpy as np, sys, json, random, os
out = sys.argv[1]; clips = sys.argv[2:]; random.seed(int.from_bytes(os.urandom(4), 'little'))
ids = random.sample(range(100, 1000), len(clips)); key = {}; rows = []
for i, p in sorted(zip(ids, clips)):
    c = cv2.VideoCapture(p); fr = []
    while 1:
        ok, f = c.read()
        if not ok: break
        fr.append(f)
    t = [cv2.resize(fr[k][0:330, 170:430], (56, 71)) for k in range(2, 93, 3)]
    lab = np.zeros((71, 44, 3), np.uint8); cv2.putText(lab, str(i), (2, 40), 0, 0.45, (255, 255, 255), 1)
    rows.append(np.hstack([lab] + t)); key[f"b{i}"] = p
for s in range(0, len(rows), 12): cv2.imwrite(f"{out}_sheet{s//12}.jpg", np.vstack(rows[s:s+12]))
json.dump(key, open(out + "_KEY.json", "w"), indent=1)
