# Independent review of the corrected analytical proxies

Task304 independently reviews task302's `38e80c8` first-frame correction and
the remaining compositing gate for task277. **The raw boundary correction is
accepted. Clean foreground/background compositing is rejected for these
fixtures.** This is software and image-composition evidence, not a Nano,
physics, planted-case, NVIDIA-scoreboard or recipe-improvement result.

## What was independently checked

Fresh `review.py` loads both sources directly from immutable git revisions,
substitutes an offline raw-frame sink, and hashes every actual writer input.
It does not import or run task302's checker. Four real-photo analytical
fixtures use the pinned292 images, proposed296 harmonic state and supplied
periods1.186/2.0162 seconds. Five additional, newly created software fixtures
cover resized pendulums at rest/outward, balls with/without hold, and one frame.
The synthetic fixtures are explicitly synthetic and do not test real physics.

The checks pass439/439: raw frame0 equals the resized input9/9; the old source
reproduces its boundary difference9/9; all460 later raw frames are unchanged
between old/new source in the same environment. This covers469 frames per
source version. All372 frames in the four archived corrected MP4s decode at
832x480/24fps. Frame0 codec MAE is3.542577/3.556647 channel levels for real06/14,
respectively; encoded frame0 is not pixel-identical.

The check count includes each decoded frame's dimensions. Individual checks,
every raw and decoded digest, source/input provenance and versions are in
[`evidence/review.json`](evidence/review.json).

## What the compositing control shows

An8x8 magenta tag replaces a patch on real06's stationary support, box
`[270,146,278,154)` in the original first image. This patch lies inside the
renderer52px-wide rod strip. In a separate control image, the same tag is
placed outside that strip at`[65,200,73,208)`. These are modified-image
software controls, not measurements of real or generated physical motion.

At frame7, the inside tag has moved about94.31px from its source position and
matches the independently calculated rigid rotation within0.17px. The outside
tag stays at its original position through all four inspected control frames.
This demonstrates that nearby stationary texture is carried by the foreground
mask. It does not estimate the amount of contamination in arbitrary scenes.

Visual inspection of the unannotated raw first-image crops and all four
decoded contact sheets at fixed indices`0,1,4,7,14,28,46,70,92` also shows a
residual source-bob silhouette/inpainting smear, moving support texture and
coarse mask boundaries. In real14, the inpainted region reaches the tabletop.
These observations support retaining the description **coarse analytical
motion scaffold**. They do not support a clean segmentation or corrected-world
rendering label. Only these sampled images received visual review; every frame
was decoded, but not every frame was inspected by eye. The overlays contain
frame/time text only; no predicted bob circle substitutes for visible pixels.

The new synthetic held-ball fixture also records a raw frame0→frame1
composition change while its commanded trajectory is stationary. That is an
expected limit of copying only frame0 while retaining every later baseline
frame; it does not refute task302's narrow correction. See the exact values in
the JSON rather than treating this as physical motion.

## Reproduction and environment

From a full shared-repo clone containing both source revisions:

```bash
python3 -m venv .venv-review304
.venv-review304/bin/pip install -r work/rahul-api-codex/t304/requirements.txt
.venv-review304/bin/python work/rahul-api-codex/t304/review.py --out work/rahul-api-codex/t304/recheck
```

The sink encodes no new videos and makes no network/model/queue/referee call.
It reads the four existing task302 corrected videos, which remain unmodified.
Network connections are disabled in the Python review process. The only git
subcommand is local`git show`. The renderer sink output directory remains
inside this task's workspace.

**Pin dependencies as well as source and proxy hashes.** The initial run with
OpenCV5.0.0/NumPy2.5.4 passed the same boundary/invariance checks, but its real
raw-frame hashes matched the task302 archive only at frame0 in each clip.
That comparison changed multiple dependencies and does not isolate one cause.
`opencv5_review.json` preserves the complete initial run. The pinned rerun uses
OpenCV4.12.0/NumPy2.2.6, matching task302's numeric library versions, and records
archive hash agreement explicitly: **372/372 raw frames match**. Python here is3.12.3, while task302 used
3.10.12. The cross-environment comparison is in`environment_comparison.json`.

## Acceptance limits and handoff

- Accept exact raw frame0 after the existing resize, for the inspected source
  and fixtures; do not extend that acceptance to decoded MP4 or VAE conditioning.
- Accept later-frame source invariance only within a fixed recorded environment.
- Reject a clean compositing claim for the inspected candidates. Any executor
  choosing a deliberately coarse diagnostic scaffold must say so and explicitly
  pin its input/state/builder/environment/rendered-proxy identities.
- No state/prompt adoption, task277 dispatch, native schedule certification,
  reference-future inspection or measuring-tool validation happened here.
  Reader289 retains raw refereeFAIL/UNVALIDATED, pending human question5939.
  Task303 owns the separate native-receipt follow-up.
- Neither marker result nor contact sheet establishes how Nano responds to the
  proxy. No model output was generated or measured; no physics result is claimed.

## Prior work

Methods/results were read before create/claim, parent note6113 and child6116.
[ProxyUp](https://arxiv.org/abs/2607.03732) §§4.2–5 separates foreground dynamics
from foreground/background coherence using masked intermediate inversion and
SFR (simulation motion rationality.52 vs.28 SDEdit).
[GAUGE](https://arxiv.org/abs/2608.05948) C.3.6 preserves pivot/radius diagnostics
and separates periodic fit from period accuracy.
[Physics-IQ](https://arxiv.org/abs/2501.09038v2) Metrics separates spatial from
framewise timing and normalizes to physical-repeat variance. The review reuses
these distinctions; it does not rerun their published motion-transfer studies.
