"""Negative-branch metadata mode + NVIDIA default negative for diffusers Cosmos3OmniPipeline (rog2, task 30).

Why: diffusers @86ef420b appends INVERSE metadata to the negative ("The video is not 7.9 seconds long and is not of 24 FPS.
This video is not of 480x832 resolution."), and swaps a None negative for "". NVIDIA's cosmos-framework image2video
defaults instead use the JSON quality negative (neg_prompts.json) + the SAME metadata as the positive
(negative_metadata_mode none -> same via negative_prompt_keep_metadata=true), so duration/fps text cancels in the CFG
difference. See board findings 369 / 382 and work/rog2/pipeline_audit_review/.

negative_metadata_mode:
  "inverse" (diffusers default, what every swarm clip so far used)
  "same"    (cosmos-framework reference): negative gets the same duration/resolution sentences as the positive.
negative_preset "nvidia_default": negative_prompt = json.dumps(cosmos-framework defaults/image2video neg_prompts.json),
  exactly as cosmos-framework args.py builds it (json.dumps(json.loads(file)), default separators).
"""
import contextlib, json
from pathlib import Path

NVIDIA_DEFAULT_NEG_FILE = Path(__file__).parent / "assets" / "cf_default_neg_prompts.json"
MODES = ("inverse", "same")
_ATTRS = ("inverse_duration_template", "inverse_image_resolution_template", "inverse_video_resolution_template")


def nvidia_default_negative() -> str:
    return json.dumps(json.loads(NVIDIA_DEFAULT_NEG_FILE.read_text()))


def resolve_negative(negative_prompt, preset):
    """Return the negative text to pass. preset overrides negative_prompt; unknown presets raise."""
    if preset in (None, "", "none"):
        return negative_prompt
    if preset == "nvidia_default":
        return nvidia_default_negative()
    raise ValueError(f"unknown negative_preset {preset!r}; expected 'nvidia_default'")


@contextlib.contextmanager
def negative_metadata(pipe, mode="inverse"):
    """Temporarily make the pipeline's 'inverse' templates equal to the forward ones (mode='same')."""
    mode = (mode or "inverse").lower()
    if mode not in MODES:
        raise ValueError(f"negative_metadata_mode must be one of {MODES}, got {mode!r}")
    saved = {a: getattr(pipe, a) for a in _ATTRS}
    try:
        if mode == "same":
            pipe.inverse_duration_template = pipe.duration_template
            pipe.inverse_image_resolution_template = pipe.image_resolution_template
            pipe.inverse_video_resolution_template = pipe.video_resolution_template
        yield
    finally:
        for a, v in saved.items():
            setattr(pipe, a, v)
