"""Make blind per-clip strips (f2..92 step 6, pendulum crop) with random ids; key saved separately."""
import cv2, numpy as np, sys, json, random, os
out = sys.argv[1]; clips = sys.argv[2:]; random.seed(int.from_bytes(os.urandom(4), 'little'))
ids = random.sample(range(100, 1000), len(clips)); key = {}
os.makedirs(out, exist_ok=True)
for i, p in zip(ids, clips):
    c = cv2.VideoCapture(p); fr = []
    while 1:
        ok, f = c.read()
        if not ok: break
        fr.append(f)
    t = [cv2.resize(fr[k][0:330, 170:430], (104, 132)) for k in range(2, 93, 6)]
    cv2.imwrite(f"{out}/b{i}.jpg", np.hstack(t)); key[f"b{i}"] = p
json.dump(key, open(out + "_KEY.json", "w"), indent=1)
