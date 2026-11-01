"""Score predicted robot rollouts against the real future.

Metrics per clip on the predicted frames 1..N (frame 0 is the shared conditioning frame),
at the real clip's resolution (256x256 for Bridge): PSNR (dB, higher=better),
SSIM (higher=better), LPIPS-alex (lower=better). Also reports the same metrics for chunk 1
(frames 1-16) and chunk 2 (17-32) separately, since autoregressive error grows.

Usage:
  python score.py <devset_dir> <pred_dir> <out.json>      # score a generation run
  python score.py <devset_dir> --baseline static <out.json>  # floor: repeat frame 0
Output JSON: per-clip metrics plus mean ± standard error over clips.
"""
from __future__ import annotations

import json
import os
import sys

import av
import lpips
import numpy as np
import torch
from PIL import Image
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

_LPIPS = None


def read(path: str) -> np.ndarray:
    with av.open(path) as c:
        return np.stack([f.to_ndarray(format="rgb24") for f in c.decode(video=0)])


def lp(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    global _LPIPS
    if _LPIPS is None:
        _LPIPS = lpips.LPIPS(net="alex", verbose=False).eval()
    ta = torch.from_numpy(a).permute(0, 3, 1, 2).float() / 127.5 - 1
    tb = torch.from_numpy(b).permute(0, 3, 1, 2).float() / 127.5 - 1
    with torch.no_grad():
        return _LPIPS(ta, tb).flatten().numpy()


def frame_metrics(pred: np.ndarray, real: np.ndarray) -> dict[str, np.ndarray]:
    psnr = np.array([peak_signal_noise_ratio(r, p, data_range=255) for p, r in zip(pred, real)])
    ssim = np.array([structural_similarity(r, p, channel_axis=-1, data_range=255) for p, r in zip(pred, real)])
    return {"psnr": psnr, "ssim": ssim, "lpips": lp(pred, real)}


def score_clip(pred: np.ndarray, real: np.ndarray) -> dict:
    n = len(real)
    if len(pred) != n:
        raise ValueError(f"frame count mismatch: pred {len(pred)} vs real {n}")
    if pred.shape[1:3] != real.shape[1:3]:
        pred = np.stack([np.asarray(Image.fromarray(f).resize(real.shape[2:0:-1], Image.BICUBIC)) for f in pred])
    m = frame_metrics(pred[1:], real[1:])
    out = {k: float(v.mean()) for k, v in m.items()}
    for ci, (a, b) in enumerate([(0, 16), (16, 32)], 1):
        if b <= len(m["psnr"]):
            out.update({f"{k}_chunk{ci}": float(v[a:b].mean()) for k, v in m.items()})
    out["per_frame"] = {k: [round(float(x), 4) for x in v] for k, v in m.items()}
    return out


def summarize(per: dict) -> dict:
    keys = [k for k in next(iter(per.values())) if k != "per_frame"]
    s = {}
    for k in keys:
        v = np.array([c[k] for c in per.values()])
        s[k] = {"mean": float(v.mean()), "se": float(v.std(ddof=1) / np.sqrt(len(v))), "n": int(len(v))}
    return s


def main() -> None:
    devset = sys.argv[1]
    idx = json.load(open(os.path.join(devset, "index.json")))
    baseline = None
    if sys.argv[2] == "--baseline":
        baseline, out_path = sys.argv[3], sys.argv[4]
    else:
        pred_dir, out_path = sys.argv[2], sys.argv[3]
    per = {}
    for c in idx["clips"]:
        real = read(os.path.join(devset, c["id"], "real.mp4"))
        if baseline == "static":
            pred = np.repeat(real[:1], len(real), axis=0)
        else:
            path = os.path.join(pred_dir, c["id"] + ".mp4")
            if not os.path.exists(path):
                continue
            pred = read(path)
        per[c["id"]] = score_clip(pred, real)
    res = {"devset": devset, "pred": baseline or pred_dir, "summary": summarize(per), "clips": per}
    json.dump(res, open(out_path, "w"), indent=1)
    for k, v in res["summary"].items():
        print(f"{k:14s} {v['mean']:.4f} ± {v['se']:.4f} (n={v['n']})")


if __name__ == "__main__":
    main()
