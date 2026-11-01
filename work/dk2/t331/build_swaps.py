"""t331: 2x2 region-swap composites (corridor from A x background from B) for DOVER localization.
Usage: python build_swaps.py <gen_dir> <proxy_dir> <out_dir>
For each scene x seed: mask M = dilated union of moving pixels (max_t |f_t - f_0| > THR) of the plain clip,
the nphys clip and the nphys proxy; feathered. Cells: pp (plain), nn (nphys), np_ (corridor nphys, bg plain),
pn (corridor plain, bg nphys). All 4 cells re-encoded identically (libx264 crf 12 yuv420p 24 fps).
Also writes sharpness.json: background (1-M) Laplacian variance per clip, frames 1..92 mean / frame 0."""
import sys, os, json, subprocess, numpy as np, cv2
THR, DIL, FEATHER = 25, 21, 6.0
gen, prox, out = sys.argv[1:4]; os.makedirs(out, exist_ok=True)
def read(p):
    cap = cv2.VideoCapture(p); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    return np.stack(fr)
def motion(v):
    g = v.astype(np.int16).mean(-1)
    m = (np.abs(g - g[0:1]).max(0) > THR).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return m
def write(p, v):
    T, H, W, _ = v.shape
    pr = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{W}x{H}", "-r", "24",
                           "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", p], stdin=subprocess.PIPE)
    pr.stdin.write(np.ascontiguousarray(v).tobytes()); pr.stdin.close(); assert pr.wait() == 0
def lapvar(f, w):
    l = cv2.Laplacian(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32), cv2.CV_32F)
    return float((l ** 2 * w).sum() / w.sum() - ((l * w).sum() / w.sum()) ** 2)
meta, sharp = {}, {}
for sc in ["09", "12", "16", "17", "18", "19"]:
    P = read(f"{prox}/proxy_real_{sc}_nphys.mp4")
    for s in [1, 2, 3]:
        A = read(f"{gen}/t276_real_{sc}_plain_s{s}.mp4"); B = read(f"{gen}/t276_real_{sc}_nphys_s{s}.mp4")
        T = min(len(A), len(B), len(P)); A, B = A[:T], B[:T]
        m = np.maximum.reduce([motion(A), motion(B), motion(P[:T])])
        m = cv2.dilate(m, np.ones((DIL, DIL), np.uint8)).astype(np.float32)
        w = np.clip(cv2.GaussianBlur(m, (0, 0), FEATHER), 0, 1)[None, ..., None]
        cells = {"pp": A, "nn": B,
                 "np": (w * B + (1 - w) * A).round().astype(np.uint8),
                 "pn": (w * A + (1 - w) * B).round().astype(np.uint8)}
        for k, v in cells.items():
            write(f"{out}/sw_{sc}_s{s}_{k}.mp4", v)
        bgw = 1 - w[0, ..., 0]
        for k, v in [("plain", A), ("nphys", B)]:
            f0 = lapvar(v[0], bgw); r = [lapvar(v[t], bgw) / f0 for t in range(1, T)]
            sharp[f"{sc}_s{s}_{k}"] = {"f0": f0, "ratio_mean": float(np.mean(r)), "ratio_last10": float(np.mean(r[-10:]))}
        meta[f"{sc}_s{s}"] = {"mask_frac_core": float(m.mean()), "mask_frac_feather": float(w.mean()), "T": T}
        print(sc, s, meta[f"{sc}_s{s}"], flush=True)
json.dump({"params": {"THR": THR, "DIL": DIL, "FEATHER": FEATHER}, "meta": meta, "sharp": sharp}, open(f"{out}/swap_meta.json", "w"), indent=1)
