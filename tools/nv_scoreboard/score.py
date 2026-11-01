#!/usr/bin/env python
"""NVIDIA-scoreboard harness: DOVER (technical/aesthetic/fused) + VBench dynamic degree.

Usage:
  python score.py CLIP_OR_DIR [...] --dover_dir PATH/TO/DOVER --out results.json [--device cpu]
                  [--no_dover] [--no_dd] [--dover_reps 1]

Per clip it reads an optional JSON sidecar (same stem, .json). Motion sampling
uses container playback fps, not the generation conditioning fps in the sidecar.

Dynamic degree follows VBench (vbench/dynamic_degree.py):
  * frames sampled every round(fps/8) frames (~8 fps)
  * RAFT (raft-things == torchvision raft_large C_T_V1), 20 refinement iters
  * per pair: mean of the top-5% flow magnitudes ("max_rad")
  * thres = 6.0 * min(H,W)/256 ; count_num = round(4 * n_frames/16)
  * dd_binary = 1 if #pairs with max_rad > thres >= count_num
  VBench's "dynamic degree" for a set = mean(dd_binary). Because binary scores are
  very coarse for a few clips, we also report the continuous dd_norm =
  mean_pairs(max_rad) / (min(H,W)/256)  (px at a 256-px short side) and dd_frac
  = fraction of pairs above thres. Compare model vs real at the same fps.

DOVER (VQAssessment/DOVER, dover.yml, val-l1080p sampling): raw technical and
aesthetic heads plus the fused overall score in [0,1] (DOVER's fuse_results).
DOVER's fragment sampling is random; --dover_reps N averages N draws and reports sd.
"""
import argparse, glob, json, math, os, sys, time
import numpy as np
import torch


def video_fps(path):
    import av
    c = av.open(path)
    s = c.streams.video[0]
    fps = float(s.average_rate) if s.average_rate else float(s.guessed_rate)
    c.close()
    return fps


def read_frames(path):
    import av
    c = av.open(path)
    fr = [f.to_ndarray(format="rgb24") for f in c.decode(video=0)]
    c.close()
    return np.stack(fr)


_RAFT = None


def raft(device):
    global _RAFT
    if _RAFT is None:
        from torchvision.models.optical_flow import raft_large, Raft_Large_Weights
        _RAFT = raft_large(weights=Raft_Large_Weights.C_T_V1).eval().to(device)
    return _RAFT


def dynamic_degree(path, fps, device="cpu"):
    v = read_frames(path)  # T,H,W,3 uint8
    interval = max(1, round(fps / 8))
    v = v[::interval]
    n = len(v)
    H, W = v.shape[1:3]
    scale = min(H, W)
    thres = 6.0 * (scale / 256.0)
    count_num = round(4 * (n / 16.0))
    m = raft(device)
    ph, pw = (-H) % 8, (-W) % 8  # pad to /8 like RAFT's InputPadder (replicate)
    x = torch.from_numpy(v).permute(0, 3, 1, 2).float()
    x = 2 * (x / 255.0) - 1.0
    if ph or pw:
        x = torch.nn.functional.pad(x, [pw // 2, pw - pw // 2, ph // 2, ph - ph // 2], mode="replicate")
    rads = []
    with torch.no_grad():
        for i in range(n - 1):
            a, b = x[i:i + 1].to(device), x[i + 1:i + 2].to(device)
            flo = m(a, b, num_flow_updates=20)[-1][0]
            if ph or pw:
                flo = flo[:, ph // 2:ph // 2 + H, pw // 2:pw // 2 + W]
            rad = flo.norm(dim=0).flatten()
            k = int(H * W * 0.05)
            rads.append(torch.topk(rad, k).values.mean().item())
    rads = np.array(rads)
    above = int((rads > thres).sum())
    return dict(dd_binary=int(above >= count_num), dd_norm=float(rads.mean() / (scale / 256.0)),
                dd_frac=float(above / len(rads)), dd_pairs=len(rads), dd_interval=interval,
                dd_thres_px=thres, dd_count_num=count_num, dd_maxrad=[round(r, 3) for r in rads.tolist()])


_DOVER = None


def dover_scores(path, dover_dir, device="cpu", reps=1):
    global _DOVER
    import yaml
    if dover_dir not in sys.path:
        sys.path.insert(0, dover_dir)
    from dover.datasets import UnifiedFrameSampler, spatial_temporal_view_decomposition
    from dover.models import DOVER
    opt = yaml.safe_load(open(os.path.join(dover_dir, "dover.yml")))
    if _DOVER is None:
        ev = DOVER(**opt["model"]["args"]).to(device)
        ev.load_state_dict(torch.load(os.path.join(dover_dir, "pretrained_weights/DOVER.pth"), map_location=device))
        _DOVER = ev.eval()
    dopt = opt["data"]["val-l1080p"]["args"]
    samplers = {}
    for st, so in dopt["sample_types"].items():
        if "t_frag" not in so:
            samplers[st] = UnifiedFrameSampler(so["clip_len"], so["num_clips"], so["frame_interval"])
        else:
            samplers[st] = UnifiedFrameSampler(so["clip_len"] // so["t_frag"], so["t_frag"], so["frame_interval"], so["num_clips"])
    mean = torch.FloatTensor([123.675, 116.28, 103.53])
    std = torch.FloatTensor([58.395, 57.12, 57.375])
    tech, aes, fused = [], [], []
    for _ in range(reps):
        views, _ = spatial_temporal_view_decomposition(path, dopt["sample_types"], samplers)
        for k, v in views.items():
            nc = dopt["sample_types"][k].get("num_clips", 1)
            views[k] = (((v.permute(1, 2, 3, 0) - mean) / std).permute(3, 0, 1, 2)
                        .reshape(v.shape[0], nc, -1, *v.shape[2:]).transpose(0, 1).to(device))
        with torch.no_grad():
            r = [t.mean().item() for t in _DOVER(views)]
        # r[0] = technical head, r[1] = aesthetic head (DOVER's evaluate_one_video order)
        x = (r[0] - 0.1107) / 0.07355 * 0.6104 + (r[1] + 0.08285) / 0.03774 * 0.3896
        tech.append(r[0]); aes.append(r[1]); fused.append(1 / (1 + np.exp(-x)))
    sd = lambda a: float(np.std(a, ddof=1)) if len(a) > 1 else None
    return dict(dover_technical=float(np.mean(tech)), dover_aesthetic=float(np.mean(aes)),
                dover_fused=float(np.mean(fused)), dover_fused_sd=sd(fused), dover_technical_sd=sd(tech),
                dover_aesthetic_sd=sd(aes), dover_reps=reps)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--dover_dir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "DOVER"))
    ap.add_argument("--out", default="nv_scores.json")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--no_dover", action="store_true")
    ap.add_argument("--no_dd", action="store_true")
    ap.add_argument("--dover_reps", type=int, default=1)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    torch.manual_seed(a.seed); np.random.seed(a.seed)
    import random; random.seed(a.seed)
    clips = []
    for p in a.inputs:
        clips += sorted(glob.glob(os.path.join(p, "*.mp4"))) if os.path.isdir(p) else [p]
    res = json.load(open(a.out)) if os.path.exists(a.out) else {}
    # Output is keyed by basename for compatibility with existing score files.
    # Refuse collisions up front rather than silently discarding a clip.
    paths_by_name = {k: os.path.abspath(v.get("clip", "")) for k, v in res.items()}
    for c in clips:
        name, path = os.path.basename(c), os.path.abspath(c)
        if name in paths_by_name and paths_by_name[name] != path:
            sys.exit(f"duplicate clip basename {name}: {paths_by_name[name]} and {path}")
        paths_by_name[name] = path
    for c in clips:
        side = os.path.splitext(c)[0] + ".json"
        meta = json.load(open(side)) if os.path.exists(side) else {}
        fps = video_fps(c)
        if not math.isfinite(fps) or fps <= 0:
            sys.exit(f"invalid playback fps for {c}: {fps}")
        if meta.get("play_fps") is not None and not math.isclose(float(meta["play_fps"]), fps, rel_tol=0.001, abs_tol=0.01):
            sys.exit(f"play_fps does not match container for {c}: {meta['play_fps']} vs {fps}")
        r = dict(clip=c, fps=fps, fps_source="container", sidecar=side if meta else None, metadata=meta)
        t0 = time.time()
        if not a.no_dd:
            r.update(dynamic_degree(c, fps, a.device))
        if not a.no_dover:
            r.update(dover_scores(c, a.dover_dir, a.device, a.dover_reps))
        r["sec"] = round(time.time() - t0, 1)
        res[os.path.basename(c)] = r
        print(json.dumps({k: v for k, v in r.items() if k != "dd_maxrad"}), flush=True)
        json.dump(res, open(a.out, "w"), indent=1)


if __name__ == "__main__":
    main()
