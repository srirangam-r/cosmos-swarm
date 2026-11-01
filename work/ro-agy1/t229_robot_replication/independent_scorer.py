#!/usr/bin/env python3
"""Independent Scorer for Task 210 clips against real devset_bridge.
Computes PSNR, SSIM, LPIPS-alex on frames 1..16, frame-0 conditioning echo, and motion MAD.
"""
import glob, json, os, re, sys
import av
import numpy as np
import torch
import lpips
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

DEVSET_DIR = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/tools/robot_pred/devset_bridge"
CLIPS_DIR = "/home/rohith/swarm-work/ro-agy1/t210_clips"
OUT_PATH = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/ro-agy1/t229_robot_replication/independent_scores.json"

def read_video(path: str) -> np.ndarray:
    with av.open(path) as container:
        frames = [f.to_ndarray(format="rgb24") for f in container.decode(video=0)]
    return np.stack(frames)

def main():
    print("Initializing AlexNet LPIPS model...")
    loss_fn = lpips.LPIPS(net="alex", verbose=False).eval()

    print(f"Loading devset real clips from {DEVSET_DIR}...")
    with open(os.path.join(DEVSET_DIR, "index.json"), "r") as f:
        idx = json.load(f)
    
    real_clips = {}
    for c in idx["clips"]:
        cid = c["id"]
        vpath = os.path.join(DEVSET_DIR, cid, "real.mp4")
        real_clips[cid] = read_video(vpath)[:17]  # frames 0..16
    print(f"Loaded {len(real_clips)} real video targets.")

    # 1. Compute static floor baseline
    print("Computing static floor baseline (repeating frame 0 for frames 1..16)...")
    static_floor = {}
    for cid, r in real_clips.items():
        # pred is 16 copies of frame 0
        pred_static = np.repeat(r[:1], 16, axis=0)
        gt = r[1:17]
        psnr_vals = [peak_signal_noise_ratio(gt[i], pred_static[i], data_range=255) for i in range(16)]
        ssim_vals = [structural_similarity(gt[i], pred_static[i], channel_axis=-1, data_range=255) for i in range(16)]
        
        ta = torch.from_numpy(pred_static).permute(0, 3, 1, 2).float() / 127.5 - 1.0
        tb = torch.from_numpy(gt).permute(0, 3, 1, 2).float() / 127.5 - 1.0
        with torch.no_grad():
            lp_vals = loss_fn(ta, tb).flatten().numpy()
        
        static_floor[cid] = {
            "psnr": float(np.mean(psnr_vals)),
            "ssim": float(np.mean(ssim_vals)),
            "lpips": float(np.mean(lp_vals))
        }

    # 2. Score generated clips
    mp4_files = sorted(glob.glob(os.path.join(CLIPS_DIR, "t210_*.mp4")))
    print(f"Found {len(mp4_files)} generated clips to score.")
    assert len(mp4_files) == 288, f"Expected 288 clips, found {len(mp4_files)}"

    clip_results = {}
    for idx_num, p in enumerate(mp4_files):
        fname = os.path.basename(p)[:-4]
        m = re.match(r"t210_(base|R|N)_(bridge_\d+)_s(\d+)$", fname)
        if not m:
            print(f"Skipping unexpected filename: {fname}")
            continue
        arm, cid, seed_str = m.groups()
        seed = int(seed_str)

        gen = read_video(p)
        assert gen.shape[0] == 17, f"Clip {fname} has {gen.shape[0]} frames (expected 17)"
        assert gen.shape[1:3] == (256, 256), f"Clip {fname} size mismatch: {gen.shape}"

        gt = real_clips[cid]
        # Frame 0 echo
        e0 = float(np.abs(gen[0].astype(float) - gt[0].astype(float)).mean())

        # Motion MAD
        mot_pred = float(np.abs(gen[1:17].astype(float) - gen[:1].astype(float)).mean())
        mot_real = float(np.abs(gt[1:17].astype(float) - gt[:1].astype(float)).mean())

        # Frame 1..16 metrics
        psnr_vals = [peak_signal_noise_ratio(gt[i+1], gen[i+1], data_range=255) for i in range(16)]
        ssim_vals = [structural_similarity(gt[i+1], gen[i+1], channel_axis=-1, data_range=255) for i in range(16)]

        ta = torch.from_numpy(gen[1:17]).permute(0, 3, 1, 2).float() / 127.5 - 1.0
        tb = torch.from_numpy(gt[1:17]).permute(0, 3, 1, 2).float() / 127.5 - 1.0
        with torch.no_grad():
            lp_vals = loss_fn(ta, tb).flatten().numpy()

        clip_results[fname] = {
            "arm": arm,
            "clip": cid,
            "seed": seed,
            "psnr": float(np.mean(psnr_vals)),
            "ssim": float(np.mean(ssim_vals)),
            "lpips": float(np.mean(lp_vals)),
            "frame0_mad": e0,
            "motion_mad": mot_pred,
            "motion_mad_real": mot_real,
            "motion_ratio": float(mot_pred / max(mot_real, 1e-6))
        }

        if (idx_num + 1) % 48 == 0:
            print(f"Scored {idx_num + 1}/{len(mp4_files)} clips...")

    output_data = {
        "static_floor": static_floor,
        "clips": clip_results
    }

    with open(OUT_PATH, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"Done! Wrote independent scores for {len(clip_results)} clips to {OUT_PATH}")

if __name__ == "__main__":
    main()
