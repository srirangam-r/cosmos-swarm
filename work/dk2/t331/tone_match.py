"""t331 post-process candidate (uses only the input frame + the output clip): one clip-level BGR offset so the
static background (pixels whose max_t |f_t - f_0| <= 25 grey, eroded 21 px) matches the input frame's mean.
Applied identically to plain and nphys. Usage: python tone_match.py <inputs_dir> <gen_dir> <out_dir>"""
import sys, os, json, subprocess, numpy as np, cv2
inp, gen, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
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
offs = {}
for sc in ["09", "12", "16", "17", "18", "19"]:
    I = cv2.imread(f"{inp}/f0_real_{sc}.png").astype(np.float32)
    for a in ["plain", "nphys"]:
        for s in [1, 2, 3]:
            V = read(f"{gen}/t276_real_{sc}_{a}_s{s}.mp4")
            g = V.astype(np.int16).mean(-1); st = (np.abs(g - g[0:1]).max(0) <= 25).astype(np.uint8)
            st = cv2.erode(st, np.ones((21, 21), np.uint8)).astype(bool)
            o = I[st].mean(0) - V[1:][:, st].astype(np.float32).mean((0, 1))
            offs[f"{sc}_{a}_s{s}"] = [float(x) for x in o] + [float(st.mean())]
            W = np.clip(V.astype(np.float32) + o, 0, 255).round().astype(np.uint8); W[0] = V[0]
            write(f"{out}/tm_{sc}_s{s}_{a}.mp4", W)
json.dump(offs, open(f"{out}/offsets.json", "w"), indent=1)
for a in ["plain", "nphys"]:
    print(a, "mean BGR offset", np.round(np.mean([v[:3] for k, v in offs.items() if f"_{a}_" in k], 0), 2), "static frac", round(np.mean([v[3] for k, v in offs.items() if f"_{a}_" in k]), 2))
