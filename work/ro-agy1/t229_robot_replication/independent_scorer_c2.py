#!/usr/bin/env python3
"""Independent Scorer for Task 210 Chunk 2 Rollout (Amendment 2).
Scores the full 2-chunk autoregressive rollout (chunk 1 [17f] + chunk 2[1:] [16f] = 33f vs real 33f).
Computes PSNR, SSIM, LPIPS-alex on:
1. Window 'all' (frames 1..32)
2. Window 'c2' (frames 17..32)
Also verifies continuity: |chunk2 f0 - chunk1 f16| MAD.
Compares numerical concordance against rahul-api's scores_c2_all.json and scores_c2_c2.json.
"""
import glob, json, os, re, sys
import av
import numpy as np
import torch
import lpips
from skimage.metrics import peak_signal_noise_ratio, structural_similarity

DEVSET_DIR = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/tools/robot_pred/devset_bridge"
CLIPS_C1_DIR = "/home/rohith/swarm-work/ro-agy1/t210_clips"
CLIPS_C2_DIR = "/home/rohith/swarm-work/ro-agy1/t210_clips_c2"
REPLICATION_DIR = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/ro-agy1/t229_robot_replication"
OUT_ALL_PATH = os.path.join(REPLICATION_DIR, "independent_scores_c2_all.json")
OUT_C2_PATH = os.path.join(REPLICATION_DIR, "independent_scores_c2_c2.json")
AUTHOR_ALL_PATH = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/rahul-api/t210/scores_c2_all.json"
AUTHOR_C2_PATH = "/home/rohith/swarm-work/ro-agy1/cosmos-swarm/work/rahul-api/t210/scores_c2_c2.json"

def read_video(path: str) -> np.ndarray:
    with av.open(path) as container:
        frames = [f.to_ndarray(format="rgb24") for f in container.decode(video=0)]
    return np.stack(frames)

def compute_metrics(pred: np.ndarray, gt: np.ndarray, loss_fn) -> dict:
    n_frames = len(pred)
    psnr_vals = [peak_signal_noise_ratio(gt[i], pred[i], data_range=255) for i in range(n_frames)]
    ssim_vals = [structural_similarity(gt[i], pred[i], channel_axis=-1, data_range=255) for i in range(n_frames)]

    ta = torch.from_numpy(pred).permute(0, 3, 1, 2).float() / 127.5 - 1.0
    tb = torch.from_numpy(gt).permute(0, 3, 1, 2).float() / 127.5 - 1.0
    with torch.no_grad():
        lp_vals = loss_fn(ta, tb).flatten().numpy()

    return {
        "psnr": float(np.mean(psnr_vals)),
        "ssim": float(np.mean(ssim_vals)),
        "lpips": float(np.mean(lp_vals))
    }

def main():
    print("Initializing AlexNet LPIPS model...")
    loss_fn = lpips.LPIPS(net="alex", verbose=False).eval()

    print(f"Loading devset real clips (33 frames) from {DEVSET_DIR}...")
    with open(os.path.join(DEVSET_DIR, "index.json"), "r") as f:
        idx = json.load(f)

    real_clips = {}
    for c in idx["clips"]:
        cid = c["id"]
        vpath = os.path.join(DEVSET_DIR, cid, "real.mp4")
        real_clips[cid] = read_video(vpath)[:33]  # frames 0..32
    print(f"Loaded {len(real_clips)} real video targets.")

    windows = {
        "all": (1, 33),
        "c2": (17, 33)
    }

    # 1. Static floor
    static_floors = {"all": {}, "c2": {}}
    for cid, r in real_clips.items():
        for w, (a, b) in windows.items():
            pred_static = np.repeat(r[:1], b - a, axis=0)
            gt = r[a:b]
            static_floors[w][cid] = compute_metrics(pred_static, gt, loss_fn)

    # 2. Score rollouts
    c2_files = sorted(glob.glob(os.path.join(CLIPS_C2_DIR, "t210c2_*.mp4")))
    print(f"Found {len(c2_files)} Chunk-2 generated clips to score.")
    assert len(c2_files) == 288, f"Expected 288 clips, found {len(c2_files)}"

    outs = {"all": {"static": static_floors["all"], "clips": {}},
            "c2": {"static": static_floors["c2"], "clips": {}}}

    max_c2_mad = 0.0
    for idx_num, p in enumerate(c2_files):
        name2 = os.path.basename(p)[:-4]
        name1 = name2.replace("t210c2_", "t210_")
        m = re.match(r"t210c2_(base|R|N)_(bridge_\d+)_s(\d+)$", name2)
        if not m:
            print(f"Skipping unexpected filename: {name2}")
            continue
        arm, cid, seed_str = m.groups()
        seed = int(seed_str)

        g1_path = os.path.join(CLIPS_C1_DIR, name1 + ".mp4")
        g1 = read_video(g1_path)
        g2 = read_video(p)
        assert len(g1) == 17, f"{name1} length {len(g1)}"
        assert len(g2) == 17, f"{name2} length {len(g2)}"

        # Check conditioning continuity
        c2_cond_mad = float(np.abs(g2[0].astype(float) - g1[-1].astype(float)).mean())
        if c2_cond_mad > max_c2_mad:
            max_c2_mad = c2_cond_mad

        roll = np.concatenate([g1, g2[1:]])
        r = real_clips[cid]
        assert len(roll) == 33 and len(r) == 33

        for w, (a, b) in windows.items():
            m_res = compute_metrics(roll[a:b], r[a:b], loss_fn)
            mot_pred = float(np.abs(roll[a:b].astype(float) - roll[:1].astype(float)).mean())
            mot_real = float(np.abs(r[a:b].astype(float) - r[:1].astype(float)).mean())

            outs[w]["clips"][name1] = {
                "arm": arm,
                "clip": cid,
                "seed": seed,
                **m_res,
                "motion_mad": mot_pred,
                "motion_mad_real": mot_real,
                "c2_cond_vs_c1_last_mad": c2_cond_mad
            }

        if (idx_num + 1) % 48 == 0 or (idx_num + 1) == len(c2_files):
            print(f"Scored {idx_num + 1}/288 rollouts...")

    print(f"Scoring complete. Maximum |c2 f0 - c1 f16| MAD across all 288 clips: {max_c2_mad:.4f}")

    # Save results
    with open(OUT_ALL_PATH, "w") as f:
        json.dump(outs["all"], f, indent=1)
    print(f"Saved independent 'all' scores to {OUT_ALL_PATH}")

    with open(OUT_C2_PATH, "w") as f:
        json.dump(outs["c2"], f, indent=1)
    print(f"Saved independent 'c2' scores to {OUT_C2_PATH}")

    # Numerical concordance audit against author's published scores
    print("\n--- 3. Numerical Concordance Audit vs Author Scores ---")
    for w, out_file, auth_file in [("all", OUT_ALL_PATH, AUTHOR_ALL_PATH), ("c2", OUT_C2_PATH, AUTHOR_C2_PATH)]:
        with open(auth_file, "r") as f:
            auth_data = json.load(f)
        my_data = outs[w]

        max_diffs = {"psnr": 0.0, "ssim": 0.0, "lpips": 0.0, "motion_mad": 0.0, "c2_cond_vs_c1_last_mad": 0.0}
        for name, my_row in my_data["clips"].items():
            auth_row = auth_data["clips"][name]
            for metric in max_diffs:
                diff = abs(my_row[metric] - auth_row[metric])
                if diff > max_diffs[metric]:
                    max_diffs[metric] = diff

        print(f"Max discrepancies in window '{w}':")
        for k, v in max_diffs.items():
            print(f"  {k}: {v:.2e}")
        assert max_diffs["lpips"] < 1e-6, f"LPIPS discrepancy too large in {w}: {max_diffs['lpips']}"
        assert max_diffs["psnr"] < 1e-6, f"PSNR discrepancy too large in {w}: {max_diffs['psnr']}"
        assert max_diffs["ssim"] < 1e-6, f"SSIM discrepancy too large in {w}: {max_diffs['ssim']}"
        print(f"Window '{w}' scores confirmed bit-identical within float precision!")

if __name__ == "__main__":
    main()
