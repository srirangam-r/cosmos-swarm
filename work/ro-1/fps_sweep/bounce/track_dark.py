"""ro-1 independent bounce tracker (no shared-tool code).
Per-pixel temporal median background over frames >= skip; ball = largest blob that is
DARKER than background by > thr (ball is black). Outputs per-frame centroid (x,y), area."""
import sys, json, numpy as np, cv2
path, out = sys.argv[1], sys.argv[2]
skip = int(sys.argv[3]) if len(sys.argv) > 3 else 3
thr = float(sys.argv[4]) if len(sys.argv) > 4 else 35
cap = cv2.VideoCapture(path); F = []
while True:
    ok, f = cap.read()
    if not ok: break
    F.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32))
F = np.stack(F); bg = np.median(F[skip:], axis=0)
rows = []; prev = None
for i, g in enumerate(F):
    d = (bg - g)  # positive where darker than background
    m = (cv2.GaussianBlur(d, (5, 5), 0) > thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m)
    best = None
    for k in range(1, n):
        a = st[k, cv2.CC_STAT_AREA]
        if a < 80 or a > 6000: continue
        w, h = st[k, cv2.CC_STAT_WIDTH], st[k, cv2.CC_STAT_HEIGHT]
        if max(w, h) > 2.5 * min(w, h): continue
        score = a - (0.5 * np.hypot(*(cen[k] - prev)) if prev is not None else 0)
        if best is None or score > best[0]: best = (score, k)
    if best is None:
        rows.append(dict(f=i, x=None, y=None, area=0)); continue
    k = best[1]; prev = cen[k]
    rows.append(dict(f=i, x=float(cen[k][0]), y=float(cen[k][1]), area=int(st[k, cv2.CC_STAT_AREA]),
                     w=int(st[k, cv2.CC_STAT_WIDTH]), h=int(st[k, cv2.CC_STAT_HEIGHT]),
                     bottom=float(st[k, cv2.CC_STAT_TOP] + st[k, cv2.CC_STAT_HEIGHT])))
json.dump(dict(clip=path, skip=skip, thr=thr, n=len(F), track=rows), open(out, "w"), indent=0)
for r in rows: print(r["f"], r.get("x") and round(r["x"]), r.get("y") and round(r["y"]), r["area"], r.get("w"), r.get("h"))
