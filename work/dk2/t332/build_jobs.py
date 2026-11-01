"""t332: Nano-Phys with ProxyUp region-wise latent noising (latent.band region box = proxy corridor bbox).
Same as the t276 nphys jobs (same prompt, proxy, start_step 19, seeds 1-3) plus latent.band. Also x17_rln at seed 1.
Box = bbox of the proxy motion mask (max_t |f_t - f_0| > 30 grey, 3x3 open), dilated 32 px, as width/height fractions.
Usage (from cosmos-swarm root): python work/dk2/t332/build_jobs.py > work/dk2/t332/jobs.jsonl"""
import json, sys, numpy as np, cv2
from pathlib import Path
R = Path(__file__).resolve().parents[3]
T276 = R / "work/dk2/t276"
def read(p):
    cap = cv2.VideoCapture(str(p)); fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    return np.stack(fr)
def box(p, pad=32):
    v = read(p); g = v.astype(np.int16).mean(-1)
    m = (np.abs(g - g[0:1]).max(0) > 30).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    H, W = m.shape; ys, xs = np.nonzero(m)
    if len(xs) == 0: return None
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, W - 1); y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, H - 1)
    return [round(x0 / W, 4), round(y0 / H, 4), round((x1 + 1) / W, 4), round((y1 + 1) / H, 4)]
src = {}
for f in ["jobs_nphys.jsonl", "jobs_nphys_x17.jsonl"]:
    for l in open(T276 / f):
        j = json.loads(l); src[j["name"]] = j
out = []
for name, j in sorted(src.items()):
    x17 = name.endswith("_s1") and "_x17_" in name
    if "_x17_" in name and not x17: continue
    sc = name.split("_")[2]
    ref = j["extra_params"]["latent"]["ref"]
    b = box(T276 / "proxies" / ref)
    if b is None: print(f"skip {name}: static proxy", file=sys.stderr); continue
    k = dict(j); k["name"] = name.replace("t276_", "t332_").replace("_nphys", "_rln")
    k["image"] = str(T276 / "inputs" / Path(j["image"]).name); k["files"] = [str(T276 / "proxies" / ref)]
    ep = json.loads(json.dumps(j["extra_params"])); ep["latent"]["band"] = {"band": "region", "box": b}
    k["extra_params"] = ep; out.append(k)
for k in out: print(json.dumps(k))
print(len(out), "jobs", file=sys.stderr)
