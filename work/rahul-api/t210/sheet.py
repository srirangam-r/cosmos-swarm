#!/usr/bin/env python3
"""Contact sheet per clip: rows real / base / R / N (seed s), columns frames 0,4,8,12,16. Usage: sheet.py <devset> <clips> <clip_id> <seed> <out.jpg>"""
import sys, os, cv2, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../tools/robot_pred"))
import score as S
dev, clips, cid, seed, outp = sys.argv[1:6]
rows = [("real", S.read(os.path.join(dev, cid, "real.mp4"))[:17])]
for a in ("base", "R", "N"):
    rows.append((a, S.read(os.path.join(clips, f"t210_{a}_{cid}_s{seed}.mp4"))))
img = []
for lab, v in rows:
    r = np.concatenate([v[i] for i in (0, 4, 8, 12, 16)], axis=1)[:, :, ::-1].copy()
    cv2.putText(r, lab, (4, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    img.append(r)
cv2.imwrite(outp, np.concatenate(img, axis=0), [cv2.IMWRITE_JPEG_QUALITY, 85])
