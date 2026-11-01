# Task300: actual CPU proxy rendering for demo277

Four **analytical proxy candidates**, produced by the unmodified shipped
`tools/nano_phys/proxy.py` on the exact task292 images, now have actual
composition, trajectory, mask, codec and contact-sheet evidence. They are
**not Nano outputs, adopted277 inputs, validated physics, or queue jobs**.

**41/41 geometry and decode checks pass. Exact raw frame0 identity is false
in all four candidates.** These are separate outcomes. No acceptance threshold
was loosened. Native sampler acceptance and reader289's raw FAIL/UNVALIDATED
status remain separate, unresolved gates.

| Scene | Supplied P (s) | Expected/traced bob at f1 (px) | Frames / fps |
| --- | --- | --- | --- |
| real06 | 1.186 | (215.36834, 175.25577) | 93 / 24 |
| real06 | 2.0162 | (211.11119, 165.91850) | 93 / 24 |
| real14 | 1.186 | (290.87401, 248.03043) | 93 / 24 |
| real14 | 2.0162 | (307.96747, 251.32114) | 93 / 24 |

The supplied state is task296's **harmonic**, non-rest, A=85 degrees, nominal
inward state. It is not the nonlinear287 law. Image, amplitude, initial
velocity and periods are candidate assumptions requiring executor adoption;
real14's geometric inward sign remains ambiguous under the conservative
annotation envelopes. No continuation was inspected or used to recover motion.
Metric length and gravity remain unknown. The builder's metadata includes an
unused default `g=9.81` even when P is explicit: **that field is not calibration**.

The test intercepts actual calls at the OpenCV boundary while preserving their
arguments and return values, and forwards every composed frame to the actual
MP4 encoder. It compares actual affine-transformed centers against296's
independently expressed harmonic law at all93 times and its pinned f1 values.
Centers agree to numerical precision, radius is fixed, all transformed source
alpha support stays inside832x480, and no rendered alpha touches an image
border. All372 encoded frames decode at24fps, 3.875s per clip. **Traced centers
are geometric diagnostics, not independent bob tracking or a planted-pass
measurement**. Bounds establish lack of frame clipping, not correct segmentation.

Raw composition changes frame0 before encoding, despite an identity affine:

| Scene (both P arms) | Changed pixels / 399360 | Mean absolute channel difference (8-bit) | Pixels with any channel delta >10 | Maximum channel delta |
| --- | --- | --- | --- | --- |
| real06 | 1868 | 0.0155123 | 151 | 123 |
| real14 | 2062 | 0.0170414 | 119 | 162 |

Encoding introduces additional differences: decoded-vs-input mean absolute
channel difference is3.55249/3.56640 (real06/14), versus encoded-vs-raw3.54274/
3.55597. Raw PNGs and amplified composition differences preserve the distinction.
Thus a zero-angle affine check alone does not establish pixel-identical proxy
frame0. This does **not** show that the endpoint violates its separate original
image/frame0 conditioning; no model was called. If exact raw proxy frame0 is
required, the owner can preserve the original at i=0, with codec differences
still evaluated separately. No product source or frozen candidate was changed.

Each `evidence/<scene>_P<period>/` contains `proxy.mp4`, full93-frame
`trace.json`, input/state/source-bound `sidecar.json`, source mask, raw and
encoded frame0 PNGs, difference image and fixed-index annotated contact sheet.
The sidecars hash every media/trace output. `evidence/acceptance.json` contains
all41 checks and the four frame0 observations. `visual_review.json` records the
limited contact-sheet inspection: no semantic clean-mask claim is made.

Run from a clone of the shared repo with Python, numpy and opencv-python:

```bash
python3 work/ro-sol1/t300/check_renderer.py --out /tmp/ro-sol1-t300-recheck
```

The script checks immutable renderer/state/image hashes before rendering. It
blocks socket connections and imports no model. Library versions are recorded;
different encoder/library versions can change MP4 hashes. There were zero
model, queue, GPU or referee requests, and no service was started or changed.

Prior-work methods/results refreshed before create/claim in parent6069:
[ProxyUp](https://arxiv.org/abs/2607.03732) sections4.2–5 separates masked
foreground dynamics from coherence using region noising and stochastic flow
relaxation (simulation MR .52 vs .28 for SDEdit);
[GAUGE](https://arxiv.org/abs/2608.05948) C.3.6 fixes the image-down angular
convention and retains radius drift separately;
[Physics-IQ](https://arxiv.org/abs/2501.09038) Metrics separates spatial motion
from framewise timing and physical-repeat variability. This package reuses those
distinctions for implementation acceptance, without repeating their experiments.
