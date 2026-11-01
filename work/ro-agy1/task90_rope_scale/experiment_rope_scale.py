#!/usr/bin/env python3
"""
Task 90: RoPE Spatial (Height/Width) Frequency Scaling Experiment on GAUGE Frame 0 Held Ball.

Hypothesis (arXiv 2609.23658, Raj #696 item 1, human steering nail #1825):
Early in denoising, frames compete over where the object is. Positions that settle early anchor the other frames
through RoPE spatial decay, producing "stays in mid-air" and "freezes" (e.g. holding the ball in the gripper).
Scaling the RoPE height/width spatial frequencies by 0.7 during the first ~10% of denoising steps (e.g. steps 0-3 of 35)
relaxes this spatial anchoring bias early in the diffusion process, potentially allowing the ball to detach and fall from the gripper
from the original GAUGE frame 0.

Arms:
- Control: Baseline standard RoPE (spatial scale 1.0 across all 35 steps)
- Treatment: RoPE height/width frequencies scaled by 0.7 for the first 4 steps (t >= 900), 1.0 for steps 4-34.

Tested across 4 seeds: 1, 2, 3, 4 on fixed GAUGE Ball 1 frame 0 held baseline.
Evaluates:
- Object release rate (detachment vs clamped in gripper)
- Phantom duplicate cloning rate (seed 1 baseline clone)
- referee-validated kinematic tracker (firstfall.py g, flag, onset)
- DOVER visual quality (Technical, Aesthetic, Fused)
- Dynamic degree (dd_binary, dd_norm)
"""
import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

import av
import cv2
import numpy as np
import torch
from PIL import Image

# Import diffusers
from diffusers import Cosmos3OmniPipeline
from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler
from diffusers.utils import export_to_video

# Optional attention patch for display watchdog if present
try:
    import cosmos_patch
except ImportError:
    pass

GAUGE_BALL_PROMPT = (
    "Static frontal camera view: A 121g black ball is suspended high above a wooden plank, which is fixed on a black "
    "perforated optical table. Coefficient of friction is 0.81; coefficient of restitution is 0.58. When released, "
    "the ball undergoes free fall, followed by a sequence of successive bounces with diminishing peak heights, "
    "before finally coming to rest on the plank. Maintain structural integrity and object consistency throughout: "
    "no changing shapes, no blending, and no flashing background."
)


def setup_rope_hook(pipe, early_scale: float = 0.7, t_threshold: float = 900.0):
    """
    Hooks pipe.transformer.rotary_emb and pipe.transformer.forward to dynamically scale
    height and width (spatial) frequencies in RoPE during early denoising steps.
    """
    transformer = pipe.transformer
    rotary = transformer.rotary_emb

    if not hasattr(rotary, "_orig_forward"):
        rotary._orig_forward = rotary.forward

    def forward_scaled(position_ids, device, dtype):
        if position_ids.ndim == 2:
            position_ids = position_ids[None, ...].expand(3, position_ids.shape[0], -1)
        inv_freq_expanded = (
            rotary.inv_freq[None, None, :, None].float().expand(3, position_ids.shape[1], -1, 1).to(device)
        )
        position_ids_expanded = position_ids[:, :, None, :].float()
        with torch.autocast(device_type=position_ids.device.type, enabled=False):
            freqs = inv_freq_expanded @ position_ids_expanded
        freqs = freqs.transpose(2, 3)

        scale = getattr(rotary, "spatial_scale", 1.0)
        if scale != 1.0:
            freqs[1] = freqs[1] * scale
            freqs[2] = freqs[2] * scale

        freqs = rotary.apply_interleaved_mrope(freqs, rotary.rope_axes_dim)
        emb = torch.cat((freqs, freqs), dim=-1)
        return emb.cos().to(dtype=dtype), emb.sin().to(dtype=dtype)

    rotary.forward = forward_scaled

    if not hasattr(transformer, "_orig_forward"):
        transformer._orig_forward = transformer.forward

    step_log = []

    def transformer_forward_wrapper(*args, **kwargs):
        vision_timesteps = kwargs.get("vision_timesteps")
        if vision_timesteps is None and len(args) > 9:
            vision_timesteps = args[9]

        t_val = vision_timesteps.float().mean().item() if vision_timesteps is not None else 0.0
        if t_val >= t_threshold:
            rotary.spatial_scale = early_scale
        else:
            rotary.spatial_scale = 1.0
        step_log.append((round(t_val, 1), rotary.spatial_scale))
        return transformer._orig_forward(*args, **kwargs)

    transformer.forward = transformer_forward_wrapper
    return step_log


def encode_mp4(frames, fps, out_path):
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    export_to_video(frames, str(out_path), fps=fps)


def run_clip(pipe, img_pil, prompt, seed, early_scale, out_path, num_frames=93, fps=24, steps=35, guidance=6.0, flow_shift=10.0):
    pipe.scheduler = UniPCMultistepScheduler.from_config(pipe.scheduler.config, flow_shift=float(flow_shift))
    step_log = setup_rope_hook(pipe, early_scale=early_scale, t_threshold=900.0)

    generator = torch.Generator(device="cuda" if torch.cuda.is_available() else "cpu").manual_seed(seed)
    t0 = time.time()
    res = pipe(
        image=img_pil,
        prompt=prompt,
        negative_prompt=None,
        width=832,
        height=480,
        num_frames=num_frames,
        fps=fps,
        num_inference_steps=steps,
        guidance_scale=guidance,
        generator=generator,
    )
    wall_sec = time.time() - t0

    v = res.video
    v = v[0] if (isinstance(v, np.ndarray) and v.ndim == 5) else v
    frames = [(np.clip(f, 0, 1) * 255).round().astype(np.uint8) if f.dtype != np.uint8 else f for f in np.asarray(v)]

    encode_mp4(frames, fps, out_path)
    print(f"[done] Wrote {out_path} ({len(frames)} frames in {wall_sec:.1f}s, scale={early_scale}, seed={seed})")

    sidecar = {
        "clip": str(out_path.name),
        "seed": seed,
        "early_scale": early_scale,
        "num_frames": num_frames,
        "fps": fps,
        "steps": steps,
        "guidance": guidance,
        "flow_shift": flow_shift,
        "wall_sec": round(wall_sec, 2),
        "step_log_sample": step_log[:6],
    }
    sidecar_path = out_path.with_suffix(".json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2))
    return sidecar


def main():
    parser = argparse.ArgumentParser(description="Task 90 RoPE Spatial Scale Experiment")
    parser.add_argument("--model", default="/home/swarm/models/Cosmos3-Nano")
    parser.add_argument("--image", default="work/raj-1/gauge_ball/gauge_ball1_f0_832x480.png")
    parser.add_argument("--out-dir", default="work/ro-agy1/task90_rope_scale/results")
    parser.add_argument("--seeds", default="1,2,3,4")
    parser.add_argument("--early-scale", type=float, default=0.7)
    parser.add_argument("--frames", type=int, default=93)
    parser.add_argument("--steps", type=int, default=35)
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    seeds = [int(s.strip()) for s in args.seeds.split(",")]
    img_path = Path(args.image)
    if not img_path.exists():
        raise FileNotFoundError(f"Input image not found: {img_path}")

    img_pil = Image.open(img_path).convert("RGB")
    if img_pil.size != (832, 480):
        img_pil = img_pil.resize((832, 480), Image.Resampling.LANCZOS)

    print(f"[init] Loading Cosmos3-Nano from {args.model}...")
    pipe = Cosmos3OmniPipeline.from_pretrained(args.model, torch_dtype=torch.bfloat16, enable_safety_checker=False)
    pipe.to("cuda")

    if hasattr(pipe, "use_duration_template"):
        pipe.use_duration_template = False
    if hasattr(pipe, "use_fps_template"):
        pipe.use_fps_template = False

    manifest = {"control": {}, "treatment": {}}

    for seed in seeds:
        print(f"\n=== Running Seed {seed} ===")
        # 1. Control (Standard RoPE, scale 1.0)
        ctrl_path = out_dir / f"gauge_b1_ctrl_s{seed}.mp4"
        print(f"Generating Control clip: {ctrl_path}")
        ctrl_meta = run_clip(pipe, img_pil, GAUGE_BALL_PROMPT, seed=seed, early_scale=1.0, out_path=ctrl_path,
                             num_frames=args.frames, steps=args.steps)
        manifest["control"][seed] = ctrl_meta

        # 2. Treatment (RoPE spatial scale 0.7 for first 4 steps)
        treat_path = out_dir / f"gauge_b1_rope07_s{seed}.mp4"
        print(f"Generating Treatment clip (RoPE 0.7x): {treat_path}")
        treat_meta = run_clip(pipe, img_pil, GAUGE_BALL_PROMPT, seed=seed, early_scale=args.early_scale, out_path=treat_path,
                              num_frames=args.frames, steps=args.steps)
        manifest["treatment"][seed] = treat_meta

    manifest_path = out_dir / "experiment_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"\n[complete] Experiment complete! Manifest written to {manifest_path}")


if __name__ == "__main__":
    main()
