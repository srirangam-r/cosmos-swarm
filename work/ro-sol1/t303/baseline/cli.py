"""
nano_phys.cli: Command-line interface for Nano-Phys.
"""

import argparse
import json
import os
from pathlib import Path
import sys

from .proxy import generate_pendulum_proxy, generate_ball_proxy
from .runner import run_remote_nanophys, run_local_nanophys


def parse_coords(s: str) -> tuple[int, int]:
    try:
        parts = [int(v.strip()) for v in s.split(",")]
        if len(parts) != 2:
            raise ValueError
        return (parts[0], parts[1])
    except Exception:
        raise argparse.ArgumentTypeError(f"Invalid coordinate format '{s}', expected 'X,Y'")


def main():
    parser = argparse.ArgumentParser(
        prog="python -m nano_phys",
        description="Nano-Phys: Training-Free Physics-Guided Diffusion for NVIDIA Cosmos3-Nano",
    )

    # Core required inputs
    parser.add_argument("--image", required=True, help="Path to input frame 0 (PNG/JPG)")
    parser.add_argument("--prompt", required=True, help="Text caption prompt for Cosmos3-Nano")
    parser.add_argument("--physics", choices=["pendulum", "ball"], required=True, help="Physics dynamics type")
    parser.add_argument("--out", required=True, help="Output MP4 file path")

    # Pendulum parameters
    parser.add_argument("--pivot", type=parse_coords, default=None, help="Pendulum pivot axle pixel coords 'X,Y'")
    parser.add_argument("--bob", type=parse_coords, default=None, help="Pendulum bob tip pixel coords 'X,Y'")
    parser.add_argument("--period", type=float, default=None, help="Oscillation period in seconds (default: derived from length or 1.18s)")
    parser.add_argument("--amplitude", type=float, default=18.0, help="Initial swing semi-amplitude in degrees (default: 18.0)")
    parser.add_argument("--direction", choices=["inward", "outward"], default="inward", help="Initial swing direction (default: inward)")
    parser.add_argument("--no-release-from-rest", action="store_true", help="Do not enforce initial velocity zero at t=0")

    # Ball drop parameters
    parser.add_argument("--center", type=parse_coords, default=None, help="Ball center pixel coords 'X,Y'")
    parser.add_argument("--radius", type=int, default=13, help="Ball radius in pixels (default: 13)")
    parser.add_argument("--floor-y", type=int, default=340, help="Floor impact y-coordinate in pixels (default: 340)")
    parser.add_argument("--e", type=float, default=0.58, help="Coefficient of restitution (default: 0.58)")

    # Shared physics constants
    parser.add_argument("--g", type=float, default=9.81, help="Gravitational acceleration in m/s^2 (default: 9.81)")

    # Generation & sampling parameters
    parser.add_argument("--start-step", type=int, default=None, help="Diffusion start step index out of 35 (SDEdit t_init; default: 14 = sigma 0.95868)")
    parser.add_argument("--sigma", type=float, default=None, help="Target noise level sigma in [0, 1] (e.g. 0.90 maps to step 19 / sigma 0.89844; overrides --start-step)")
    parser.add_argument("--seed", type=int, default=1, help="RNG seed for CPU noise draws (default: 1)")
    parser.add_argument("--steps", type=int, default=35, help="Total inference steps (default: 35)")
    parser.add_argument("--guidance", type=float, default=6.0, help="Classifier-free guidance scale (default: 6.0)")
    parser.add_argument("--flow-shift", type=float, default=10.0, help="Flow shift parameter (default: 10.0)")
    parser.add_argument("--num-frames", type=int, default=None, help="Number of frames (default: 93 for pendulum, 189 for ball)")
    parser.add_argument("--fps", type=int, default=24, help="Framerate (default: 24)")
    parser.add_argument("--width", type=int, default=832, help="Video width (default: 832)")
    parser.add_argument("--height", type=int, default=480, help="Video height (default: 480)")
    parser.add_argument("--negative-prompt", default="", help="Negative prompt")

    # Backend selection
    parser.add_argument("--server", default=None, help="URL of remote Cosmos3-Nano endpoint (e.g. http://board.tail0c526a.ts.net:8011)")
    parser.add_argument("--proxy-only", action="store_true", help="Generate and output only the analytical proxy video")
    parser.add_argument("--emit-queue-job", action="store_true", help="Output JSONL job line for cosmos_queue.py submission")

    args = parser.parse_args()

    if args.sigma is not None and not (0.0 <= args.sigma <= 1.0):
        parser.error(f"--sigma must be in [0, 1], got {args.sigma}")
    if args.start_step is not None and not (0 <= args.start_step < args.steps):
        parser.error(f"--start-step must be an integer in [0, {args.steps - 1}], got {args.start_step}")

    # Determine default frame count based on physics if not set
    num_frames = args.num_frames
    if num_frames is None:
        num_frames = 93 if args.physics == "pendulum" else 189

    out_p = Path(args.out)
    proxy_mp4 = out_p.parent / f"{out_p.stem}_proxy.mp4"

    # Step 1: Generate analytical physics proxy
    print(f"[Nano-Phys] Generating analytical {args.physics} proxy video...", file=sys.stderr)
    if args.physics == "pendulum":
        if args.pivot is None or args.bob is None:
            parser.error("--pivot X,Y and --bob X,Y are required for pendulum physics")
        proxy_meta = generate_pendulum_proxy(
            image_path=args.image,
            out_path=proxy_mp4,
            pivot=args.pivot,
            bob=args.bob,
            period=args.period,
            g=args.g,
            amplitude_deg=args.amplitude,
            release_from_rest=not args.no_release_from_rest,
            direction=args.direction,
            num_frames=num_frames,
            fps=args.fps,
            width=args.width,
            height=args.height,
        )
    elif args.physics == "ball":
        if args.center is None:
            parser.error("--center X,Y is required for ball physics")
        proxy_meta = generate_ball_proxy(
            image_path=args.image,
            out_path=proxy_mp4,
            center=args.center,
            radius=args.radius,
            floor_y=args.floor_y,
            g=args.g,
            e=args.e,
            num_frames=num_frames,
            fps=args.fps,
            width=args.width,
            height=args.height,
        )

    print(f"[Nano-Phys] Saved proxy video to {proxy_mp4}", file=sys.stderr)

    # Determine effective start step
    from .runner import NATIVE_SIGMAS_35, sigma_to_step
    if args.sigma is not None:
        start_step = sigma_to_step(args.sigma, steps=args.steps)
    elif args.start_step is not None:
        start_step = args.start_step
    else:
        start_step = 14  # default: step 14 (sigma = 0.95868)

    if args.emit_queue_job:
        job = {
            "name": out_p.stem,
            "prompt": args.prompt,
            "image": str(Path(args.image).resolve()),
            "files": [str(proxy_mp4.resolve())],
            "width": args.width,
            "height": args.height,
            "num_frames": num_frames,
            "fps": args.fps,
            "steps": args.steps,
            "guidance": args.guidance,
            "flow_shift": args.flow_shift,
            "seed": args.seed,
            "negative_prompt": args.negative_prompt,
            "extra_params": {
                "client": "nano_phys",
                "noise": {"device": "cpu"},
                "latent": {
                    "ref": proxy_mp4.name,
                    "start_step": start_step,
                    "init": "noised",
                },
            },
        }
        print(json.dumps(job))

    if args.proxy_only or args.emit_queue_job:
        print("[Nano-Phys] Exiting after proxy/job generation.", file=sys.stderr)
        return

    # Step 2: Denoise with Cosmos3-Nano via Latent SDEdit Start
    print(f"[Nano-Phys] Starting diffusion from VAE latent of proxy (start_step={start_step}/35, noise.device=cpu)...")
    if args.server:
        print(f"[Nano-Phys] Dispatching to remote server: {args.server}")
        res = run_remote_nanophys(
            server_url=args.server,
            image_path=args.image,
            proxy_path=proxy_mp4,
            prompt=args.prompt,
            out_mp4=args.out,
            negative_prompt=args.negative_prompt,
            width=args.width,
            height=args.height,
            num_frames=num_frames,
            fps=args.fps,
            steps=args.steps,
            guidance=args.guidance,
            flow_shift=args.flow_shift,
            seed=args.seed,
            start_step=start_step,
            sigma=args.sigma,
        )
    else:
        print(f"[Nano-Phys] Running with local diffusers pipeline...")
        res = run_local_nanophys(
            image_path=args.image,
            proxy_path=proxy_mp4,
            prompt=args.prompt,
            out_mp4=args.out,
            negative_prompt=args.negative_prompt,
            width=args.width,
            height=args.height,
            num_frames=num_frames,
            fps=args.fps,
            steps=args.steps,
            guidance=args.guidance,
            flow_shift=args.flow_shift,
            seed=args.seed,
            start_step=start_step,
            sigma=args.sigma,
        )

    print(f"[Nano-Phys] Generation complete! Output saved to: {args.out}")
    print(f"[Nano-Phys] JSON sidecar saved to: {Path(args.out).with_suffix('.json')}")


if __name__ == "__main__":
    main()
