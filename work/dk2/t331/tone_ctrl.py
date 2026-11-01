"""t331 control: apply nphys-like global tone change to plain clips (re-encoded like the swaps).
Usage: python tone_ctrl.py <swaps_dir> <out_dir>; writes sw_<sc>_s<s>_ppdark.mp4 (luma -1.5) and _ppblur.mp4 (Gaussian sigma 0.5)."""
import sys, os, subprocess, numpy as np, cv2
sw, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True)
def read(p):
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    return np.stack(fr)
def write(p, v):
    T, H, W, _ = v.shape
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "24",
                           "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", p], stdin=subprocess.PIPE)
    pr.stdin.write(np.ascontiguousarray(v).tobytes()); pr.stdin.close(); assert pr.wait() == 0
for sc in ["09", "12", "16", "17", "18", "19"]:
    for s in [1, 2, 3]:
        A = read(f"{sw}/sw_{sc}_s{s}_pp.mp4")
        write(f"{out}/sw_{sc}_s{s}_ppdark.mp4", np.clip(A.astype(np.float32) - 1.5, 0, 255).round().astype(np.uint8))
        write(f"{out}/sw_{sc}_s{s}_ppblur.mp4", np.stack([cv2.GaussianBlur(f, (0, 0), 0.5) for f in A]))
