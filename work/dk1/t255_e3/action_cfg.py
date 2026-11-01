"""Action-contrast guidance for forward-dynamics requests (extra_params.action_cfg). Task 255 E3, dk1.

    "action_cfg": {"scale": 1.0}                              # contrast action = -a (FreeAction, arXiv 2509.24241)
    "action_cfg": {"scale": 1.0, "alt": [[...], ...]}         # contrast action given explicitly (e.g. physical zero, normalised)
    "action_cfg": {"scale": 1.0, "alt": "neg", "steps": [0, 15]}   # guide only denoising steps 0..14 (FreeAction: t > T/2)

Why: in Cosmos3OmniPipeline (diffusers 86ef420b) the CFG uncond pass packs the SAME action tokens as the cond pass, so
stock guidance only contrasts text; nothing ever amplifies the action. With this option the uncond pass is replaced by
"cond text + contrast action a'", and the pipeline's own CFG line gives
    v = v(text, a') + g * (v(text, a) - v(text, a')),   g = 1 + scale
i.e. v(a) + scale * (v(a) - v(a')): FreeAction Eq. 2 with omega = scale (the client picks scale, e.g. lambda*||a||).
Outside `steps` the uncond pass is fed the cond inputs unchanged, so v_uncond == v_cond and the step is unguided.

Restrictions (checked by parse): action_mode forward_dynamics only; the request's guidance_scale must be 1 (text CFG
and action CFG would need a third pass); no internals / latent options in the same request.
"""

from __future__ import annotations

import contextlib
from dataclasses import dataclass, field

import torch


@dataclass
class ActionCfgSpec:
    scale: float
    alt: str | list = "neg"
    steps: tuple[int, int] | None = None
    raw: dict = field(default_factory=dict)
    log: dict = field(default_factory=lambda: dict(guided_steps=[], unguided_steps=[], cond_calls=0, uncond_calls=0))


def parse(extra: dict, guidance_scale: float, num_inference_steps: int) -> ActionCfgSpec | None:
    raw = extra.get("action_cfg")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ValueError("action_cfg must be an object, e.g. {\"scale\": 1.0}")
    unknown = set(raw) - {"scale", "alt", "steps"}
    if unknown:
        raise ValueError(f"action_cfg: unknown keys {sorted(unknown)}")
    if extra.get("action_mode") != "forward_dynamics":
        raise ValueError("action_cfg needs action_mode=forward_dynamics")
    if float(guidance_scale) != 1.0:
        raise ValueError("action_cfg needs guidance_scale=1 (it uses the CFG pass for the action contrast)")
    for k in ("internals", "latent"):
        if k in extra:
            raise ValueError(f"action_cfg cannot be combined with {k}")
    scale = float(raw.get("scale", -1))
    if not 0.0 < scale <= 20.0:
        raise ValueError("action_cfg.scale must be in (0, 20]")
    alt = raw.get("alt", "neg")
    if isinstance(alt, str):
        if alt != "neg":
            raise ValueError("action_cfg.alt must be \"neg\" or a [T, D] list of (normalised) actions")
    elif not (isinstance(alt, list) and alt and all(isinstance(r, list) and r for r in alt)):
        raise ValueError("action_cfg.alt must be \"neg\" or a [T, D] list of (normalised) actions")
    steps = raw.get("steps")
    if steps is not None:
        if not (isinstance(steps, list) and len(steps) == 2 and 0 <= int(steps[0]) < int(steps[1]) <= num_inference_steps):
            raise ValueError(f"action_cfg.steps must be [lo, hi] with 0 <= lo < hi <= {num_inference_steps}")
        steps = (int(steps[0]), int(steps[1]))
    return ActionCfgSpec(scale=scale, alt=alt, steps=steps, raw=raw)


def alt_tokens(spec: ActionCfgSpec, cond_tokens: torch.Tensor, raw_dim: int | None = None) -> torch.Tensor:
    """Contrast action tokens shaped like the cond ones ([chunk, action_dim]); same padding rules as the pipeline:
    shorter sequences repeat the last action, longer ones are truncated, channels are zero-padded to action_dim."""
    if spec.alt == "neg":
        return -cond_tokens
    a = torch.tensor(spec.alt, dtype=torch.float32)
    n, d = cond_tokens.shape
    if raw_dim is not None and a.shape[1] != raw_dim:
        raise ValueError(f"action_cfg.alt width {a.shape[1]} != action width {raw_dim}")
    if a.shape[1] > d:
        raise ValueError(f"action_cfg.alt width {a.shape[1]} > model action_dim {d}")
    if a.shape[0] < n:
        a = torch.cat([a, a[-1:].expand(n - a.shape[0], -1)])
    a = a[:n]
    if a.shape[1] < d:
        a = torch.cat([a, torch.zeros(n, d - a.shape[1])], dim=1)
    return a.to(device=cond_tokens.device, dtype=cond_tokens.dtype)


def _step_index(pipe) -> int:
    t = pipe.current_timestep
    if t is None:
        return -1
    hit = (pipe.scheduler.timesteps == t).nonzero()
    return int(hit[0]) if len(hit) else -1


@contextlib.contextmanager
def installed(pipe, spec: ActionCfgSpec | None, raw_dim: int | None = None):
    """Forward pre-hook on pipe.transformer: per step, remember the cond call's kwargs; rewrite the uncond call to
    those kwargs with the action tokens swapped for the contrast action (or left as-is outside `steps`)."""
    if spec is None:
        yield None
        return
    st = dict(step=None, calls=0, cond=None, alt=None)

    def hook(module, args, kwargs):
        step = _step_index(pipe)
        if step != st["step"]:
            st["step"], st["calls"] = step, 0
        st["calls"] += 1
        if st["calls"] == 1:  # cond pass
            spec.log["cond_calls"] += 1
            st["cond"] = kwargs
            return None
        spec.log["uncond_calls"] += 1
        new = dict(st["cond"])
        guided = spec.steps is None or spec.steps[0] <= step < spec.steps[1]
        if guided:
            toks = st["cond"].get("action_tokens")
            if not toks:
                raise RuntimeError("action_cfg: the cond pass carried no action tokens")
            if st["alt"] is None:
                st["alt"] = alt_tokens(spec, toks[0], raw_dim)
            new["action_tokens"] = [st["alt"]]
            spec.log["guided_steps"].append(step)
        else:
            spec.log["unguided_steps"].append(step)
        return args, new

    h = pipe.transformer.register_forward_pre_hook(hook, with_kwargs=True)
    try:
        yield spec
    finally:
        h.remove()


def summary(spec: ActionCfgSpec | None) -> dict | None:
    if spec is None:
        return None
    lg = spec.log
    return dict(scale=spec.scale, alt="neg" if spec.alt == "neg" else f"explicit[{len(spec.alt)}x{len(spec.alt[0])}]",
                steps=list(spec.steps) if spec.steps else None, effective_guidance_scale=1.0 + spec.scale,
                cond_calls=lg["cond_calls"], uncond_calls=lg["uncond_calls"],
                guided_steps=sorted(set(lg["guided_steps"])), unguided_steps=sorted(set(lg["unguided_steps"])))
