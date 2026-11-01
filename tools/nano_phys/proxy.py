"""
nano_phys.proxy: Analytical physics proxy generation from frame 0.
Reuses proven formulations from ro-3 (#5315, Task 252) and rahul-3 (Task 266).
"""

import math
import os
from pathlib import Path
import cv2
import numpy as np


def generate_pendulum_proxy(
    image_path: str | Path,
    out_path: str | Path,
    pivot: tuple[int, int],
    bob: tuple[int, int],
    period: float | None = None,
    g: float = 9.81,
    amplitude_deg: float = 18.0,
    release_from_rest: bool = True,
    direction: str = "inward",
    num_frames: int = 93,
    fps: int = 24,
    width: int = 832,
    height: int = 480,
) -> dict:
    """Generate crude 2D kinematic pendulum proxy rotating rod+bob patch about axle."""
    im = cv2.imread(str(image_path))
    if im is None:
        raise FileNotFoundError(f"Input image not found: {image_path}")

    H, W = im.shape[:2]
    if (W, H) != (width, height):
        im = cv2.resize(im, (width, height), interpolation=cv2.INTER_AREA)
        H, W = height, width

    px, py = pivot
    bx, by = bob

    # Angle from vertical (in degrees)
    th_cur = math.degrees(math.atan2(px - bx, by - py))
    L_px = math.hypot(bx - px, by - py)

    # Estimate physical period if not explicitly supplied
    if period is None:
        # Effective physical length in meters (standard GAUGE rig ~ 0.35 m)
        L_m = 0.35
        period = 2.0 * math.pi * math.sqrt(L_m / g)

    # Polygon along rod axis from 8px above pivot to 10px past bob, half-width 26
    ang = math.atan2(bx - px, by - py)
    ux, uy = math.sin(ang), math.cos(ang)
    vx, vy = uy, -ux
    pts = []
    for s, w in [(8, -26), (8, 26), (L_px + 10, 26), (L_px + 10, -26)]:
        pts.append((px + ux * s + vx * w, py + uy * s + vy * w))

    mask = np.zeros((H, W), np.uint8)
    cv2.fillPoly(mask, [np.int32(pts)], 255)
    bg = cv2.inpaint(im, cv2.dilate(mask, np.ones((5, 5), np.uint8)), 5, cv2.INPAINT_TELEA)
    malpha = cv2.GaussianBlur(mask, (0, 0), 2).astype(np.float32)[..., None] / 255.0

    w = 2.0 * math.pi / period

    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    vw = cv2.VideoWriter(str(out_p), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    for i in range(num_frames):
        t = i / fps
        if release_from_rest:
            # Releasing from rest: initial velocity is zero, swings inward toward vertical
            # th(0) = th_cur, th'(0) = 0
            th = th_cur * math.cos(w * t)
        else:
            # General harmonic motion with explicit inward direction
            A = max(abs(th_cur), amplitude_deg)
            phi = math.asin(max(-1.0, min(1.0, th_cur / A)))
            # If direction is inward, sign depends on initial position
            sgn = -1.0 if th_cur >= 0 else 1.0
            if direction == "outward":
                sgn = -sgn
            th = A * math.sin(sgn * w * t + phi)

        d = th - th_cur
        M = cv2.getRotationMatrix2D((px, py), -d, 1.0)
        rot = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        ra = cv2.warpAffine(malpha, M, (W, H))
        if ra.ndim == 2:
            ra = ra[..., None]
        frame = (bg * (1.0 - ra) + rot * ra).astype(np.uint8)
        vw.write(frame)

    vw.release()

    return {
        "physics": "pendulum",
        "proxy_path": str(out_p),
        "period": period,
        "g": g,
        "amplitude_deg": amplitude_deg,
        "release_from_rest": release_from_rest,
        "L_px": L_px,
        "th_cur_deg": th_cur,
        "num_frames": num_frames,
        "fps": fps,
        "resolution": f"{width}x{height}",
    }


def generate_ball_proxy(
    image_path: str | Path,
    out_path: str | Path,
    center: tuple[int, int],
    radius: int = 13,
    floor_y: int = 340,
    g: float = 9.81,
    e: float = 0.58,
    ppm: float = 539.8,
    hold: float = 0.25,
    num_frames: int = 189,
    fps: int = 24,
    width: int = 832,
    height: int = 480,
) -> dict:
    """Generate crude 2D kinematic ball drop/bounce proxy from frame 0."""
    im = cv2.imread(str(image_path))
    if im is None:
        raise FileNotFoundError(f"Input image not found: {image_path}")

    H, W = im.shape[:2]
    if (W, H) != (width, height):
        im = cv2.resize(im, (width, height), interpolation=cv2.INTER_AREA)
        H, W = height, width

    cx, cy = center
    drop = floor_y - cy

    # Background inpainting
    mask = np.zeros((H, W), np.uint8)
    cv2.circle(mask, (cx, cy), radius + 3, 255, -1)
    bg = cv2.inpaint(im, mask, 5, cv2.INPAINT_TELEA)

    alpha = np.zeros((H, W), np.uint8)
    cv2.circle(alpha, (cx, cy), radius, 255, -1)
    alpha = cv2.GaussianBlur(alpha, (0, 0), 1).astype(np.float32) / 255.0

    # Sub-stepped physics integration
    substeps = 20
    dt = 1.0 / (fps * substeps)
    total_steps = num_frames * substeps
    ga = g * ppm

    traj = []
    ypx = 0.0
    vpx = 0.0

    for i in range(total_steps):
        t = i * dt
        if i % substeps == 0:
            traj.append(ypx)
        if t >= hold:
            vpx += ga * dt
            ypx += vpx * dt
            if ypx >= drop and vpx > 0:
                ypx = drop
                vpx = -e * vpx

    out_p = Path(out_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    vw = cv2.VideoWriter(str(out_p), cv2.VideoWriter_fourcc(*"mp4v"), fps, (W, H))

    for k in range(num_frames):
        dy = traj[k]
        M = np.float32([[1.0, 0.0, 0.0], [0.0, 1.0, dy]])
        sh = cv2.warpAffine(im, M, (W, H))
        sa = cv2.warpAffine(alpha, M, (W, H))[..., None]
        frame = (bg * (1.0 - sa) + sh * sa).astype(np.uint8)
        vw.write(frame)

    vw.release()

    return {
        "physics": "ball",
        "proxy_path": str(out_p),
        "g": g,
        "e": e,
        "floor_y": floor_y,
        "drop_px": drop,
        "hold_s": hold,
        "num_frames": num_frames,
        "fps": fps,
        "resolution": f"{width}x{height}",
    }
