"""Control over the initial noise of a Cosmos3-Nano generation (extra_params.noise).

    "noise": {"device": "cpu"}                      # draw the seed's noise on the CPU: same noise on every GPU type
    "noise": {"device": "cpu", "mix": {"seed": 7, "band": "temporal_low", "cut": 0.25}}

device  "cuda" (default, what the server always did) or "cpu". torch's CUDA RNG maps a seed to different
        numbers on GPUs with different multiprocessor counts, so the same seed is a different noise on q8,
        a6k, l40s and A100. With "cpu" the seed means the same noise everywhere (also used for the VAE sample).
mix     take part of the noise from a second seed B; the rest stays the request's own seed A.
        band "temporal_low"  B's latent-time frequencies with |f| <= cut * 0.5 (Nyquist = 0.5)
             "temporal_high" B's latent-time frequencies with |f| >  cut * 0.5
             "spatial_low"   B's spatial frequencies with max(|fy|, |fx|) <= cut * 0.5 (a square band)
             "spatial_high"  B's spatial frequencies with max(|fy|, |fx|) >  cut * 0.5
             "region"        B inside box [x0, y0, x1, y1] (fractions of width/height), A outside
             "all"           all of B (the arm to compare a mix against: same code path as the mixes)
        Complementary masks of two independent white Gaussian noises give white Gaussian noise again, so a
        mixed noise is still a valid initial noise. An empty band reproduces the plain request exactly; a partial band adds FFT rounding (~1e-7).

The vision noise is the pipeline's first 5-D randn_tensor call (B, C, T, H, W); sound/action noise is untouched.
"""

from __future__ import annotations

import contextlib
import sys
from dataclasses import dataclass, field

import torch

BANDS = ("temporal_low", "temporal_high", "spatial_low", "spatial_high", "region", "all")


@dataclass
class NoiseSpec:
    device: str = "cuda"
    mix: dict | None = None
    raw: dict = field(default_factory=dict)
    used: bool = False  # set once the vision noise was replaced


def parse(extra: dict) -> NoiseSpec | None:
    raw = extra.get("noise")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("noise must be an object, e.g. {\"device\": \"cpu\"}")
    unknown = set(raw) - {"device", "mix"}
    if unknown:
        raise ValueError(f"noise: unknown keys {sorted(unknown)}")
    device = str(raw.get("device", "cuda")).lower()
    if device not in ("cuda", "cpu"):
        raise ValueError("noise.device must be \"cuda\" or \"cpu\"")
    mix = raw.get("mix")
    if mix is not None:
        if not isinstance(mix, dict) or "seed" not in mix:
            raise ValueError("noise.mix needs at least {\"seed\": <int>, \"band\": ...}")
        band = mix.get("band", "all")
        if band not in BANDS:
            raise ValueError(f"noise.mix.band must be one of {BANDS}")
        if band in ("temporal_low", "temporal_high", "spatial_low", "spatial_high"):
            cut = float(mix.get("cut", -1))
            if not 0.0 <= cut <= 1.0:
                raise ValueError("noise.mix.cut must be in [0, 1] (fraction of Nyquist)")
        if band == "region":
            box = mix.get("box")
            if not (isinstance(box, (list, tuple)) and len(box) == 4 and 0 <= box[0] < box[2] <= 1 and 0 <= box[1] < box[3] <= 1):
                raise ValueError("noise.mix.box must be [x0, y0, x1, y1] with 0 <= x0 < x1 <= 1 and 0 <= y0 < y1 <= 1")
        mix = dict(mix, seed=int(mix["seed"]), band=band)
    return NoiseSpec(device=device, mix=mix, raw=raw)


def band_mask(shape: tuple[int, ...], mix: dict) -> torch.Tensor:
    """1 where the noise comes from seed B, broadcastable to (B, C, T, H, W)."""
    _, _, T, H, W = shape
    band = mix["band"]
    if band == "all":
        return torch.ones(1, 1, 1, 1, 1)
    if band == "region":
        x0, y0, x1, y1 = mix["box"]
        m = torch.zeros(1, 1, 1, H, W)
        m[..., int(round(y0 * H)):max(int(round(y1 * H)), int(round(y0 * H)) + 1),
          int(round(x0 * W)):max(int(round(x1 * W)), int(round(x0 * W)) + 1)] = 1
        return m
    limit = float(mix["cut"]) * 0.5
    if band.startswith("temporal"):
        low = (torch.fft.fftfreq(T).abs() <= limit + 1e-9).float().view(1, 1, T, 1, 1)
    else:
        fy, fx = torch.fft.fftfreq(H).view(H, 1), torch.fft.fftfreq(W).view(1, W)
        low = (torch.maximum(fy.abs(), fx.abs()) <= limit + 1e-9).float().view(1, 1, 1, H, W)
    return low if band.endswith("_low") else 1 - low


def mix_noise(a: torch.Tensor, b: torch.Tensor, mix: dict) -> torch.Tensor:
    """Seed B's part of the noise (band or region) on top of seed A's, in float32."""
    mask = band_mask(tuple(a.shape), mix).to(a.device)
    if mask.min() == mask.max():  # an empty or full band: exactly A or exactly B, no FFT rounding
        return (b if mask.max() > 0 else a).float()
    a, b = a.float(), b.float()
    if mix["band"] in ("all", "region"):
        return mask * b + (1 - mask) * a
    dims = (2,) if mix["band"].startswith("temporal") else (3, 4)
    fa, fb = torch.fft.fftn(a, dim=dims), torch.fft.fftn(b, dim=dims)
    return torch.fft.ifftn(mask * fb + (1 - mask) * fa, dim=dims).real


def generator(spec: NoiseSpec | None, seed: int) -> torch.Generator:
    return torch.Generator(device=spec.device if spec else "cuda").manual_seed(int(seed))


@contextlib.contextmanager
def installed(pipe, spec: NoiseSpec | None):
    """Swap the pipeline's vision noise for the mixed one during one call (no-op without a mix)."""
    if spec is None or spec.mix is None:
        yield spec
        return
    module = sys.modules[type(pipe).__module__]
    original = module.randn_tensor

    def randn(shape, generator=None, device=None, dtype=None, **kw):
        if spec.used or len(tuple(shape)) != 5:
            return original(shape, generator=generator, device=device, dtype=dtype, **kw)
        spec.used = True
        a = original(shape, generator=generator, device=device, dtype=dtype, **kw)
        gb = torch.Generator(device=generator.device if generator is not None else spec.device).manual_seed(spec.mix["seed"])
        b = original(shape, generator=gb, device=device, dtype=dtype, **kw)
        return mix_noise(a, b, spec.mix).to(device=a.device, dtype=a.dtype)

    module.randn_tensor = randn
    try:
        yield spec
    finally:
        module.randn_tensor = original
