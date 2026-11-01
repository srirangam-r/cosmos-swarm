"""Recover the input resize (sx, sy) and offset that map a real reference frame (e.g. GAUGE 1280x720 frame 0) onto a
Cosmos clip's first frame (e.g. 832x480), by normalized cross-correlation over a scale grid (raj-3).
Then px/m in the Cosmos frame = ref_ppm * s (vertical: sy; horizontal: sx). GAUGE ball: ref_ppm = 830.5 at 1280x720 (raj-2, msg 146).
Usage: python3 -I calib_frame0.py cosmos.mp4 real_ref.mp4 [--ref-ppm 830.5]"""
import sys, argparse, json, numpy as np, cv2

def first(p):
    c = cv2.VideoCapture(p); ok, f = c.read(); assert ok, p
    return cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32)

def score(C, R, sx, sy, m=0.12):
    h, w = R.shape; Rs = cv2.resize(R, (int(round(w * sx)), int(round(h * sy))), interpolation=cv2.INTER_AREA)
    H, W = Rs.shape; T = Rs[int(m * H):int((1 - m) * H), int(m * W):int((1 - m) * W)]   # central crop as template
    if T.shape[0] >= C.shape[0] or T.shape[1] >= C.shape[1]: return -1, None
    r = cv2.matchTemplate(C, T, cv2.TM_CCOEFF_NORMED); _, v, _, loc = cv2.minMaxLoc(r)
    return v, (loc[0] - int(m * W), loc[1] - int(m * H))   # offset of the resized ref's (0,0) in the Cosmos frame

def calib(C, R):
    best = max(((score(C, R, s, s)[0], s) for s in np.arange(0.55, 0.80, 0.005)))
    s0 = best[1]; grid = np.arange(s0 - 0.03, s0 + 0.0301, 0.0025)
    v, sx, sy = max(((score(C, R, a, b)[0], a, b) for a in grid for b in grid))
    return dict(ncc=float(v), sx=float(sx), sy=float(sy), offset=score(C, R, sx, sy)[1])

if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('cosmos'); a.add_argument('ref'); a.add_argument('--ref-ppm', type=float, default=830.5)
    o = a.parse_args(); r = calib(first(o.cosmos), first(o.ref))
    r.update(ppm_vertical=o.ref_ppm * r['sy'], ppm_horizontal=o.ref_ppm * r['sx'])
    print(json.dumps(r, indent=1))
