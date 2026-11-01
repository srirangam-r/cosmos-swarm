"""Latent-space control for Cosmos3-Nano generation (extra_params.latent). Each option implements a published method.

    "latent": {"ref": "proxy.mp4",            # uploaded in internals_files; encoded with Nano's own VAE -> x0_ref
               "start_step": 7,               # start sampling at step k of the 35 (SDEdit; ProxyUp t_init)
               "init": "noised",              # x_k = (1-s_k) x0_ref + s_k eps   (SDEdit, arXiv 2108.01073)
               "invert_substeps": 1,          # inversion only: split each sigma interval into n (more accurate)
                       | "inverted",          # x_k = ODE inversion of x0_ref up to s_k (ProxyUp 2607.03732), 2nd-order
                                              #       midpoint solver (RF-Solver 2411.04746), CFG 1 during inversion
               "start_file": "z.npz",          # instead: start from an uploaded latent (npz with x_inverted/x_start)
               "band": {"band": "temporal_low", "cut": 0.25} | {"band": "region", "box": [...]},
                                              # keep only this band/region of x_k, the rest is fresh noise at the same
                                              # level (FreeInit 2312.07537; ProxyUp region-wise latent noising)
               "sfr": 15, "sfr_guidance": 3.0, # ProxyUp's stochastic flow relaxation at s_k (K rounds)
               "x0_inject": {"steps": [0, 10], "box": [x0, y0, x1, y1]} | {"steps": [0, 10], "mask": "m.npy"},
                                              # in those steps, the predicted clean video inside the box/mask is
                                              # replaced by x0_ref (PhyRPR 2601.09255 latent fusion)
               "return": ["x_start", "x_inverted", "x0_ref"]}   # saved as one artifact (npz)

Notes
- Shapes: x0_ref is [1, C, T', H', W'] = [1, 48, (frames-1)/4+1, H/16, W/16]. Latent frame 0 is the conditioning frame in
  I2V; it is never overwritten (the pipeline's condition mask keeps it clean).
- The reference video must have the request's size and frame count (it is resized and padded/trimmed to match).
- With start_step k, internals step ranges (prompt_switch, steer, ...) count from the start step.
- Sigmas are the request's own schedule (Karras flow sigmas of the 35-step UniPC); s_k = sigmas[k]. The sidecar records them.
- "init": "inverted" with start_step 0 and no band reconstructs the reference (up to inversion error): the first test to run.
"""

from __future__ import annotations

import contextlib
import io
import sys
from dataclasses import dataclass, field

import numpy as np
import torch

import noise as noise_mod

INITS = ("noised", "inverted")
RETURNS = ("x_start", "x_inverted", "x0_ref")


@dataclass
class LatentSpec:
    ref: str | None = None
    start_file: str | None = None
    start_step: int = 0
    init: str = "noised"
    band: dict | None = None
    sfr: int = 0
    sfr_guidance: float | None = None
    invert_substeps: int = 1
    x0_inject: dict | None = None
    returns: list = field(default_factory=list)
    raw: dict = field(default_factory=dict)
    summary: dict = field(default_factory=dict)


def parse(extra: dict, uploads: dict, num_inference_steps: int) -> LatentSpec | None:
    raw = extra.get("latent")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("latent must be an object")
    unknown = set(raw) - {"ref", "start_file", "start_step", "init", "invert_substeps", "band", "sfr", "sfr_guidance", "x0_inject", "return"}
    if unknown:
        raise ValueError(f"latent: unknown keys {sorted(unknown)}")
    s = LatentSpec(raw=raw)
    s.ref = raw.get("ref")
    if s.ref is not None and s.ref not in uploads:
        raise ValueError(f"latent.ref {s.ref!r} is not among the uploaded internals_files {sorted(uploads)}")
    s.start_file = raw.get("start_file")
    if s.start_file is not None and s.start_file not in uploads:
        raise ValueError(f"latent.start_file {s.start_file!r} is not uploaded")
    s.start_step = int(raw.get("start_step", 0))
    if not 0 <= s.start_step < num_inference_steps:
        raise ValueError(f"latent.start_step must be in [0, {num_inference_steps})")
    s.init = str(raw.get("init", "noised"))
    if s.init not in INITS:
        raise ValueError(f"latent.init must be one of {INITS}")
    if raw.get("band") is not None:
        s.band = noise_mod.parse({"noise": {"mix": {"seed": 0, **raw["band"]}}}).mix  # same validation as noise.mix
    s.invert_substeps = int(raw.get("invert_substeps", 1))
    if not 1 <= s.invert_substeps <= 8:
        raise ValueError("latent.invert_substeps must be in [1, 8]")
    s.sfr = int(raw.get("sfr", 0))
    if not 0 <= s.sfr <= 50:
        raise ValueError("latent.sfr must be in [0, 50]")
    s.sfr_guidance = float(raw["sfr_guidance"]) if raw.get("sfr_guidance") is not None else None
    if raw.get("x0_inject") is not None:
        inj = dict(raw["x0_inject"])
        a, b = (int(v) for v in inj.get("steps", [0, num_inference_steps]))
        if not 0 <= a < b <= num_inference_steps:
            raise ValueError("latent.x0_inject.steps must be [a, b) within the schedule")
        if "mask" in inj:
            if inj["mask"] not in uploads:
                raise ValueError(f"latent.x0_inject.mask {inj['mask']!r} is not uploaded")
        elif "box" in inj:
            noise_mod.parse({"noise": {"mix": {"seed": 0, "band": "region", "box": inj["box"]}}})
        else:
            raise ValueError("latent.x0_inject needs a box or a mask")
        inj["steps"] = [a, b]
        s.x0_inject = inj
    s.returns = list(raw.get("return", []))
    if set(s.returns) - set(RETURNS):
        raise ValueError(f"latent.return entries must be among {RETURNS}")
    needs_ref = s.x0_inject is not None or (s.start_file is None and (
        s.init == "inverted" or s.start_step > 0 or s.band is not None or s.sfr > 0))
    if needs_ref and s.ref is None:
        raise ValueError("latent: this option needs a reference video (latent.ref)")
    return s


# ---------------------------------------------------------------- reference video

def encode_ref(pipe, data: bytes, num_frames: int, width: int, height: int) -> torch.Tensor:
    """Video bytes -> Nano's normalized latent [1, C, T', H', W'] (float32, on the pipeline's device)."""
    import av
    frames = [f.to_ndarray(format="rgb24") for f in av.open(io.BytesIO(data)).decode(video=0)]
    if not frames:
        raise ValueError("latent.ref: no frames decoded")
    frames = (frames + [frames[-1]] * num_frames)[:num_frames]
    x = torch.tensor(np.stack(frames)).permute(3, 0, 1, 2).float() / 127.5 - 1  # C T H W in [-1, 1]
    if x.shape[2:] != (height, width):
        x = torch.nn.functional.interpolate(x, size=(height, width), mode="bilinear", align_corners=False)
    dev = next(pipe.transformer.parameters()).device if not hasattr(pipe, "_execution_device") else pipe._execution_device
    with torch.no_grad():
        return pipe._encode_video(x.unsqueeze(0).to(dev)).float()


def region_mask(shape, inj: dict, uploads: dict) -> torch.Tensor:
    """[1, 1, T', H', W'] float mask (1 = inject), never on latent frame 0."""
    _, _, T, H, W = shape
    if "mask" in inj:
        m = torch.tensor(np.load(io.BytesIO(uploads[inj["mask"]]))).float()
        m = m.expand(T, H, W) if m.dim() == 2 else m
        if tuple(m.shape) != (T, H, W):
            raise ValueError(f"latent.x0_inject.mask must be [{H},{W}] or [{T},{H},{W}], got {tuple(m.shape)}")
        m = m.view(1, 1, T, H, W).clone()
    else:
        m = noise_mod.band_mask(shape, {"band": "region", "box": inj["box"]}).expand(1, 1, T, H, W).clone()
    m[:, :, 0] = 0
    return m


# ---------------------------------------------------------------- schedules

def sigma_list(sched_cls, base_config: dict, flow_shift: float, steps: int) -> list[float]:
    s = sched_cls.from_config(base_config, flow_shift=float(flow_shift))
    s.set_timesteps(steps)
    return [float(x) for x in s.sigmas]  # steps + 1 values, last 0


def start_at_scheduler(sched_cls, base_config: dict, flow_shift: float, start: int, x0_ref=None, mask=None,
                       inject_steps=None):
    """The request's UniPC scheduler, sliced to start at step `start`, optionally fusing x0_ref into the predicted
    clean video inside `mask` during `inject_steps` (absolute step indices)."""

    class StartAt(sched_cls):
        def set_timesteps(self, *a, **kw):
            super().set_timesteps(*a, **kw)
            if start:
                self.timesteps = self.timesteps[start:]
                self.sigmas = self.sigmas[start:]
                self.num_inference_steps = len(self.timesteps)

        def convert_model_output(self, model_output, *args, sample=None, **kwargs):
            x0 = super().convert_model_output(model_output, *args, sample=sample, **kwargs)
            if x0_ref is not None and inject_steps is not None and self.step_index is not None:
                step = start + int(self.step_index)
                if inject_steps[0] <= step < inject_steps[1]:
                    ref = x0_ref.to(x0.device, x0.dtype).reshape(x0.shape)
                    m = mask.to(x0.device, x0.dtype).reshape((1,) * (x0.dim() - 4) + tuple(mask.shape[1:]))
                    x0 = m * ref + (1 - m) * x0
            return x0

    return StartAt.from_config(base_config, flow_shift=float(flow_shift))


class _ListScheduler:
    """Minimal scheduler for auxiliary passes: the pipeline asks for timesteps, calls step(v, t, x) at each one.
    `timesteps` are sigma * 1000, as in the request's UniPC (flow sigmas, num_train_timesteps 1000)."""
    order = 1
    init_noise_sigma = 1.0

    def __init__(self, base_config: dict, sigmas_eval: list[float]):
        self.config = base_config
        self._sig = sigmas_eval
        self.timesteps = None
        self.sigmas = None

    def set_timesteps(self, num_inference_steps=None, device=None, sigmas=None, **kw):
        self.timesteps = torch.tensor([s * 1000.0 for s in self._sig], dtype=torch.float32, device=device)
        self.sigmas = torch.tensor(self._sig + [0.0], dtype=torch.float32)
        self._i = 0

    def scale_model_input(self, sample, *a, **kw):
        return sample


class InvertMidpoint(_ListScheduler):
    """Deterministic ODE inversion x(s) from s=0 up to s_target with the midpoint method (2nd order).
    Flow convention of Nano's UniPC: x_s = (1-s) x0 + s eps, model output v = eps - x0 = dx/ds.
    Evaluation points alternate [s_i, mid_i]: at s_i store x_i and take a half step; at mid_i take the full step."""

    def __init__(self, base_config: dict, grid: list[float]):
        evals = []
        for a, b in zip(grid[:-1], grid[1:]):
            evals += [a, 0.5 * (a + b)]
        super().__init__(base_config, evals)
        self._grid = grid

    def step(self, model_output, timestep, sample, return_dict=False, **kw):
        k, stage = divmod(self._i, 2)
        a, b = self._grid[k], self._grid[k + 1]
        if stage == 0:
            self._x = sample
            out = sample + 0.5 * (b - a) * model_output
        else:
            out = self._x + (b - a) * model_output
        self._i += 1
        return (out,)


class Renoise(_ListScheduler):
    """One ProxyUp SFR round at sigma s: x0_hat = x - s v; x' = (1-s) x0_hat + s eps_new."""

    def __init__(self, base_config: dict, s: float, eps: torch.Tensor):
        super().__init__(base_config, [s])
        self._s, self._eps = s, eps

    def step(self, model_output, timestep, sample, return_dict=False, **kw):
        x0 = sample - self._s * model_output
        return ((1 - self._s) * x0 + self._s * self._eps.to(sample.device, sample.dtype).reshape(sample.shape),)


@contextlib.contextmanager
def vision_noise(pipe, tensor: torch.Tensor):
    """Replace the pipeline's first 5-D randn_tensor call (the vision noise) with `tensor` during one call.
    The pipeline then forms latents = cond_mask * x0_cond + (1 - cond_mask) * tensor, so latent frame 0 stays the
    conditioning frame in I2V."""
    module = sys.modules[type(pipe).__module__]
    original = module.randn_tensor
    used = []

    def randn(shape, generator=None, device=None, dtype=None, **kw):
        if used or len(tuple(shape)) != 5:
            return original(shape, generator=generator, device=device, dtype=dtype, **kw)
        used.append(True)
        if tuple(tensor.shape) != tuple(shape):
            raise ValueError(f"latent: tensor shape {tuple(tensor.shape)} does not match the vision noise {tuple(shape)}")
        return tensor.to(device=device, dtype=dtype)

    module.randn_tensor = randn
    try:
        yield
    finally:
        module.randn_tensor = original


def _aux_latents(res) -> torch.Tensor:
    v = res.video if hasattr(res, "video") else res[0]
    v = v[0] if isinstance(v, (list, tuple)) else v
    return v.float().unsqueeze(0) if v.dim() == 4 else v.float()


def randn_like_seed(shape, seed: int, device) -> torch.Tensor:
    return torch.randn(shape, generator=torch.Generator().manual_seed(int(seed)), dtype=torch.float32).to(device)


def build_start(pipe, call: dict, spec: LatentSpec, x0_ref, sig: list[float], seed: int,
                make_generator, neg_ctx, uploads: dict | None = None, shape=None) -> tuple[torch.Tensor, dict]:
    """The latent state at s_k the main pass starts from, plus what was done (for the sidecar and artifacts)."""
    uploads = uploads or {}
    dev = x0_ref.device if x0_ref is not None else torch.device("cuda")
    shape = tuple(x0_ref.shape) if x0_ref is not None else shape
    k = spec.start_step
    s_k = sig[k]
    out = {}
    if spec.start_file is not None:  # a latent computed elsewhere (e.g. another clip's x_inverted artifact)
        z = np.load(io.BytesIO(uploads[spec.start_file]))
        arr = z[z.files[0]] if hasattr(z, "files") else z
        arr = next((z[k] for k in ("x_inverted", "x_start") if hasattr(z, "files") and k in z.files), arr)
        x_k = torch.tensor(np.asarray(arr, dtype=np.float32)).to(dev)
        spec.summary["start_file"] = spec.start_file
    elif spec.init == "inverted":
        coarse = [0.0] + sorted(s for s in sig[k:-1])  # ascending: 0 -> ... -> s_k, the request's own sigma grid
        n = spec.invert_substeps  # each interval split into n (finer grid = smaller inversion error, n x the cost)
        grid = [a + (b - a) * j / n for a, b in zip(coarse[:-1], coarse[1:]) for j in range(n)] + [coarse[-1]]
        aux = dict(call, generator=make_generator(), guidance_scale=1.0, num_inference_steps=2 * (len(grid) - 1),
                   output_type="latent")
        saved = pipe.scheduler
        pipe.scheduler = InvertMidpoint(saved.config, grid)
        try:
            with neg_ctx(), vision_noise(pipe, x0_ref.to(torch.float32)):
                x_k = _aux_latents(pipe(**aux))
        finally:
            pipe.scheduler = saved
        out["x_inverted"] = x_k
        spec.summary["inversion"] = dict(solver="midpoint", grid=[round(g, 5) for g in grid], model_evals=2 * (len(grid) - 1))
    else:
        x_k = (1 - s_k) * x0_ref + s_k * randn_like_seed(shape, seed, dev)
    if spec.band is not None:
        fill = randn_like_seed(shape, seed + 7777, dev) * float(np.sqrt((1 - s_k) ** 2 + s_k ** 2))
        x_k = noise_mod.mix_noise(fill, x_k, spec.band).to(dev)  # the band from x_k, the rest fresh
    for r in range(spec.sfr):
        aux = dict(call, generator=make_generator(), num_inference_steps=1, output_type="latent")
        if spec.sfr_guidance is not None:
            aux["guidance_scale"] = spec.sfr_guidance
        saved = pipe.scheduler
        pipe.scheduler = Renoise(saved.config, s_k, randn_like_seed(shape, seed * 1000 + r + 1, dev))
        try:
            with neg_ctx(), vision_noise(pipe, x_k):
                x_k = _aux_latents(pipe(**aux))
        finally:
            pipe.scheduler = saved
    spec.summary.update(start_step=k, sigma_start=round(s_k, 5), init=spec.init, band=spec.band, sfr=spec.sfr)
    out["x_start"] = x_k
    return x_k, out
