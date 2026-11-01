"""Build the Bridge robot-prediction dev set for Cosmos3-Nano forward dynamics.

For each episode this writes:
  <out>/<ep>/first_frame.png     conditioning frame (real frame 0, 256x256)
  <out>/<ep>/action_chunks.json  same schema as the Nano model card's
                                 example_action_fd_agibotworld_action_chunks.json
  <out>/<ep>/real.mp4            real frames 0..16*n_chunks (ground-truth future)

Actions follow NVIDIA's BridgeOrigLeRobotDataset (cosmos-framework@55f0554):
10-D [pos_delta(3), rot6d_delta(6), gripper(1)], backward-framewise, after the
same frame corrections, then quantile-normalised with bridge_orig_lerobot_stats.json.

Usage: python build_devset.py <episodes_dir> <devset.json> <out_dir> [n_chunks=2]
"""
from __future__ import annotations

import json
import os
import sys

import av
import numpy as np
import pandas as pd
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nv_pose_utils import build_abs_pose_from_components, pose_abs_to_rel  # noqa: E402

CHUNK = 16
FPS = 5
_DEFAULT_ROTATION = np.array([[0.0, 0.0, 1.0], [0.0, 1.0, 0.0], [-1.0, 0.0, 0.0]], dtype=np.float32)
_BRIDGE_TO_OPENCV = np.array([[0.0, 0.0, 1.0], [-1.0, 0.0, 0.0], [0.0, -1.0, 0.0]], dtype=np.float32)
_TCP_TO_FLANGE = np.array(
    [[1.0, 0.0, 0.0, -0.093575], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [0.0, 0.0, 0.0, 1.0]], dtype=np.float32
)
STATS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bridge_orig_lerobot_stats.json")))
Q01, Q99 = np.array(STATS["q01"], np.float32), np.array(STATS["q99"], np.float32)


def raw_actions(state: np.ndarray, action: np.ndarray, start: int) -> np.ndarray:
    """NVIDIA's _build_raw_action for observation rows start..start+16 (17 rows)."""
    obs = state[start : start + CHUNK + 1]
    poses = build_abs_pose_from_components(obs[:, 0:3], obs[:, 3:6], "euler_xyz")
    poses[:, :3, :3] = poses[:, :3, :3] @ _DEFAULT_ROTATION.astype(poses.dtype)
    poses = poses @ _TCP_TO_FLANGE.astype(poses.dtype)
    poses[:, :3, :3] = poses[:, :3, :3] @ _BRIDGE_TO_OPENCV.astype(poses.dtype)
    rel = pose_abs_to_rel(poses, rotation_format="rot6d", pose_convention="backward_framewise")
    grip = action[start : start + CHUNK, 6:7].astype(np.float32)
    return np.concatenate([rel[-CHUNK:], grip], axis=-1)


def normalize(a: np.ndarray) -> np.ndarray:
    return 2.0 * (a - Q01) / np.clip(Q99 - Q01, 1e-8, None) - 1.0


def read_frames(path: str) -> np.ndarray:
    with av.open(path) as c:
        return np.stack([f.to_ndarray(format="rgb24") for f in c.decode(video=0)])


def write_mp4(path: str, frames: np.ndarray, fps: int) -> None:
    with av.open(path, "w") as c:
        s = c.add_stream("libx264", rate=fps)
        s.width, s.height, s.pix_fmt = frames.shape[2], frames.shape[1], "yuv420p"
        s.options = {"crf": "0"}  # lossless-ish ground truth
        for fr in frames:
            for p in s.encode(av.VideoFrame.from_ndarray(fr, format="rgb24")):
                c.mux(p)
        for p in s.encode():
            c.mux(p)


def main(ep_dir: str, devset_path: str, out: str, n_chunks: int = 2) -> None:
    dev = json.load(open(devset_path))
    n_frames = CHUNK * n_chunks + 1
    index = []
    for e in dev["episodes"]:
        i = e["episode_index"]
        df = pd.read_parquet(os.path.join(ep_dir, f"episode_{i:06d}.parquet"))
        state = np.stack(df["observation.state"].to_numpy()).astype(np.float32)
        action = np.stack(df["action"].to_numpy()).astype(np.float32)
        frames = read_frames(os.path.join(ep_dir, f"episode_{i:06d}.mp4"))
        assert len(frames) >= n_frames and len(state) >= n_frames, (i, len(frames), len(state))
        chunks = [normalize(raw_actions(state, action, k * CHUNK)) for k in range(n_chunks)]
        d = os.path.join(out, f"bridge_{i:06d}")
        os.makedirs(d, exist_ok=True)
        Image.fromarray(frames[0]).save(os.path.join(d, "first_frame.png"))
        write_mp4(os.path.join(d, "real.mp4"), frames[:n_frames], FPS)
        spec = {
            "prompt": e["tasks"][0],
            "domain_name": "bridge_orig_lerobot",
            "view_point": "ego_view",
            "fps": FPS,
            "image_size": 256,
            "action_chunk_size": CHUNK,
            "num_chunks": n_chunks,
            "description": f"Bridge episode {i}: {n_chunks} quantile-normalised 10-D WidowX chunks "
            "(NVIDIA BridgeOrigLeRobotDataset convention). Condition chunk 0 on first_frame.png; "
            "later chunks on the last generated frame of the previous chunk.",
            "action_chunks": [c.round(6).tolist() for c in chunks],
            "frac_outside_unit": float(np.mean(np.abs(np.stack(chunks)) > 1.0)),
        }
        json.dump(spec, open(os.path.join(d, "action_chunks.json"), "w"))
        index.append({"id": f"bridge_{i:06d}", "episode_index": i, "prompt": e["tasks"][0]})
    json.dump({"source": dev["source"], "selection": dev["selection"], "n_chunks": n_chunks, "clips": index},
              open(os.path.join(out, "index.json"), "w"), indent=1)
    print(f"wrote {len(index)} clips to {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]) if len(sys.argv) > 4 else 2)
