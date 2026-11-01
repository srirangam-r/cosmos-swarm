# E1 native-video image-change diagnostic

Fixed in board #4893 before any E1 clip, per-clip outcome, sidecar or author
analysis was opened. Source jobs are from `work/raj-noise/jobs/E1.jsonl` at
165f3ee; source design only was inspected. E0 aggregate/result already known.

There are 64 planned T2V runs: seeds 201–216 × red/blue × slow/fast,
832×480, 93 frames, 24 fps, 35 steps, CFG 6, requested shift 10, CPU noise,
null negative prompt. Queue design-only snapshot SHA256
2f08125c86aa342e718de0ab676af0ae31afb29b181b493bf7ed0bb729b1dd15:
60 endpoint assignments (q8-5/6), four unassigned blue cells in seeds 208/216.
The planned endpoints are q8-4..7. Endpoint labels identify the declared common
q8 GPU class, not quantization. Native runtime/sigmas/checkpoint/noise records
remain unverified. Karras is the published server default and requested
`flow_shift` is ignored under that default; actual sigmas are unavailable.

This addendum adds one explicitly **unvalidated diagnostic**, not a physics
outcome: M = 255 × mean absolute pixel change. Use unchanged
`e0_video.decode_changes`: decode all native frames, float64 BT.601 luma in
[0,1], area resize to 208×120, and take all 92 consecutive differences including
f1−f0. Average absolute change over space and time. Units: gray levels per
native transition at 24 fps. This combines object/scene motion, appearance,
camera changes, lighting and codec effects. It cannot measure period, speed,
rigid swing, physics accuracy or requested-colour compliance. T2V appearance
also varies with seed and prompt, so seed SS here is not identified as dynamics.

Primary planned cube: seed × prompt × one T2V input, within declared q8 stack.
Prompt order red_slow, red_fast, blue_slow, blue_fast. Report all seven SS
shares using unchanged analysis_core, seed-cluster percentile CIs (2,000 draws,
RNG 20261101) and cell means. One Holm family of three two-sided/omnibus tests:
four-prompt omnibus, red_fast−red_slow, blue_fast−blue_slow. Omnibus uses
within-seed label permutations, 9,999 draws and plus-one p (RNG 20261102).
Paired contrasts use whole-seed sign flips with the frozen core's draw rule.

Descriptive secondary: fast−slow averaged over both colours, blue−red averaged
over both speed clauses, paired speed differences divided by the across-seed
SD of each seed's four-prompt mean M, and the complete 4×4 across-seed sample
covariance/correlation matrix. Use whole-seed uncertainty; covariance entries
are descriptive and do not receive extra significance tests. Report seed-level
values, endpoints and counts; no complete-grid inference from missing cells.

Before opening outcomes, fix missingness handling: keep all 64 runs in primary
manifest and preserve all three registered tests. If any planned cell is absent,
invalid or unavailable, primary decomposition/tests stay blocked. An explicitly
labelled sensitivity may use only seeds with all four valid, same-declared-GPU
cells; this changes the population and is not the primary result. Report each
omitted seed and why. Never impute. A later full-64 update is a follow-up.

Native/request contract failures produce invalid outcomes, not zero motion.
Each video is hashed and joined to its queue ID and exact owner job. Fetched
queue sidecars are request-derived evidence, not authenticated native execution.
Later-ready endpoints must belong to the predeclared q8-4..7 class; any other
GPU assignment blocks pooled inference. No same-host repeat generation is
present, so within-seed effects are associations conditional on this stack.

Validate software with an independent ffmpeg RGB decode/block-area calculation
on three lexically first fetched clips and an independent scalar paired-sign
enumeration on the complete-seed sensitivity (if n<=16). Arithmetic checks are
not planted-case validation. No referee submission or classifier tuning.
No E2/E3 outcomes, model generation, GPU compute, q8 use or D1–D3 edits.
