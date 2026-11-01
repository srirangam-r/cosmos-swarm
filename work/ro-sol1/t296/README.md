# Task296: executable input/state handoff for demo277

This additive package binds completed review294 to the **unchanged** input
manifest and images from292 at `592bf7838ecfcc7eb5b7a5e5d1f7eebd1f91928d`.
It does not adopt the candidate state for the executor or submit model jobs.

`state_contract.json` records the conservative clarification agreed in board
6005/6013: apply the rough 6px/5px tolerance independently to both coordinates
of **both pivot and bob**. These are review envelopes, not calibrated error
bounds or confidence intervals. In real14 the corresponding angular interval
crosses vertical, so geometric “inward” has no robust sign. Its absolute velocity
sign remains an explicitly supplied assumption.

Both angle conventions, their velocity signs, and the OpenCV affine sign are
explicit. Right-positive is `atan2(bob_x-pivot_x,bob_y-pivot_y)`; both angle and
velocity negate under the292 left-positive convention. OpenCV rotation is the
right-positive angular change. The proposed law is **harmonic**, A=85 degrees,
non-rest, P=1.186/2.0162 seconds. It is not the nonlinear287 law or a measured
real trajectory. Metric length and gravity remain null.

| Scene | Period (s) | Prescribed right-positive omega0 (rad/s) | Expected bob at frame1 |
| --- | --- | --- | --- |
| real06 | 1.186 | +3.868768336 | (215.36834, 175.25577) |
| real06 | 2.0162 | +2.275746080 | (211.11119, 165.91850) |
| real14 | 1.186 | -7.850902354 | (290.87401, 248.03043) |
| real14 | 2.0162 | -4.618177855 | (307.96747, 251.32114) |

The overlay PNGs annotate only these supplied first-step centers on the existing
input image. They are not proxy clips, generated Nano outputs, or observations
of real motion.

`input_boundary_review.js` contains the exact code blocks from board6010+6011,
plus their requested JSON print. `source_messages.json` preserves attribution
and original messages. The verifier asserts code-block fidelity and reads the
pinned manifest directly from git before checking the working copy and images.

Run from the shared repo with Python, numpy, opencv-python and Node:

```bash
python3 work/ro-sol1/t296/verify.py --out /tmp/ro-sol1-t296-recheck
```

Actual execution: **30/30 runtime checks PASS** (hashes, image dimensions,
geometry binding, left/right conversion, pixel-identical zero-angle warp,
OpenCV point mapping, expected first-step coordinates and reversed-sign
rejection). Exact reviewer source executes 2678 assertions across36 synthetic
states/1225 perturbations plus16016 sampled envelope points. These are software
checks; they do not validate real annotations or model physics. Library versions
and complete checks are in `runtime_check.json`; original reviewer results are
in `reviewer_result.json`.

An actual renderer must still adopt/freeze the state and prompt, preserve the
input and first-step signs, and check full rod/crop/mask/codec behavior. A zero
image warp here does not prove that a composited proxy preserves frame0.
Native sampler provenance295 and queue serialization5975 remain separate gates.
The289 crossing reader retains **UNVALIDATED / raw referee FAIL** pending human
coverage decision5939. No referee submission, model job, new measurement,
planted PASS or NVIDIA-scoreboard result is included.

Prior work read beyond abstracts before creation/claim, parent6018/child6020:
[ProxyUp](https://arxiv.org/abs/2607.03732) sections4–5 (supplied dynamics with
separate quality), [GAUGE](https://arxiv.org/abs/2608.05948) C.3.6 (image-down
angle/radius), and [Physics-IQ](https://arxiv.org/abs/2501.09038) Metrics (spatial
vs temporal motion). This package reuses their reporting distinctions rather
than repeating a published experiment.
