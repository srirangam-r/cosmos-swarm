"""Per-request "internals" hooks for the Cosmos3-Nano server (diffusers Cosmos3OmniPipeline @86ef420b).

Everything here is opt-in through `extra_params.internals`; a request without it never touches this module.
`parse()` validates the spec up front (-> InternalsError, which server.py turns into an HTTP 400), `installed()` is a
context manager that installs forward hooks / one function swap around `pipe(**call)` and removes every one of them
on exit, including when the request fails. See README.md for the JSON shapes.

What the real source says (checked in diffusers 86ef420b):
  * `Cosmos3OmniTransformer.layers` is a ModuleList of `Cosmos3VLTextMoTDecoderLayer`; each returns `(und_seq, gen_seq)`.
    Video tokens live in `gen_seq`: the first `T*S` rows of it (T latent frames, S = patch_h*patch_w tokens per frame, row
    order t, h, w), because `vision_sequence_indexes` starts at `und_len`. Sound/action tokens, if any, come after.
  * The transformer is called with keyword arguments only (`und_len`, `vision_token_shapes`, `vision_noisy_frame_indexes`,
    `vision_tokens` ...), once per CFG branch: cond first, uncond second, every denoising step.
  * The conditioning frame is a *clean latent* inside `vision_tokens` (pipeline `prepare_latents`: mask frame 0 for I2V),
    its tokens get NO timestep embedding (only `vision_noisy_frame_indexes` frames do) and its velocity is masked to 0.
    So "noisy frames" = frames in `vision_noisy_frame_indexes[0]`, conditioning frames = all the others.
  * Temporal RoPE: `transformer.rotary_emb.inv_freq` (64 fp32 entries); interleaved mrope puts H on j=1,4,..58, W on
    j=2,5,..59 and T on everything else (j%3==0 for j<60, plus 60..63).
"""
import contextlib, functools, hashlib, io, json, math, re, secrets, types
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
import diffusers.models.transformers.transformer_cosmos3 as _tc


class InternalsError(ValueError):
    """A bad `internals` spec; the server answers 400 with this message."""


ARTIFACT_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
KEYS = {"rope", "conditioning", "capture", "steer", "prompt_switch"}
PASSES = ("cond", "uncond")


# ----------------------------------------------------------------------------- artifacts
class ArtifactStore:
    """npz files in one directory, addressed by id (`act_<8 hex>`). ids are validated, so no path traversal."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def new_id(self) -> str:
        return "act_" + secrets.token_hex(4)

    def path(self, artifact_id: str):
        if not ARTIFACT_RE.match(artifact_id or ""):
            return None
        p = self.root / f"{artifact_id}.npz"
        return p if p.is_file() else None

    def save(self, artifact_id: str, arrays: dict, meta: dict) -> Path:
        p = self.root / f"{artifact_id}.npz"
        tmp = self.root / f"{artifact_id}.tmp"
        with open(tmp, "wb") as f:
            np.savez(f, _meta=np.array(json.dumps(meta)), **arrays)
        tmp.replace(p)
        return p


@dataclass
class Env:
    """What parse() needs to know about the request and model."""
    num_layers: int
    hidden_size: int
    num_steps: int
    latent_frames: int  # T of the latent video: (num_frames - 1) // 4 + 1
    artifacts: ArtifactStore
    uploads: dict = field(default_factory=dict)  # filename -> bytes (multipart field internals_files)
    max_capture_bytes: int = 1 << 30
    temporal: list = None  # inv_freq indexes that carry the temporal axis: temporal_indices(transformer.rotary_emb)


@dataclass
class Spec:
    raw: dict  # what goes in the sidecar (vector payloads replaced by shape + sha256)
    rope: dict | None = None  # {j: multiplier}
    cond_noise: dict | None = None  # level, seed, range
    cond_attn: dict | None = None  # factor, range, layers
    capture: dict | None = None  # layers, range, every, passes, full
    steer: dict | None = None  # alpha, range, passes, profile, include_cond, vectors {layer: tensor}
    prompt_switch: dict | None = None  # prompt, range; server.py adds "pack" (capture_text_pack) before the run


# ----------------------------------------------------------------------------- parsing
def _num(x, name, lo=None, hi=None):
    if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x):
        raise InternalsError(f"{name} must be a finite number, got {x!r}")
    if (lo is not None and x < lo) or (hi is not None and x > hi):
        raise InternalsError(f"{name}={x} is outside [{lo}, {hi}]")
    return float(x)


def _unknown(d, allowed, where):
    extra = set(d) - set(allowed)
    if extra:
        raise InternalsError(f"unknown key(s) {sorted(extra)} in {where}; allowed: {sorted(allowed)}")


def _obj(d, where):
    if not isinstance(d, dict):
        raise InternalsError(f"{where} must be a JSON object")
    return d


def _step_range(v, env, where):
    """None -> all steps. [start, end) with 0 <= start < end <= num_inference_steps."""
    if v is None:
        return (0, env.num_steps)
    if not (isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(i, int) and not isinstance(i, bool) for i in v)):
        raise InternalsError(f"{where}.step_range must be [start, end) integers, got {v!r}")
    if not 0 <= v[0] < v[1] <= env.num_steps:
        raise InternalsError(f"{where}.step_range {list(v)} must satisfy 0 <= start < end <= num_inference_steps ({env.num_steps})")
    return (v[0], v[1])


def _layers(v, env, where, default_all=False):
    if v is None and default_all:
        return list(range(env.num_layers))
    if v == "all":
        return list(range(env.num_layers))
    if not (isinstance(v, list) and v and all(isinstance(i, int) and not isinstance(i, bool) for i in v)):
        raise InternalsError(f"{where}.layers must be a non-empty list of block indexes (or \"all\"), got {v!r}")
    bad = [i for i in v if not 0 <= i < env.num_layers]
    if bad:
        raise InternalsError(f"{where}.layers {bad} out of range: the transformer has {env.num_layers} blocks (0..{env.num_layers - 1})")
    return sorted(set(v))


def _passes(v, where, default):
    if v is None:
        return tuple(default)
    if v == "both":
        return PASSES
    if v in PASSES:
        return (v,)
    if isinstance(v, list) and v and all(p in PASSES for p in v):
        return tuple(dict.fromkeys(v))
    raise InternalsError(f"{where}.passes must be \"cond\", \"uncond\", \"both\" or a list of those, got {v!r}")


def temporal_indices(rotary_emb) -> list:
    """j of the inv_freq entries that rotate by the temporal position (see module docstring)."""
    n = rotary_emb.inv_freq.numel()
    h = set(range(1, rotary_emb.rope_axes_dim[1] * 3, 3))
    w = set(range(2, rotary_emb.rope_axes_dim[2] * 3, 3))
    return [j for j in range(n) if j not in h and j not in w]


def _parse_rope(v, env, temporal):
    v = _obj(v, "rope")
    _unknown(v, {"temporal_scale"}, "rope")
    s = v.get("temporal_scale")
    if isinstance(s, (int, float)) and not isinstance(s, bool):
        return {j: _num(s, "rope.temporal_scale", 1e-3, 1e3) for j in temporal}
    s = _obj(s, "rope.temporal_scale (a number, or an object {inv_freq index: multiplier})")
    out = {}
    for k, m in s.items():
        try:
            j = int(k)
        except ValueError:
            raise InternalsError(f"rope.temporal_scale key {k!r} is not an inv_freq index")
        if j not in temporal:
            raise InternalsError(f"rope.temporal_scale index {j} is not a temporal entry; temporal indexes are {temporal}")
        out[j] = _num(m, f"rope.temporal_scale[{k}]", 1e-3, 1e3)
    if not out:
        raise InternalsError("rope.temporal_scale is empty")
    return out


def _parse_conditioning(v, env):
    v = _obj(v, "conditioning")
    _unknown(v, {"noise", "attention_scale"}, "conditioning")
    noise = attn = None
    if "noise" in v:
        n = _obj(v["noise"], "conditioning.noise")
        _unknown(n, {"level", "seed", "step_range"}, "conditioning.noise")
        if "level" not in n:
            raise InternalsError("conditioning.noise.level is required (0..1; x = (1-level)*x_cond + level*eps)")
        noise = dict(level=_num(n["level"], "conditioning.noise.level", 0.0, 1.0), seed=int(n.get("seed", 0)),
                     range=_step_range(n.get("step_range"), env, "conditioning.noise"))
    if "attention_scale" in v:
        a = _obj(v["attention_scale"], "conditioning.attention_scale")
        _unknown(a, {"factor", "step_range", "layers"}, "conditioning.attention_scale")
        if "factor" not in a:
            raise InternalsError("conditioning.attention_scale.factor is required (>= 0; 1.0 = no change)")
        attn = dict(factor=_num(a["factor"], "conditioning.attention_scale.factor", 0.0, 1e3),
                    range=_step_range(a.get("step_range"), env, "conditioning.attention_scale"),
                    layers=_layers(a.get("layers"), env, "conditioning.attention_scale", default_all=True))
    if noise is None and attn is None:
        raise InternalsError("conditioning needs \"noise\" and/or \"attention_scale\"")
    return noise, attn


def _parse_capture(v, env):
    v = _obj(v, "capture")
    _unknown(v, {"layers", "step_range", "every", "passes", "full"}, "capture")
    layers = _layers(v.get("layers"), env, "capture")
    rng = _step_range(v.get("step_range"), env, "capture")
    every = v.get("every", 1)
    if not isinstance(every, int) or isinstance(every, bool) or every < 1:
        raise InternalsError(f"capture.every must be a positive integer, got {every!r}")
    passes = _passes(v.get("passes"), "capture", ("cond",))
    full = bool(v.get("full", False))
    n_steps = len(range(rng[0], rng[1], every))
    per = env.latent_frames * env.hidden_size * 4  # per-frame means, float32
    if full:  # float16 [T, S, D]; S is unknown here, so bound it by the largest sensible grid (1280x720 -> 45x80 = 3600)
        per += env.latent_frames * 3600 * env.hidden_size * 2
    est = n_steps * len(passes) * len(layers) * per
    if est > env.max_capture_bytes:
        raise InternalsError(f"capture would hold ~{est / 2**20:.0f} MiB (limit {env.max_capture_bytes / 2**20:.0f} MiB); "
                             f"use fewer layers/steps (step_range, every), passes=[\"cond\"], or full=false")
    return dict(layers=layers, range=rng, every=every, passes=passes, full=full)


def _load_array(entry, env, where):
    if "artifact" in entry:
        path = env.artifacts.path(str(entry["artifact"]))
        if path is None:
            raise InternalsError(f"{where}: no artifact with id {entry['artifact']!r}")
        z = np.load(path, allow_pickle=False)
        names = [k for k in z.files if k != "_meta"]
        src = f"artifact {entry['artifact']}"
    elif "file" in entry:
        raw = env.uploads.get(str(entry["file"]))
        if raw is None:
            raise InternalsError(f"{where}: no uploaded file named {entry['file']!r} (upload it in the multipart field "
                                 f"internals_files; uploaded: {sorted(env.uploads)})")
        try:
            z = np.load(io.BytesIO(raw), allow_pickle=False)
        except Exception as e:
            raise InternalsError(f"{where}: {entry['file']!r} is not a readable .npy/.npz ({type(e).__name__}: {e})")
        names = [k for k in getattr(z, "files", [])]
        src = f"file {entry['file']}"
    elif "values" in entry:  # inline JSON numbers: the only option through the job queue besides artifact ids
        try:
            return np.asarray(entry["values"], dtype=np.float32), "inline values"
        except (ValueError, TypeError) as e:
            raise InternalsError(f"{where}: \"values\" must be a (nested) list of numbers ({e})")
    else:
        raise InternalsError(f"{where}: give \"artifact\" (capture id + key), \"file\" (uploaded .npy/.npz name) or \"values\" (inline list)")
    if isinstance(z, np.ndarray):  # .npy
        return z, src
    key = entry.get("key")
    if key is None and len(names) == 1:
        key = names[0]
    if key not in names:
        raise InternalsError(f"{where}: {src} needs \"key\" naming one array; it has {names[:8]}{' ...' if len(names) > 8 else ''}")
    return z[key], f"{src}[{key}]"


def _parse_steer(v, env):
    v = _obj(v, "steer")
    _unknown(v, {"alpha", "vectors", "step_range", "passes", "frame_profile", "include_conditioning_frames"}, "steer")
    alpha = _num(v.get("alpha"), "steer.alpha", -1e4, 1e4) if "alpha" in v else None
    if alpha is None:
        raise InternalsError("steer.alpha is required")
    entries = v.get("vectors")
    if not (isinstance(entries, list) and entries):
        raise InternalsError("steer.vectors must be a non-empty list of {layer, artifact|file, key?, average_frames?}")
    T, D = env.latent_frames, env.hidden_size
    vectors, described = {}, []
    for i, e in enumerate(entries):
        where = f"steer.vectors[{i}]"
        e = _obj(e, where)
        _unknown(e, {"layer", "artifact", "file", "key", "average_frames", "values"}, where)
        layer = _layers([e.get("layer")], env, where)[0]
        if layer in vectors:
            raise InternalsError(f"{where}: layer {layer} appears twice")
        arr, src = _load_array(e, env, where)
        arr = np.asarray(arr)
        if not np.issubdtype(arr.dtype, np.floating):
            raise InternalsError(f"{where}: {src} has dtype {arr.dtype}, expected a float array")
        arr = arr.astype(np.float32)
        if e.get("average_frames") and arr.ndim == 2:
            arr = arr.mean(0)
        if arr.ndim == 1 and arr.shape[0] != D or arr.ndim == 2 and arr.shape != (T, D) or arr.ndim not in (1, 2):
            raise InternalsError(
                f"{where}: {src} has shape {list(arr.shape)}; expected [{D}] (one vector for every frame) or [{T}, {D}] "
                f"(one per latent frame; this request has {T} latent frames = (num_frames-1)//4+1, hidden_size {D}). "
                f"A captured 'full' array [T,S,D] must be averaged over S first; a [T,D] capture can use average_frames=true.")
        if not np.isfinite(arr).all():
            raise InternalsError(f"{where}: {src} contains NaN/inf")
        vectors[layer] = torch.from_numpy(np.ascontiguousarray(arr))
        described.append({**e, "resolved": dict(source=src, shape=list(arr.shape), norm=float(np.linalg.norm(arr)),
                                                sha256=hashlib.sha256(arr.tobytes()).hexdigest()[:16])})
    profile = v.get("frame_profile")
    if profile is not None:
        if not (isinstance(profile, list) and len(profile) == T):
            raise InternalsError(f"steer.frame_profile must be a list of {T} numbers (one per latent frame, "
                                 f"T=(num_frames-1)//4+1), got {len(profile) if isinstance(profile, list) else profile!r}")
        profile = [_num(p, "steer.frame_profile[]") for p in profile]
    steer = dict(alpha=alpha, range=_step_range(v.get("step_range"), env, "steer"), passes=_passes(v.get("passes"), "steer", PASSES),
                 profile=profile, include_cond=bool(v.get("include_conditioning_frames", False)), vectors=vectors)
    return steer, {**v, "vectors": described}


def _parse_prompt_switch(v, env):
    v = _obj(v, "prompt_switch")
    _unknown(v, {"prompt", "step_range"}, "prompt_switch")
    p = v.get("prompt")
    if not isinstance(p, str) or not p.strip():
        raise InternalsError("prompt_switch.prompt must be a non-empty string (the prompt the conditional pass gets)")
    if len(p) > 8000:
        raise InternalsError("prompt_switch.prompt is longer than 8000 characters")
    return dict(prompt=p, range=_step_range(v.get("step_range"), env, "prompt_switch"))


def parse(raw, env: Env) -> Spec:
    """Validate `extra_params.internals`. Raises InternalsError (-> 400). No GPU, no model."""
    raw = _obj(raw, "internals")
    _unknown(raw, KEYS, "internals")
    spec = Spec(raw=json.loads(json.dumps(raw)))
    if "rope" in raw:
        spec.rope = _parse_rope(raw["rope"], env, env.temporal)
    if "conditioning" in raw:
        spec.cond_noise, spec.cond_attn = _parse_conditioning(raw["conditioning"], env)
    if "capture" in raw:
        spec.capture = _parse_capture(raw["capture"], env)
    if "steer" in raw:
        spec.steer, spec.raw["steer"] = _parse_steer(raw["steer"], env)
    if "prompt_switch" in raw:
        spec.prompt_switch = _parse_prompt_switch(raw["prompt_switch"], env)
    if not any((spec.rope, spec.cond_noise, spec.cond_attn, spec.capture, spec.steer, spec.prompt_switch)):
        raise InternalsError("internals is empty; give one of " + ", ".join(sorted(KEYS)))
    return spec


# ----------------------------------------------------------------------------- prompt switch
# The transformer inputs that carry the packed text, and the sequence layout that depends on its length
# (ro-1's server_prompt_switch.py, work/ro-1/switch_probe). The noisy latents (vision_tokens) are not among them.
TEXT_PACK_KEYS = ("input_ids", "text_indexes", "position_ids", "und_len", "sequence_length", "vision_token_shapes",
                  "vision_sequence_indexes", "vision_mse_loss_indexes", "vision_noisy_frame_indexes")


class _PackCaptured(Exception):
    pass


def capture_text_pack(pipe, call: dict, prompt: str) -> dict:
    """The conditional pass's packed text inputs for `prompt`: run the pipeline for one step with the same call and
    stop at the first transformer call (the conditional pass of step 0). Install no other hooks while this runs."""
    box = {}

    def grab(module, args, kwargs):
        box.update({k: kwargs[k] for k in TEXT_PACK_KEYS if k in kwargs})
        raise _PackCaptured()

    gen = call.get("generator")
    dry = {**call, "prompt": prompt, "num_inference_steps": 1,
           "generator": torch.Generator(device=gen.device if gen is not None else "cpu").manual_seed(0)}
    h = pipe.transformer.register_forward_pre_hook(grab, with_kwargs=True)
    try:
        pipe(**dry)
    except _PackCaptured:
        pass
    finally:
        h.remove()
    missing = [k for k in ("input_ids", "und_len", "sequence_length") if k not in box]
    if missing:
        raise RuntimeError(f"prompt_switch: the dry run did not reach the transformer with {missing}; diffusers changed?")
    return box


# ----------------------------------------------------------------------------- hooks
class _State:
    """Shared by this request's hooks; rebuilt per request."""
    step = -1
    calls = 0  # transformer calls seen in this step (0 = cond branch, 1 = uncond)
    pass_name = "cond"
    und_len = T = S = 0
    ph = pw = 0
    cond_frames = ()
    attn_on = False


def _step_index(pipe) -> int:
    t = pipe.current_timestep  # public property of Cosmos3OmniPipeline, None outside the denoising loop
    if t is None:
        return -1
    hit = (pipe.scheduler.timesteps == t).nonzero()
    return int(hit[0]) if len(hit) else -1


def _in(step, rng):
    return rng[0] <= step < rng[1]


def _rope_forward(rot, mults):
    """Replacement for rotary_emb.forward that runs the ORIGINAL class forward on a shim holding scaled frequencies.

    The buffer itself is never written: with group offload the buffer is re-copied from a CPU stash on every onload,
    so an in-place edit (what poornima-1's gen92.py did, with no offload) would silently be lost."""
    base = rot.inv_freq.detach().float().cpu().clone()
    scale = torch.ones_like(base)
    for j, m in mults.items():
        scale[j] = m
    scaled = base * scale
    cls_forward = type(rot).forward

    def forward(position_ids, device, dtype):
        shim = types.SimpleNamespace(inv_freq=scaled.to(device), rope_axes_dim=rot.rope_axes_dim,
                                     apply_interleaved_mrope=rot.apply_interleaved_mrope)
        return cls_forward(shim, position_ids, device, dtype)

    return forward


@contextlib.contextmanager
def rope_scaled(transformer, mults: dict):
    """Temporarily scale temporal inv_freq entries: {j: multiplier}. Restores the module exactly."""
    rot = transformer.rotary_emb
    had = "forward" in rot.__dict__
    prev = rot.__dict__.get("forward")  # group offload may have put its own wrapper here
    rot.forward = _rope_forward(rot, mults)
    try:
        yield
    finally:
        if had:
            rot.forward = prev
        else:
            rot.__dict__.pop("forward", None)


class Recorder:
    """What the hooks saw; server.py turns it into the artifact + sidecar summary."""

    def __init__(self):
        self.arrays = {}
        self.meta = {}
        self.steered = []  # (step, pass, layer) triples
        self.attn_steps = set()
        self.noise_steps = set()
        self.switch_steps = set()

    def summary(self):
        out = {}
        if self.arrays:
            out["capture"] = dict(n_arrays=len(self.arrays), keys_example=sorted(self.arrays)[:3],
                                  mib=round(sum(a.nbytes for a in self.arrays.values()) / 2**20, 2), **self.meta)
        if self.steered:
            out["steer_applied"] = dict(n_block_calls=len(self.steered), steps=sorted({s for s, _, _ in self.steered}))
        if self.attn_steps:
            out["attention_scale_steps"] = sorted(self.attn_steps)
        if self.noise_steps:
            out["conditioning_noise_steps"] = sorted(self.noise_steps)
        if self.switch_steps:
            out["prompt_switch_steps"] = sorted(self.switch_steps)
        return out


def _on_transformer_call(pipe, spec, st, rec, module, args, kwargs):
    step = _step_index(pipe)
    if step != st.step:
        st.step, st.calls = step, 0
    st.pass_name = "cond" if st.calls == 0 else "uncond"
    st.calls += 1
    changed = False
    ps = spec.prompt_switch
    if ps and ps.get("pack") and st.pass_name == "cond" and _in(step, ps["range"]):
        # Swap in the other prompt's packed text before anything below reads the sequence layout.
        kwargs = {**kwargs, **ps["pack"]}
        changed = True
        rec.switch_steps.add(step)
    try:
        st.und_len = int(kwargs["und_len"])
        st.T, st.ph, st.pw = kwargs["vision_token_shapes"][0]
        noisy = set(kwargs["vision_noisy_frame_indexes"][0].tolist())
    except KeyError as e:
        raise RuntimeError(f"internals hooks expect the transformer to be called with keyword {e}; diffusers changed?")
    st.S = st.ph * st.pw
    st.cond_frames = tuple(f for f in range(st.T) if f not in noisy)
    if spec.steer is not None and spec.steer["vectors"]:
        for layer, v in spec.steer["vectors"].items():
            if v.ndim == 2 and v.shape[0] != st.T:
                raise RuntimeError(f"steering vector for layer {layer} has {v.shape[0]} frames, the model got {st.T} latent frames")
    n = spec.cond_noise
    if n and n["level"] > 0 and st.cond_frames and _in(step, n["range"]):
        x = kwargs["vision_tokens"][0]  # [1, C, T, H, W] latent, cond frames clean
        if not hasattr(st, "eps") or st.eps.shape != x.shape:  # fixed noise for every step, from its own CPU generator
            st.eps = torch.randn(x.shape, generator=torch.Generator().manual_seed(n["seed"]), dtype=torch.float32)
        eps = st.eps.to(x.device)
        y = x.clone()
        for f in st.cond_frames:
            y[:, :, f] = ((1 - n["level"]) * x[:, :, f].float() + n["level"] * eps[:, :, f]).to(x.dtype)
        rec.noise_steps.add(step)
        return args, {**kwargs, "vision_tokens": [y, *kwargs["vision_tokens"][1:]]}
    return (args, kwargs) if changed else None


def _attn_wrapper(orig, spec, st, rec):
    a = spec.cond_attn
    log_f = math.log(a["factor"]) if a["factor"] > 0 else -math.inf

    def wrapped(query, key, value, *args, is_causal=False, **kw):
        if is_causal or not st.attn_on or not st.cond_frames or kw.get("attn_mask") is not None:
            return orig(query, key, value, *args, is_causal=is_causal, **kw)
        Lq, Lk = query.shape[1], key.shape[1]
        if st.und_len + Lq != Lk:
            raise RuntimeError(f"unexpected generation-attention shapes: {Lq} queries, {Lk} keys, und_len {st.und_len}")
        bias = torch.zeros(Lk, dtype=query.dtype, device=query.device)
        runs, pos = [], 0  # runs of generation queries: (start, end, is_conditioning_frame)
        for f in st.cond_frames:
            bias[st.und_len + f * st.S: st.und_len + (f + 1) * st.S] = log_f
            if f * st.S > pos:
                runs.append((pos, f * st.S, False))
            runs.append((f * st.S, (f + 1) * st.S, True))
            pos = (f + 1) * st.S
        if pos < Lq:
            runs.append((pos, Lq, False))
        bias = bias.view(1, 1, 1, Lk)  # broadcast over batch, heads, queries: key columns of the conditioning frames
        rec.attn_steps.add(st.step)
        # conditioning-frame queries keep ordinary attention (they would otherwise starve their own frame)
        outs = [orig(query[:, s:e], key, value, *args, is_causal=False, **{**kw, "attn_mask": None if is_c else bias})
                for s, e, is_c in runs]
        return torch.cat(outs, dim=1)

    return wrapped


def _steer_hook(spec, st, rec, layer, module, args, output):
    s = spec.steer
    if not (_in(st.step, s["range"]) and st.pass_name in s["passes"]):
        return None
    und, gen = output
    v = s["vectors"][layer].to(device=gen.device)
    T, S, D = st.T, st.S, gen.shape[-1]
    per_frame = (v if v.ndim == 2 else v.expand(T, D)) * s["alpha"]
    w = torch.ones(T, device=gen.device) if s["profile"] is None else torch.tensor(s["profile"], device=gen.device)
    if not s["include_cond"]:
        w[list(st.cond_frames)] = 0.0
    delta = (per_frame * w[:, None]).to(gen.dtype)
    gen = gen.clone()
    gen[: T * S].view(T, S, D).add_(delta[:, None, :])
    rec.steered.append((st.step, st.pass_name, layer))
    return und, gen


def _capture_hook(spec, st, rec, layer, module, args, output):
    c = spec.capture
    if not (_in(st.step, c["range"]) and (st.step - c["range"][0]) % c["every"] == 0 and st.pass_name in c["passes"]):
        return None
    gen = output[1][: st.T * st.S].view(st.T, st.S, -1)
    key = f"s{st.step:03d}_{st.pass_name}_L{layer:02d}"
    rec.arrays[key + "_mean"] = gen.float().mean(1).cpu().numpy()  # [T, D]
    if c["full"]:
        rec.arrays[key + "_full"] = gen.half().cpu().numpy()  # [T, S, D]
    rec.meta.update(latent_frames=st.T, patch_grid=[st.ph, st.pw])
    return None


@contextlib.contextmanager
def installed(pipe, spec: Spec):
    """Install the spec's hooks on pipe.transformer; yields a Recorder; removes everything on exit (try/finally)."""
    tr, st, rec = pipe.transformer, _State(), Recorder()
    with contextlib.ExitStack() as stack:
        if spec.rope:
            stack.enter_context(rope_scaled(tr, spec.rope))
        if spec.cond_noise or spec.cond_attn or spec.capture or spec.steer or spec.prompt_switch:
            h = tr.register_forward_pre_hook(functools.partial(_on_transformer_call, pipe, spec, st, rec), with_kwargs=True)
            stack.callback(h.remove)
        if spec.cond_attn:
            orig = _tc.dispatch_attention_fn
            _tc.dispatch_attention_fn = _attn_wrapper(orig, spec, st, rec)
            stack.callback(setattr, _tc, "dispatch_attention_fn", orig)
            a = spec.cond_attn
            for i in a["layers"]:
                attn = tr.layers[i].self_attn
                h1 = attn.register_forward_pre_hook(lambda m, args, a=a: setattr(st, "attn_on", _in(st.step, a["range"])))
                h2 = attn.register_forward_hook(lambda m, args, out: setattr(st, "attn_on", False))
                stack.callback(h1.remove)
                stack.callback(h2.remove)
        if spec.steer:  # registered before capture, so a captured block shows the steered output
            for layer in spec.steer["vectors"]:
                stack.callback(tr.layers[layer].register_forward_hook(functools.partial(_steer_hook, spec, st, rec, layer)).remove)
        if spec.capture:
            for layer in spec.capture["layers"]:
                stack.callback(tr.layers[layer].register_forward_hook(functools.partial(_capture_hook, spec, st, rec, layer)).remove)
        yield rec


def save_capture(store: ArtifactStore, rec: Recorder, spec: Spec, request_meta: dict):
    """Write the captured arrays to the artifact store; returns the id (None if nothing was captured)."""
    if not rec.arrays:
        return None
    aid = store.new_id()
    store.save(aid, rec.arrays, dict(spec=spec.raw.get("capture"), shapes="*_mean: [T, D] float32; *_full: [T, S, D] float16",
                                     **rec.meta, **request_meta))
    return aid
