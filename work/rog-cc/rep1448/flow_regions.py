"""Independent replication of #1448 (poornima-1, task 45): does the RoPE fps parameter act as a clock?

Method (independent of arm_stats.py / timewarp.py, which use |frame diff|):
  RAFT-large (torchvision C_T_V1, 12 iters) dense optical flow between consecutive frames at half
  resolution (416x240; inputs pre-downscaled on GB10 with ffmpeg scale=416:240:flags=area, crf 14). Per pair we record the mean flow magnitude (px at FULL res, i.e. x2) in
    arm   : y 0-280, x 200-480   (full-res coords, same ROI as #1448)
    table : y 300-470, all x
    whole : full frame
Outputs one JSON with per-clip per-pair series. analyze.py turns it into paired stats.
"""
import argparse, glob, json, os, re, time
import numpy as np, torch, av
from torchvision.models.optical_flow import raft_large, Raft_Large_Weights

ap = argparse.ArgumentParser()
ap.add_argument("clipdir"); ap.add_argument("--out", required=True); ap.add_argument("--device", default="cuda")
ap.add_argument("--iters", type=int, default=12)
a = ap.parse_args()

m = raft_large(weights=Raft_Large_Weights.C_T_V1).eval().to(a.device)
ROI = {"arm": (0, 280, 200, 480), "table": (300, 470, 0, 832), "whole": (0, 480, 0, 832)}
res = json.load(open(a.out)) if os.path.exists(a.out) else {}
for p in sorted(glob.glob(os.path.join(a.clipdir, "*.mp4"))):
    name = os.path.basename(p)[:-4]
    if name in res: continue
    t0 = time.time()
    c = av.open(p); fr = np.stack([f.to_ndarray(format="rgb24") for f in c.decode(video=0)]); c.close()
    T, H, W, _ = fr.shape
    x = torch.from_numpy(fr).permute(0, 3, 1, 2).float()
    if W > 416:
        x = torch.nn.functional.interpolate(x, size=(240, 416), mode="bilinear", align_corners=False)
    # clips arrive either full-res 832x480 or pre-downscaled 416x240 (ffmpeg scale=416:240:flags=area)
    x = 2 * (x / 255.0) - 1.0
    ser = {k: [] for k in ROI}
    with torch.no_grad():
        for i in range(0, T - 1, 8):
            j = min(i + 8, T - 1)
            A = x[i:j].to(a.device); B = x[i + 1:j + 1].to(a.device)
            flo = m(A, B, num_flow_updates=a.iters)[-1]  # N,2,h,w
            mag = flo.norm(dim=1) * 2.0  # back to full-res px
            for k, (y0, y1, x0, x1) in ROI.items():
                ser[k] += mag[:, y0 // 2:y1 // 2, x0 // 2:x1 // 2].mean(dim=(1, 2)).cpu().tolist()
    res[name] = {"T": T, "H": H, "W": W, **{k: [round(v, 4) for v in s] for k, s in ser.items()}}
    json.dump(res, open(a.out, "w"))
    print(name, T, f"{time.time() - t0:.1f}s", flush=True)
