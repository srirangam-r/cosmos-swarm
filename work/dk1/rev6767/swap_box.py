"""Independent 2x2 region swap for review of #6767 (dk1). Shares no code with work/dk2/t331.

Differences from t331 by design:
  * corridor mask = the rectangle a region-wise fix would use (the t336 box definition): pixels of the
    normal and x1.7 proxies (work/dk2/t276/proxies) with max_t|f_t-f_0| > 30 grey, plus the pivot and bob
    points, dilated 32 px, bounding rectangle; edges ramped linearly over RAMP px. It does NOT include
    plain's own scattered motion (plain moves 18-23% of pixels by >20 grey somewhere in the frame), so the
    np cell (box from nphys, rest from plain) is the ceiling of an ideal region-wise / dual-clock fix;
  * re-encode is lossless x264 (-qp 0, yuv420p), so cells carry no extra compression loss;
  * sanity: the pp / nn cells are the unswapped clips re-encoded, so pp vs the original plain score
    (and nn vs nphys) measures any re-encode shift.
Usage: swap_box.py <gen_dir> <work/dk2/t276 dir> <out_dir>
"""
import json, subprocess, sys
from pathlib import Path
import numpy as np
from scipy.ndimage import binary_dilation

THR, DIL, RAMP = 30, 32, 8
W, H = 832, 480


def read(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)


def write(p, v):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", "24",
                    "-i", "-", "-c:v", "libx264", "-qp", "0", "-preset", "veryfast", "-pix_fmt", "yuv420p", str(p)],
                   input=np.ascontiguousarray(v).tobytes(), check=True)


def proxy_box(proxies, pivot, bob):
    m = np.zeros((H, W), bool)
    for p in proxies:
        g = read(p).astype(np.int16).mean(-1)
        m |= np.abs(g - g[0]).max(0) > THR
    for x, y in (pivot, bob):
        m[y, x] = True
    m = binary_dilation(m, np.ones((2 * DIL + 1, 2 * DIL + 1), bool))
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    xx = np.arange(W)[None, :] + 0.5; yy = np.arange(H)[:, None] + 0.5
    d = np.minimum(np.minimum(xx - x0, x1 - xx), np.minimum(yy - y0, y1 - yy))
    return np.clip(d / RAMP + 0.5, 0, 1).astype(np.float32), [int(x0), int(y0), int(x1), int(y1)]


def main(gen, t276, out):
    gen, t276, out = Path(gen), Path(t276), Path(out); out.mkdir(parents=True, exist_ok=True)
    fr = {f["id"]: f for f in json.load(open(t276 / "frames.json"))}
    meta = {"THR": THR, "DIL": DIL, "RAMP": RAMP, "clips": {}}
    boxes = {}
    for pp in sorted(gen.glob("t276_real_*_plain_s*.mp4")):
        key = pp.stem.replace("t276_real_", "").replace("_plain", "")  # e.g. 09_s1
        nn = gen / pp.name.replace("_plain_", "_nphys_")
        P, N = read(pp).astype(np.float32), read(nn).astype(np.float32)
        T = min(len(P), len(N)); P, N = P[:T], N[:T]
        sid = "real_" + key[:2]
        if sid not in boxes:
            f = fr[sid]
            boxes[sid] = proxy_box([t276 / "proxies" / f"proxy_{sid}_{a}.mp4" for a in ("nphys", "nphys_x17")],
                                   f["pivot"], f["bob"])
        mk, box = boxes[sid]
        m = mk[None, :, :, None]
        cells = {"pp": P, "nn": N, "np": m * N + (1 - m) * P, "pn": m * P + (1 - m) * N}
        for c, v in cells.items():
            write(out / f"bx_{key}_{c}.mp4", np.clip(np.rint(v), 0, 255).astype(np.uint8))
        meta["clips"][key] = {"box": box, "mask_frac": float(mk.mean()), "T": T}
        print(key, box, round(float(mk.mean()), 3), flush=True)
    (out / "swap_meta.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main(*sys.argv[1:4])
