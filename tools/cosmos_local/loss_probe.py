"""Rectified-flow denoising-loss probe for Cosmos3-Nano (served as POST /v1/probe/loss by server.py).

Adapted from codex-api-1's loss_probe/probe.py (same maths, same controls), made to run inside the server on the loaded
pipeline, with per-latent-frame losses and an optional I2V conditioning image.

For each clip variant (forward / reverse / freeze_first), noise level sigma and noise seed:
    z_sigma = (1 - sigma) * z_clean + sigma * eps         target = eps - z_clean        (what NVIDIA trains on)
    loss    = mean((v_theta(z_sigma, t = 1000*sigma, text) - target)^2)   over the noisy latent elements
Controls kept from codex-api-1: eps is drawn once per seed on the CPU (torch.Generator) and shared by every variant and
sigma, so variants are paired; the VAE posterior mode is used (pipeline `_encode_video`); one conditional pass only (no CFG);
an identical-input repeat is run first and must agree; everything is recorded in the result.
With a conditioning image the pipeline's I2V packing is used: latent frame 0 is the clean image latent, stays clean, gets no
timestep embedding, and is excluded from the loss (its per-frame loss is null).
"""
import math
import time

import numpy as np
import torch

DEFAULTS = dict(sigmas=[0.1, 0.3, 0.5, 0.7, 0.9], seeds=[1, 2], variants=["forward"], determinism_check=True,
                determinism_tolerance=1e-6, image_from_video_frame0=False)
VARIANTS = ("forward", "reverse", "freeze_first")
ALLOWED = set(DEFAULTS) | {"num_frames", "start", "fps", "size", "rope"}


class ProbeError(ValueError):
    """Bad probe request; the server answers 400."""


def validate(settings: dict, n_available: int) -> dict:
    s = {**DEFAULTS, **settings}
    extra = set(settings) - ALLOWED
    if extra:
        raise ProbeError(f"unknown settings {sorted(extra)}; allowed: {sorted(ALLOWED)}")
    sig, seeds = s["sigmas"], s["seeds"]
    if not isinstance(sig, list) or not sig or any(isinstance(x, bool) or not isinstance(x, (int, float)) or not 0 < x < 1 for x in sig):
        raise ProbeError("sigmas must be a non-empty list of numbers strictly between 0 and 1")
    if len(set(sig)) != len(sig):
        raise ProbeError("sigmas must be unique")
    if not isinstance(seeds, list) or not seeds or len(set(seeds)) != len(seeds) or any(not isinstance(x, int) or not 0 <= x < 2**63 for x in seeds):
        raise ProbeError("seeds must be a non-empty list of unique integers in [0, 2**63)")
    if not isinstance(s["variants"], list) or not s["variants"] or any(v not in VARIANTS for v in s["variants"]):
        raise ProbeError(f"variants must be a non-empty list from {list(VARIANTS)}")
    if len(set(s["variants"])) != len(s["variants"]):
        raise ProbeError("variants must be unique")
    start = int(s.get("start", 0))
    n = s.get("num_frames")
    if n is None:  # the longest 4k+1 window that fits
        n = (n_available - start - 1) // 4 * 4 + 1
    n = int(n)
    if start < 0 or n < 5 or (n - 1) % 4 or start + n > n_available:
        raise ProbeError(f"need 4k+1 >= 5 frames inside the video: start={start}, num_frames={n}, video has {n_available}")
    s.update(start=start, num_frames=n)
    if s.get("fps") is not None and not (isinstance(s["fps"], (int, float)) and s["fps"] > 0):
        raise ProbeError("fps must be positive")
    return s


def decode_video(data: bytes, size=None):
    """mp4 bytes -> (uint8 [T,H,W,3], fps). Resizes to `size` ("WxH") if given. H and W must be multiples of 16."""
    import io, av
    from PIL import Image
    try:
        with av.open(io.BytesIO(data)) as c:
            stream = c.streams.video[0]
            fps = float(stream.average_rate) if stream.average_rate else None
            frames = [f.to_ndarray(format="rgb24") for f in c.decode(video=0)]
    except Exception as e:
        raise ProbeError(f"cannot decode the uploaded video: {type(e).__name__}: {e}")
    if not frames:
        raise ProbeError("the uploaded video has no frames")
    if size:
        w, h = (int(v) for v in str(size).lower().split("x"))
        frames = [np.asarray(Image.fromarray(f).resize((w, h), Image.LANCZOS)) for f in frames]
    video = np.ascontiguousarray(np.stack(frames))
    if video.shape[1] % 16 or video.shape[2] % 16:
        raise ProbeError(f"video frames are {video.shape[2]}x{video.shape[1]}; width and height must be multiples of 16 "
                         f"(pass settings.size, e.g. \"832x480\")")
    return video, fps


def make_variant(frames: np.ndarray, name: str) -> np.ndarray:
    if name == "forward":
        return frames
    if name == "reverse":  # reverse the decoded RGB frames BEFORE the VAE (latent time-reversal is not the same thing)
        return frames[::-1]
    if name == "freeze_first":  # a clip with no motion at all, same first frame
        return np.repeat(frames[:1], len(frames), axis=0)
    raise ProbeError(name)


def video_tensor(frames: np.ndarray, device):
    arr = np.ascontiguousarray(frames)
    return torch.from_numpy(arr).to(device=device, dtype=torch.float32).permute(3, 0, 1, 2).unsqueeze(0).div(127.5).sub(1)


def flow_inputs(clean, noise, sigma, cond_mask=None):
    """(model input, velocity target). Conditioning frames (cond_mask [T,1,1] == 1) stay clean, as in the pipeline."""
    if clean.dtype != torch.float32 or noise.dtype != torch.float32:
        raise ValueError("noise and clean latent must be float32")
    noisy = (1 - sigma) * clean + sigma * noise
    if cond_mask is not None:
        noisy = cond_mask * clean + (1 - cond_mask) * noisy
    return noisy, noise - clean


def frame_losses(pred, target, noisy_frames):
    """(mean over all noisy elements, per-latent-frame mean list with None for conditioning frames). pred/target [1,C,T,H,W]."""
    se = (pred.float() - target).square()
    per = se.mean(dim=(0, 1, 3, 4))  # [T]
    idx = torch.as_tensor(noisy_frames, device=se.device, dtype=torch.long)
    overall = se[:, :, idx].mean().item()
    per = per.tolist()
    return overall, [per[t] if t in set(noisy_frames) else None for t in range(len(per))]


def pack(pipe, clean, prompt, fps, num_frames, height, width, cond_frames):
    """Text + vision packing exactly as Cosmos3OmniPipeline.__call__ does it (one conditional branch)."""
    device = clean.device
    ids, _ = pipe.tokenize_prompt(prompt, None, num_frames=num_frames, height=height, width=width, fps=fps)
    text = pipe._prepare_text_segment(ids, device=device)
    vision = pipe._prepare_vision_segment(
        input_vision_tokens=clean, has_image_condition=bool(cond_frames), mrope_offset=text["vision_start_temporal_offset"],
        vision_fps=fps, curr=text["und_len"], device=device, condition_frame_indexes=list(cond_frames))
    noisy = vision["vision_noisy_frame_indexes"][0].tolist()
    if sorted(noisy) != [t for t in range(clean.shape[2]) if t not in cond_frames]:
        raise RuntimeError(f"unexpected noisy frames {noisy} for condition frames {cond_frames}")
    return {**text, **vision, "position_ids": torch.cat([text["text_mrope_ids"], vision["vision_mrope_ids"]], dim=1),
            "sequence_length": text["und_len"] + vision["num_vision_tokens"]}, noisy


def predict(pipe, packed, noisy, sigma):
    timesteps = torch.full((packed["num_noisy_vision_tokens"],), 1000.0 * sigma, device=noisy.device)
    preds, sound, action = pipe.transformer(
        input_ids=packed["input_ids"], text_indexes=packed["text_indexes"], position_ids=packed["position_ids"],
        und_len=packed["und_len"], sequence_length=packed["sequence_length"],
        vision_tokens=[noisy.to(dtype=pipe.transformer.dtype)], vision_token_shapes=packed["vision_token_shapes"],
        vision_sequence_indexes=packed["vision_sequence_indexes"], vision_mse_loss_indexes=packed["vision_mse_loss_indexes"],
        vision_timesteps=timesteps, vision_noisy_frame_indexes=packed["vision_noisy_frame_indexes"], return_dict=False)
    if sound is not None or action is not None or len(preds) != 1:
        raise RuntimeError("unexpected model output modalities or batch")
    pred = preds[0].float()
    if pred.shape != noisy.shape or not torch.isfinite(pred).all():
        raise RuntimeError(f"unexpected or nonfinite model prediction {tuple(pred.shape)}")
    return pred


def _mean(xs):
    return sum(xs) / len(xs)


def summarize(rows, variants):
    out = {}
    for v in variants:
        r = [x for x in rows if x["variant"] == v]
        pf = [x["per_frame"] for x in r]
        out[v] = dict(mean_loss=_mean([x["loss"] for x in r]),
                      mean_per_frame=[None if pf[0][t] is None else _mean([p[t] for p in pf]) for t in range(len(pf[0]))],
                      by_sigma={str(s): _mean([x["loss"] for x in r if x["sigma"] == s]) for s in sorted({x["sigma"] for x in r})})
    paired = {}
    for v in variants[1:]:
        key = lambda x: (x["sigma"], x["seed"])
        base = {key(x): x for x in rows if x["variant"] == variants[0]}
        d = [(x, base[key(x)]) for x in rows if x["variant"] == v]
        paired[f"{v}_minus_{variants[0]}"] = dict(
            mean_delta=_mean([a["loss"] - b["loss"] for a, b in d]), n_pairs=len(d),
            frac_pairs_positive=_mean([float(a["loss"] > b["loss"]) for a, b in d]),
            mean_delta_per_frame=[None if d[0][0]["per_frame"][t] is None else _mean([a["per_frame"][t] - b["per_frame"][t] for a, b in d])
                                  for t in range(len(d[0][0]["per_frame"]))])
    return out, paired


def run_probe(pipe, video: np.ndarray, source_fps, prompt: str, image, settings: dict) -> dict:
    """video uint8 [T,H,W,3] (already a 4k+1 window); image PIL or None. Returns the JSON-able result."""
    from diffusers.pipelines.cosmos.pipeline_cosmos3_omni import _preprocess_conditioning_image
    t0 = time.time()
    s, fps = settings, float(settings.get("fps") or source_fps or 24.0)
    nf, (H, W) = len(video), video.shape[1:3]
    device = pipe._get_execution_device()
    with torch.no_grad():
        if image is None and s["image_from_video_frame0"]:
            from PIL import Image
            image = Image.fromarray(video[0])
        cond_latent = None
        if image is not None:  # the pipeline's own I2V path: the image repeated over all frames, encoded as a clip
            img = _preprocess_conditioning_image(image, height=H, width=W).to(device=device, dtype=torch.float32)
            clip = torch.zeros(1, 3, nf, H, W, dtype=torch.float32, device=device)
            clip[:, :, 0] = img
            clip[:, :, 1:] = img.unsqueeze(2).expand(-1, -1, nf - 1, -1, -1)
            cond_latent = pipe._encode_video(clip).contiguous().float()[:, :, :1]
        latents = {}
        for name in s["variants"]:
            z = pipe._encode_video(video_tensor(make_variant(video, name), device)).contiguous().float()
            expected_t = (nf - 1) // pipe.vae_scale_factor_temporal + 1
            if z.ndim != 5 or z.shape[0] != 1 or z.shape[2] != expected_t or not torch.isfinite(z).all():
                raise RuntimeError(f"bad VAE output shape {tuple(z.shape)}, expected T={expected_t}")
            if cond_latent is not None:
                z[:, :, :1] = cond_latent  # the conditioning frame is the same clean latent for every variant
            latents[name] = z
        shape = tuple(next(iter(latents.values())).shape)
        T = shape[2]
        cond_frames = [0] if cond_latent is not None else []
        mask = None
        if cond_frames:
            mask = torch.zeros(T, 1, 1, device=device)
            mask[0] = 1.0
        packed, noisy_frames = pack(pipe, next(iter(latents.values())), prompt, fps, nf, H, W, cond_frames)
        noise = {seed: torch.randn(shape, generator=torch.Generator(device="cpu").manual_seed(seed), dtype=torch.float32).to(device)
                 for seed in s["seeds"]}

        def score(z, eps, sigma):
            noisy, target = flow_inputs(z, eps, sigma, mask)
            return frame_losses(predict(pipe, packed, noisy, sigma), target, noisy_frames)

        pre = None
        if s["determinism_check"]:
            z0 = latents[s["variants"][0]]
            a, b = score(z0, noise[s["seeds"][0]], s["sigmas"][0])[0], score(z0, noise[s["seeds"][0]], s["sigmas"][0])[0]
            if abs(a - b) > s["determinism_tolerance"]:
                raise RuntimeError(f"identical-input repeat disagrees: {a} vs {b} (tolerance {s['determinism_tolerance']})")
            pre = [a, b]
        rows = []
        for sigma in s["sigmas"]:
            for seed in s["seeds"]:
                for name in s["variants"]:
                    loss, per = score(latents[name], noise[seed], sigma)
                    rows.append(dict(variant=name, sigma=sigma, seed=seed, loss=loss, per_frame=per))
    by_variant, paired = summarize(rows, s["variants"])
    return dict(
        probe="rectified-flow velocity MSE (surrogate for denoising loss; not a likelihood)",
        loss_definition="mean over noisy latent elements of (v_pred - (eps - z_clean))^2; z_sigma=(1-sigma)z+sigma*eps; t=1000*sigma; "
                        "one conditional pass, no CFG; conditioning frames excluded (per_frame null)",
        prompt=prompt, settings={k: v for k, v in s.items() if k != "rope"}, fps=fps, source_fps=source_fps,
        frames_used=nf, size=f"{W}x{H}", latent_shape=list(shape), conditioning_frames=cond_frames,
        conditioning=("image (I2V packing, latent frame 0 clean)" if cond_frames else "none (T2V packing)"),
        noise="torch.randn on CPU, Generator.manual_seed(seed), float32, shared by all variants and sigmas",
        vae_posterior="mode", determinism_preflight=pre, rows=rows, summary=by_variant, paired=paired,
        seconds=round(time.time() - t0, 1), torch=torch.__version__)
