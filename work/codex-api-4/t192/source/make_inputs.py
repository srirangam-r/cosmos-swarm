"""Build independent robot-removal (A) and equal-area edit-control (E) inputs from GAUGE frame 0.

Independent of raj-opus-1's task-139 edit (texture copy): here the masks are hand-set polygons and
the fill is LaMa (simple-lama-inpainting). The ball disk is excluded from every mask, so its pixels
are untouched.

Inputs: GAUGE-Dataset data/rigid/bouncing ball/video/{8,15}.mp4 frame 0 (1280x720), resized to 853x480
(INTER_AREA) and centre-cropped to 832x480 (columns 10..841).
Arms:
  O  unedited
  A  whole Franka (gripper body, fingers, cables, arm column, base) removed, ball kept
  K  arm column, wrist, cables and base removed; gripper body + fingers kept around the ball
     -> energy-matched control: a large robot edit that keeps the holder.
  E  robot kept; an equal-area mask (foam block on the table + a curtain patch on the right) filled
     with the same LaMa pipeline -> controls for "any large LaMa edit releases the ball".
Usage: python make_inputs.py <raw_dir> <out_dir>
"""
import json
import sys

import cv2
import numpy as np


def ball_center(img, guess=(277, 113), win=22):
    """Locate the ball near the guess: darkest-disk via Hough on the local crop, fallback to guess."""
    x0, y0 = guess
    crop = cv2.cvtColor(img[y0 - win:y0 + win, x0 - win:x0 + win], cv2.COLOR_BGR2GRAY)
    crop = cv2.GaussianBlur(crop, (3, 3), 0)
    c = cv2.HoughCircles(crop, cv2.HOUGH_GRADIENT, dp=1, minDist=40, param1=80, param2=12, minRadius=9, maxRadius=15)
    if c is None:
        return guess, 12, False
    cx, cy, r = c[0][0]
    return (int(round(x0 - win + cx)), int(round(y0 - win + cy))), int(round(r)), True


ROBOT_POLY = [(226, 0), (482, 0), (482, 255), (492, 298), (486, 316), (380, 316), (376, 262), (372, 205),
              (330, 205), (305, 208), (280, 208), (260, 160), (256, 99), (226, 101)]
FOAM_POLY = [(52, 268), (212, 268), (212, 332), (52, 332)]
# the dark mounting rod enters from the upper left and runs behind the gripper; mask its last stretch so
# LaMa cannot extend it toward the ball (first attempt drew a rod end + bracket just above the ball)
ROD_POLY = [(140, 26), (230, 40), (230, 66), (140, 52)]
# K: arm column, wrist, cables and base removed; gripper body + fingers (the holder) kept
ARM_POLY = [(338, 0), (482, 0), (482, 255), (492, 298), (486, 316), (380, 316), (376, 262), (372, 205), (338, 205)]


def main(raw_dir, out_dir):
    from simple_lama_inpainting import SimpleLama
    from PIL import Image
    lama = SimpleLama(device="cpu")
    meta = {}
    for vid in (8, 15):
        raw = cv2.imread(f"{raw_dir}/v{vid}_f0.png")
        img = cv2.resize(raw, (853, 480), interpolation=cv2.INTER_AREA)[:, 10:842].copy()
        (cx, cy), r, found = ball_center(img)
        keep = np.zeros(img.shape[:2], np.uint8)
        cv2.circle(keep, (cx, cy), r + 1, 255, -1)

        m_robot = np.zeros(img.shape[:2], np.uint8)
        cv2.fillPoly(m_robot, [np.array(ROBOT_POLY, np.int32)], 255)
        cv2.fillPoly(m_robot, [np.array(ROD_POLY, np.int32)], 255)
        m_robot[keep > 0] = 0
        m_arm = np.zeros(img.shape[:2], np.uint8)
        cv2.fillPoly(m_arm, [np.array(ARM_POLY, np.int32)], 255)
        m_arm[keep > 0] = 0
        area = int((m_robot > 0).sum())

        # E: foam block + a curtain rectangle on the right, sized so the total area matches m_robot
        m_ctrl = np.zeros(img.shape[:2], np.uint8)
        cv2.fillPoly(m_ctrl, [np.array(FOAM_POLY, np.int32)], 255)
        need = area - int((m_ctrl > 0).sum())
        w = 250
        h = int(np.ceil(need / w))
        x1, y1 = 545, 0  # curtain region right of the curtain gap, away from robot and ball
        m_ctrl[y1:y1 + h, x1:x1 + w] = 255
        area_ctrl = int((m_ctrl > 0).sum())

        out = {"O": img}
        for arm, m in (("A", m_robot), ("K", m_arm), ("E", m_ctrl)):
            md = cv2.dilate(m, np.ones((3, 3), np.uint8))
            md[keep > 0] = 0
            res = lama(Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)), Image.fromarray(md))
            res = cv2.cvtColor(np.array(res)[:480, :832], cv2.COLOR_RGB2BGR)
            res[md == 0] = img[md == 0]  # paste back every unmasked pixel exactly
            out[arm] = res
            cv2.imwrite(f"{out_dir}/v{vid}_{arm}_mask.png", md)
        for arm, im in out.items():
            cv2.imwrite(f"{out_dir}/v{vid}_{arm}.png", im)
        ball_same = {arm: bool(np.array_equal(out[arm][keep > 0], img[keep > 0])) for arm in out}
        diff = {arm: float(np.abs(out[arm].astype(int) - img.astype(int)).sum() / 255.0) for arm in out}
        meta[f"v{vid}"] = {"ball_center": [cx, cy], "ball_r": r, "hough_found": found,
                           "mask_area_A": area, "mask_area_K": int((m_arm > 0).sum()), "mask_area_E": area_ctrl,
                           "ball_pixels_identical": ball_same, "abs_diff_sum_vs_O": diff}
        print(vid, meta[f"v{vid}"])
    json.dump(meta, open(f"{out_dir}/inputs_meta.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
