# Task 145: non-ball transfer of the task-128 settling vector

Frozen before generation. Diagnostic only; not a recipe claim.

## Question and arms

Does the fixed ball QT−F activation vector at layer 12 transfer to four non-ball scenes? Use the four task-136 T2V scene prompts (block, top, cart, coin) with seeds 4, 5, 6. These seeds were not used to construct the vector (task 128 used ball seeds 1–3). Each scene/seed has seven matched jobs:

- F: unmodified task-136 prompt, no steering.
- S2 and S4: the task-128 ball vector, layer 12, alpha 2 or 4, all 35 denoising steps, conditional pass only.
- Z2 and Z4: the task-128 random vector, per-frame norm-matched to the ball vector, same gain and settings as S2 and S4 respectively.
- N and R: F with the task-133 neutral suffix or Rule R suffix respectively; capture conditional layer-12 spatial means at steps 0 and 5. Capture is read-only and does not steer.

Prompts are exactly in `make_jobs.py`; no still image is used. The steering vector was learned on I2V, whereas these tests are T2V, an important domain difference; frame zero is no longer a clean conditioning latent. All generations: Nano diffusers q8 stack, 832x480, 93 frames at 24 fps, 35 steps, CFG 6, empty negative prompt, requested flow_shift 10; Karras sigmas mean the requested shift is ignored (#2870). All 84 jobs use q8-0 through q8-7 only.

`v_L12_s0s5.npy` and `rand_L12.npy` are from `work/raj-opus-1/steer128` commit 410129f. Four-significant-digit inline JSON values fit the endpoint's 1 MiB form-part limit; relative per-frame norm errors from rounding are under 0.00002. The random vector matches the ball vector's norm, not its semantic direction. Alpha 4 is the highest dose reported in task 128, but neither dose was established to reproduce the full prompt effect; negative results do not rule out other doses or vector constructions.

## Analysis planned before inspecting generated clips

1. Primary transfer contrast: within each scene and seed, calculate a late-motion summary for S2−Z2 and S4−Z4 (secondary: each against F). Reuse task-136's camera-compensated flow metric when available, report its code and all parameters, plus 3 seed pairs per scene and scene-level summaries. Negative values mean less late motion, not automatically physically correct rest. With three seeds, do not treat within-scene uncertainty as strong proof; seed variation and scene variation must be reported separately. Independently inspect blinded native-resolution clips for object identity, actual end state, stationary camera, camera artifacts, and out-of-frame censoring; disclose blindness and censoring. No planted case validates a generic rest metric.
2. For each R/N pair, compute the conditional layer-12 difference of spatial-mean activations at steps 0 and 5, per latent frame, then compare its cosine with the task-128 ball vector. Report each seed and scene, and separately steps 0 and 5; compare whole-frame and frame-averaged cosines. The ball vector is itself averaged over steps 0 and 5. This is a text-effect direction comparison, not evidence of causal transfer on its own.
3. Run the existing `tools/nv_scoreboard` DOVER fused/aesthetic/technical on F, S2, S4, Z2, Z4 with identical settings and seeds. Report matched differences and sampling uncertainty, separately from task 133's prompt-only checks. Interpret any cost as diagnostic, not a full NVIDIA non-regression evaluation. Do not claim a working recipe without all scoreboard items and relevant controls.

Clip sidecars record requested settings, endpoint, and vector hashes. Capture artifact IDs are fetched from the queue-side endpoint after generation. Save all analysis scripts, results and QC in the shared repo; store clips according to the shared clip-store policy. No output inspection occurs before this preregistration.
