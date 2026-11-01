"""Counterfactual pendulum-length first frames from GAUGE pend10_mid_f93 (task 220), v2.

Uses a clean background plate (median of real GAUGE pendulum-10 frames around the
source frame, fixed camera; see plate.py) instead of blind inpainting.

For a length fraction f the bob centre moves along the rod toward the pivot:
    c_new = pivot + f * (bob - pivot)
1. Inside the region R = (old bob ellipse) U (rod pixels from c_new to the old bob),
   pixels are replaced by the plate (colour-matched to the input).
2. The bob is moved with a background-aware matte. alpha = clip(|I - B| / 30) inside
   the old bob ellipse, B = plate.  Composite at the new place:
       out = I_shift + (1 - alpha_shift) * (B_new - B_shift)
   i.e. the bob's old background is swapped for the background at the new place.
The rod above c_new is the untouched original.

usage: edit_len2.py <in.png> <plate_roi.png> <out_dir>
"""
import json
import sys

import cv2
import numpy as np

src, plate_fn, out = sys.argv[1:4]
im = cv2.imread(src).astype(np.float32)
H, W = im.shape[:2]
Y0, Y1, X0, X1 = 140, 300, 250, 380          # plate ROI (plate.py)
plate_roi = cv2.imread(plate_fn).astype(np.float32)

PIVOT = np.array([322.0, 127.0])
BOB = np.array([307.0, 258.0])
BOB_R = (30, 19)
ROD_HALF_W = 8


def ell(c, r=BOB_R):
    m = np.zeros((H, W), np.uint8)
    cv2.ellipse(m, (int(round(c[0])), int(round(c[1]))), r, 0, 0, 360, 255, -1)
    return m


# full-frame plate = input outside the ROI, colour-matched plate inside
pend = ell(BOB, (BOB_R[0] + 6, BOB_R[1] + 6))
cv2.line(pend, tuple(map(int, PIVOT)), tuple(map(int, BOB)), 255, 2 * ROD_HALF_W + 9)
roi_in = im[Y0:Y1, X0:X1]
keep = pend[Y0:Y1, X0:X1] == 0
offset = (roi_in[keep] - plate_roi[keep]).mean(axis=0)
B = im.copy()
B[Y0:Y1, X0:X1] = plate_roi + offset
plate_err = float(np.abs(roi_in[keep] - (plate_roi[keep] + offset)).mean())

alpha_full = np.clip(np.abs(im - B).max(axis=2) / 30.0, 0, 1)
alpha_full *= ell(BOB).astype(np.float32) / 255.0
# table pixels below the bob (warm tan hue) are background, not bob: drop them from the
# matte in the lower half of the ellipse (the tan rod stub in the upper half moves with the bob)
warm = (im[..., 2] - im[..., 0] > 20) & (im.mean(axis=2) > 45)
lower = np.zeros((H, W), bool); lower[int(BOB[1]) - 2:, :] = True
alpha_full[warm & lower] = 0
alpha_full = cv2.GaussianBlur(alpha_full, (0, 0), 0.8)


def make(frac):
    d = BOB - PIVOT
    newc = PIVOT + frac * d
    sh = newc - BOB
    # region to clear: old bob + rod below the new bob centre
    R = ell(BOB, (BOB_R[0] + 3, BOB_R[1] + 3))
    cv2.line(R, tuple(int(round(v)) for v in newc), tuple(int(round(v)) for v in BOB), 255, 2 * ROD_HALF_W + 1)
    Rf = cv2.GaussianBlur(R.astype(np.float32) / 255.0, (0, 0), 1.5)[..., None]
    res = im * (1 - Rf) + B * Rf
    M = np.float32([[1, 0, sh[0]], [0, 1, sh[1]]])
    I_s = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    B_s = cv2.warpAffine(B, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    a_s = cv2.warpAffine(alpha_full, M, (W, H), flags=cv2.INTER_LINEAR)
    bobpix = I_s + (1 - a_s[..., None]) * (B - B_s)
    region = cv2.warpAffine(ell(BOB).astype(np.float32) / 255.0, M, (W, H), flags=cv2.INTER_LINEAR)
    region = cv2.GaussianBlur(region, (0, 0), 1.0)[..., None]
    res = res * (1 - region) + bobpix * region
    res = np.clip(res + 0.5, 0, 255).astype(np.uint8)
    L0 = float(np.linalg.norm(d))
    return res, dict(frac=frac, pivot=PIVOT.tolist(), bob_orig=BOB.tolist(), bob_new=newc.tolist(),
                     L_orig_px=L0, L_new_px=frac * L0)


meta = dict(plate_offset_bgr=offset.tolist(), plate_mae_outside_pendulum=plate_err)
for name, frac in [("L70", 0.7), ("L50", 0.5)]:
    res, info = make(frac)
    fn = f"{out}/pend10_mid_f93_{name}.png"
    cv2.imwrite(fn, res)
    z = cv2.resize(res[90:300, 230:420], None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(f"{out}/zoom_{name}.png", z)
    info["changed_px_gt8"] = int((np.abs(res.astype(int) - im.astype(int)).max(axis=2) > 8).sum())
    meta[name] = info
json.dump(meta, open(f"{out}/edit_meta.json", "w"), indent=1)
print(json.dumps(meta, indent=1))
