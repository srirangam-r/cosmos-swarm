# blind aid: late-window (f72-92 step 4) native crops y250-420,x120-520 + |f92-f72|x4 tile, 4 clips/image, labelled by hex only
import sys, json, os, glob, cv2, numpy as np
out_dir, clips, dst = sys.argv[1], sys.argv[2], sys.argv[3]
key = json.load(open(os.path.join(out_dir, "UNBLIND_key.json")))  # used only to locate files; hex labels only are drawn
os.makedirs(dst, exist_ok=True)
hexes = sorted(key)
def frames(p):
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    return fr
rows = []
for h in hexes:
    fr = frames(os.path.join(clips, key[h] + ".mp4"))
    tl = []
    for i in range(72, 93, 4):
        t = fr[i][250:420, 120:520].copy(); cv2.putText(t, f"f{i}", (360, 162), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1); tl.append(t)
    d = np.clip(np.abs(fr[92][250:420, 120:520].astype(int) - fr[72][250:420, 120:520].astype(int)) * 4, 0, 255).astype(np.uint8)
    cv2.putText(d, "|92-72|x4", (290, 162), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1); tl.append(d)
    r = np.hstack(tl); cv2.putText(r, h, (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2); rows.append(r)
for j in range(0, len(rows), 4):
    cv2.imwrite(os.path.join(dst, f"z{j//4:02d}.jpg"), np.vstack(rows[j:j+4]), [cv2.IMWRITE_JPEG_QUALITY, 85])
