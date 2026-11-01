#!/usr/bin/env python3
"""Real GAUGE continuation clips for the HUE |gen - real| reference (follow-up to #2905).
Same transform as raj-3 midfall_frames.py (dedup 25-in-30, letterbox 1280x720 -> 832x468 + 6 px pad),
93 frames from dedup frame `start`, written at 24 fps (like ro-1's real_ball1_dd32_93f).
Checks f0 against the Cosmos input PNG (MAE) so the reference starts at the same frame as the generated clips.
usage: make_real_cont.py <repo_root> <video.mp4> <start> <out.mp4> [--check input.png]"""
import argparse, subprocess, sys
import numpy as np, cv2

ap = argparse.ArgumentParser()
ap.add_argument("repo"); ap.add_argument("video"); ap.add_argument("start", type=int); ap.add_argument("out")
ap.add_argument("--check"); ap.add_argument("--n", type=int, default=93)
a = ap.parse_args()
sys.path.insert(0, a.repo + "/tools/trk_ballfall")
import trk, measure_ball as mb  # noqa: E402
F = trk.load(a.video); F, fac = mb.dedup(F)
assert a.start + a.n <= len(F), (len(F), a.start + a.n)
frames = []
for k in range(a.start, a.start + a.n):
    L = np.zeros((480, 832, 3), np.uint8)
    L[6:474] = cv2.resize(F[k].clip(0, 255).astype(np.uint8), (832, 468), interpolation=cv2.INTER_AREA)
    frames.append(L)
if a.check:
    ref = cv2.imread(a.check)
    print("f0 MAE vs input", float(np.abs(frames[0].astype(float) - ref.astype(float)).mean()),
          "| f1", float(np.abs(frames[1].astype(float) - ref.astype(float)).mean()))
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", "832x480",
                      "-r", "24", "-i", "-", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", a.out],
                     stdin=subprocess.PIPE)
for L in frames:
    p.stdin.write(L.tobytes())
p.stdin.close(); p.wait()
print("wrote", a.out, "dedup fps", 30 * fac, "n_dedup", len(F))
