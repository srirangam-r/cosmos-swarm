"""Tan-rod tip distance from the real pivot (326,118) on each input frame, using rodtrack's HSV tan mask,
restricted to a 12 px corridor around the original rod line and above the table edge (y < 262)."""
import cv2, numpy as np, json, sys
P = np.array([326.0, 118.0])
out = {}
for name, fn in [('orig', sys.argv[1]), ('L70', 'inp/pend10_mid_f93_L70.png'), ('L50', 'inp/pend10_mid_f93_L50.png')]:
    im = cv2.imread(fn)
    h = cv2.cvtColor(im[40:275, 0:420], cv2.COLOR_BGR2HSV)
    m = (h[..., 0] >= 6) & (h[..., 0] <= 26) & (h[..., 1] > 45) & (h[..., 2] > 90)
    ys, xs = np.nonzero(m); ys = ys + 40
    d = np.array([307 - 322, 258 - 127.0]); d /= np.linalg.norm(d)
    rel = np.c_[xs - 322, ys - 127.0]; along = rel @ d; perp = np.abs(rel @ np.array([-d[1], d[0]]))
    k = (perp < 12) & (along > 15) & (ys > 130) & (ys < 262)
    pts = np.c_[xs[k], ys[k]]; dist = np.linalg.norm(pts - P, axis=1)
    tip = pts[np.argmax(dist)]
    out[name] = dict(L_tan_px=float(dist.max()), tip=tip.tolist(), n=int(k.sum()))
for a in ('L70', 'L50'):
    out[a]['scale_vs_orig'] = out[a]['L_tan_px'] / out['orig']['L_tan_px']
json.dump(out, open('inp/input_rodlen.json', 'w'), indent=1); print(json.dumps(out))
