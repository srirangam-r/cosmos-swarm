# Task 301: runnable task-290 speed-dial analysis

This package persists the exact task-290 analysis and regression from board
messages **5951/5954**, now executed in Node on sha-devel. The analysis contract
is **5950**, for task 265's repurposed simulated-proxy dial (human instruction
5658). It is summary arithmetic over supplied rows. It does not generate,
inspect or measure a video.

**There are no task-265 model observations in this package.** Every example,
including its scene IDs, seed IDs, accepted flags and booleans, is synthetic.
The illustrative empty example retains 30 missing slots and produces no
full-grid slope summary. Its plan is not an adopted execution plan.

## Run

Requires Node (tested v18.19.1). The independent acceptance script also uses
Python 3.12 standard libraries. No package installation is needed.

From this directory:

```sh
python3 verify_runtime.py
node analyze.cjs examples/unity_input.json > synthetic_report.json
node analyze.cjs frozen_measured_input.json > measured_report.json
```

The last command requires an executor-created input. Errors go to stderr,
produce no JSON on stdout, and return status 2. Accepted input returns status
0 even when observations fail QC or are missing: those failures stay in the
report. Redirected files should be reviewed before downstream use, since the
shell creates an empty output file even when a command fails.

`dial_analysis.cjs` and `test_dial_analysis.cjs` preserve the extracted code,
with trailing blank lines normalized to one terminal LF;
`board_provenance.json` retains the original messages. `analyze.cjs` adds file
input, a SHA-256 of the exact input bytes, explicit data-kind labeling, and the
required 3-scene × 2-seed × 5-period shape. It does not alter the frozen math.

## Input contract

The top-level JSON has:

| Field | Meaning |
| --- | --- |
| `data_kind` | `synthetic` or `audited_measurements`; caller labeling, not certification |
| `context` | Optional retained provenance/validation notes |
| `plan` | All 30 frozen slots, including those with missing/failed outputs |
| `observations` | Zero or more rows joined to the plan by exact `id` |

Before looking at results, the executor freezes three actual input identities
and two seeds, then calls `makeDialPlan(sceneIds, seeds)` from
`dial_analysis.cjs`. The function creates each slot as:

```json
{"id":"[\"syntheticA\",1,0.6]","scene":"syntheticA","seed":1,"target_s":0.6}
```

The five commanded proxy periods are exactly `[0.6, 0.9, 1.18, 1.5, 2.0]`
seconds. Do not substitute task 277's different two-scene/three-seed protocol.
The module accepts other crossed scene/seed counts for arithmetic tests; the
CLI enforces the task-265 shape. Duplicate/unknown observations, duplicate
slots, altered doses, or a non-crossed plan are rejected.

Each observation supplies:

| Field | Required value for arithmetic acceptance |
| --- | --- |
| `id` | Exact frozen slot ID |
| `acf_s`, `mp_s` | Positive finite period estimates in **seconds**, kept separate |
| `flag_acf`, `flag_mp` | Both exactly `ok` |
| `flicker` | Finite, nonnegative and strictly less than 0.08 |
| `strip_ok` | Boolean `true` after external strip review |
| `native_verified` | Boolean `true` after external executed-stack review |

Symmetric inter-tool difference must satisfy
`2*abs(acf_s-mp_s)/(acf_s+mp_s) <= 0.10`. A period reported in frames must first
be converted using the audited clip's actual fps. Missing rows and every failed
gate remain in `rows` with reasons; failures are never regenerated or silently
removed by this package. Additional observation fields are retained verbatim.

For measured use, retain links/hashes for the raw clip, sidecar, strip, native
schedule/receipt, per-tool outputs and relevant validation evidence in each
row or context. **This code does not inspect those files, authenticate records,
pass a reader on planted cases, or establish that a caller's booleans are
true.** An `audited_measurements` label is also caller-supplied. A report cannot
replace that external review. Do not set `native_verified` from requested
settings alone.

## Read the report

- Each complete five-dose scene/seed line gets separate ACF and MP slope,
  intercept, R², bias, RMSE and mean absolute relative error to the command.
- A complete-scene slope averages its two complete seed-line slopes. The
  primary `full_grid_slope_summary` is null unless **all 30 slots** pass.
- `secondary_accepted_only_fit`, available complete scenes, adjacent contrasts
  and endpoint contrasts are conditional diagnostics. Show their denominators
  alongside them. Endpoint-only agreement does not fill missing middle doses.
- Scene SD/range/leave-one-scene-out values describe these three reused scenes;
  there is no iid-30 confidence interval or hypothesis test. Dose summaries
  also describe accepted observations, not independent replicates.
- `guided_seed_spread` is a within-cell two-seed SD. It is **not** an
  unmodified-model seed-noise baseline.
- A high R² alone does not establish calibration: the synthetic twice-command
  example has R²=1, slope=2, and 100% mean relative error to the command.
  Scene slopes `[0,1,2]` average to 1 while hiding a nonresponsive scene.

Following a supplied proxy period demonstrates commanded-motion adherence,
conditional on validated measurement. It does not establish recovery of a
scene's true physics, a Nano mechanism, a causal effect or a shipping recipe.
Those claims still need the relevant controls, raw validation and NVIDIA
scoreboard. No demo, queue, sampler, proxy or input has been changed here.

## Acceptance evidence

`verification.json` records:

- Exact-byte matches to source 5951 and regression 5954 after terminal-LF
  normalization only, with SHA-256 hashes. No executable tokens changed.
- 121/121 original synthetic assertions (20 affine fixtures, 11 QC fixtures,
  10 malformed-input rejections) in an actual Node process.
- 101 independent rational-arithmetic OLS fixtures, including non-affine and
  constant outputs: 606 metric comparisons, maximum absolute difference
  `8.881784197001252e-16`.
- 35 actual CLI acceptance checks covering complete/empty/partial grids,
  exact output/digest equality, invalid shape, duplicate/unknown rows,
  altered plans, malformed JSON and command usage.

The rational oracle uses exact raw-sum normal equations and residual sums of
squares in Python. It is independent of the module's centered floating-point
cross-product calculation. These are software checks, not independent Nano
replication, media measurements or planted validation.

## Prior work

Methods and results were refreshed before claiming this bounded task; board
notes 6085/6087 document what was reused and what remains open.

- [ProxyUp](https://arxiv.org/abs/2607.03732), §§4–5: masked intermediate-time
  inversion/noising and stochastic relaxation preserve proxy dynamics while
  controlling appearance/coherence. Simulation motion rationality was .52
  versus .28 for SDEdit. It establishes transfer, not this wrapper's correctness.
- [3DPhysVideo](https://arxiv.org/abs/2605.16795), §§3–4: reconstructed geometry,
  explicit simulation and consistency-guided Flow SDE; VideoPhy .266 and GPT
  physical realism .727±.029, with separately reported visual metrics.
- [Time-to-Move](https://arxiv.org/abs/2511.08633), §§3–4: warped first-frame
  motion references and region-specific denoising clocks. SVD CTD was 7.967;
  dynamic degree can increase through unintended background/camera motion.

We reuse separation of prescribed-motion adherence, calibration, artifacts and
appearance. The published transfer experiments are not rerun here. The open
deliverable was an executable, reviewable version of the existing board-only
analysis, with honest missing-data denominators.
