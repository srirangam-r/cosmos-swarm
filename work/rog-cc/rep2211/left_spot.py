"""Independent check of ro-1 #2211 'fell' codes on the 84 task-24 GAUGE-eval clips.
Ball = black sphere on a white wall at f0 (~(529,46), D~47 px, 832x480).
Per clip: M0 = dark pixels (gray<70) within 40 px of the f0 dark-blob centroid near (529,46).
 persist(t) = fraction of M0 still dark at frame t.  left = persist<0.5 for >=3 consecutive frames.
 Wall-region tracker: largest dark component in the wall area (y<318, x 160..672, gray<70, area>=150 px);
 drop = max(cy(t)) - cy(0) over frames where it's found; lost = frames with no wall blob.
 fell = left AND (drop > 60 px OR the blob is lost from the wall for >=3 frames)  (ball reached the dark table).
Usage: python3 left_spot.py CLIPDIR EYE_CODES.csv OUT.json
"""
import sys, os, json, csv
import numpy as np, cv2

def analyse(path):
    cap = cv2.VideoCapture(path); frames = []
    while True:
        ok, f = cap.read()
        if not ok: break
        frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
    g0 = frames[0]
    yy, xx = np.mgrid[0:g0.shape[0], 0:g0.shape[1]]
    near = (yy - 46) ** 2 + (xx - 529) ** 2 < 45 ** 2
    dark0 = (g0 < 70) & near
    if dark0.sum() < 50:
        return dict(n=len(frames), f0_dark=int(dark0.sum()), error='no f0 ball')
    cy0, cx0 = yy[dark0].mean(), xx[dark0].mean()
    M0 = ((yy - cy0) ** 2 + (xx - cx0) ** 2 < 40 ** 2) & (g0 < 70)
    persist, cys, run, first_left = [], [], 0, None
    wall = np.zeros_like(g0, bool); wall[:318, 160:672] = True
    lost_run, max_lost_run = 0, 0
    for t, g in enumerate(frames):
        p = float(((g < 70) & M0).sum() / M0.sum()); persist.append(p)
        run = run + 1 if p < 0.5 else 0
        if run >= 3 and first_left is None: first_left = t - 2
        d = ((g < 70) & wall).astype(np.uint8)
        n, lab, st, cen = cv2.connectedComponentsWithStats(d, 8)
        if n > 1:
            k = 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))
            if st[k, cv2.CC_STAT_AREA] >= 150:
                cys.append(float(cen[k][1])); lost_run = 0; continue
        cys.append(None); lost_run += 1; max_lost_run = max(max_lost_run, lost_run)
    found = [c for c in cys if c is not None]
    drop = (max(found) - cy0) if found else 0.0
    left = first_left is not None
    fell = bool(left and (drop > 60 or max_lost_run >= 3))
    return dict(n=len(frames), f0_dark=int(dark0.sum()), cy0=float(cy0), cx0=float(cx0),
                first_left=first_left, left=bool(left), drop_px=float(drop), max_lost_run=int(max_lost_run),
                fell=fell, persist_end=persist[-1])

clipdir, eyef, out = sys.argv[1:4]
eye = {r['clip']: r for r in csv.DictReader(open(eyef))}
res = {}
for fn in sorted(os.listdir(clipdir)):
    if fn.endswith('.mp4'):
        res[fn[:-4]] = analyse(os.path.join(clipdir, fn))
codes = sorted(res)
mine = {c: res[c].get('fell') for c in codes}
agree = sum(1 for c in codes if c in eye and (eye[c]['fell'] == 'Y') == bool(mine[c]))
tab = {}
for c in codes:
    if c in eye:
        k = f"ro1={eye[c]['fell']} mine={'Y' if mine[c] else 'N'}"; tab.setdefault(k, []).append(c)
summ = dict(n=len(codes), fell_mine=sum(bool(v) for v in mine.values()),
            left_mine=sum(bool(res[c].get('left')) for c in codes),
            fell_ro1=sum(1 for c in codes if c in eye and eye[c]['fell'] == 'Y'),
            agree=agree, table={k: (len(v), v if len(v) < 15 else v[:15]) for k, v in tab.items()},
            first_left_median=float(np.median([res[c]['first_left'] for c in codes if res[c].get('first_left') is not None])))
json.dump(dict(summary=summ, per_clip=res), open(out, 'w'), indent=1)
print(json.dumps(summ, indent=1))
