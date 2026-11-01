"""Counterfactual pendulum-length first frames from GAUGE pend10_mid_f93 (task 220).

Moves the bob (with its motion blur) up along the rod toward the pivot by a
fraction of the pivot-bob distance, inpaints the vacated bob/rod pixels, and
pastes the bob back with a feathered mask.  frac=1.0 is the sham control: the
same inpaint + paste pipeline, with no displacement.

usage: edit_len.py <in.png> <out_dir>
"""
import json
import sys

import cv2
import numpy as np

src, out = sys.argv[1], sys.argv[2]
im = cv2.imread(src)
H, W = im.shape[:2]

PIVOT = np.array([322.0, 127.0])   # hub centre, read off the 4x zoom
BOB = np.array([307.0, 258.0])     # blurred bob centre
BOB_R = (34, 20)                   # half-width, half-height of blurred bob + ring (px)
ROD_HALF_W = 6                     # rod half-width incl. blur (px)
HUB_CLEAR = 22                     # keep rod pixels within this distance of the pivot


def bob_mask(c):
    m = np.zeros((H, W), np.uint8)
    cv2.ellipse(m, (int(round(c[0])), int(round(c[1]))), BOB_R, 0, 0, 360, 255, -1)
    return m


def make(frac):
    d = BOB - PIVOT
    newc = PIVOT + frac * d
    shift = newc - BOB
    # 1. remove the old bob and the rod segment below the new bob centre
    rm = bob_mask(BOB)
    rod_from = PIVOT + d * max(frac, 0.0)
    p0 = tuple(int(round(v)) for v in rod_from)
    p1 = tuple(int(round(v)) for v in BOB)
    if frac < 1.0:
        cv2.line(rm, p0, p1, 255, 2 * ROD_HALF_W + 1)
    rm = cv2.dilate(rm, np.ones((3, 3), np.uint8))
    filled = cv2.inpaint(im, rm, 7, cv2.INPAINT_TELEA)
    # 2. paste the original bob patch at the new centre with a feathered ellipse
    M = np.float32([[1, 0, shift[0]], [0, 1, shift[1]]])
    moved = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    a = bob_mask(newc).astype(np.float32) / 255.0
    a = cv2.GaussianBlur(a, (0, 0), 3.0)
    res = filled.astype(np.float32) * (1 - a[..., None]) + moved.astype(np.float32) * a[..., None]
    res = np.clip(res + 0.5, 0, 255).astype(np.uint8)
    L0 = float(np.linalg.norm(d))
    return res, dict(frac=frac, pivot=PIVOT.tolist(), bob_orig=BOB.tolist(), bob_new=newc.tolist(),
                     L_orig_px=L0, L_new_px=frac * L0)


meta = {}
for name, frac in [("sham", 1.0), ("half", 0.5)]:
    res, info = make(frac)
    fn = f"{out}/pend10_mid_f93_{name}.png"
    cv2.imwrite(fn, res)
    z = cv2.resize(res[90:300, 230:420], None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST)
    cv2.imwrite(f"{out}/zoom_{name}.png", z)
    diff = np.abs(res.astype(int) - im.astype(int)).max(axis=2)
    info["changed_px_gt8"] = int((diff > 8).sum())
    info["file"] = fn
    meta[name] = info
json.dump(meta, open(f"{out}/edit_meta.json", "w"), indent=1)
print(json.dumps(meta, indent=1))
