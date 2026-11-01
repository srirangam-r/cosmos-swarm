# Additive completion of the frozen E1 diagnostic

This package adds the six originally unfinished cells to the prior
[`e1_diagnostic`](../e1_diagnostic/README.md) snapshot. That snapshot and its
58 clip measurements remain unchanged. The six new cells are red-fast and both
blue arms for seeds 208 and 216. There are no new generation requests.

The primary planned population is now all 64 clips: seeds 201–216 crossed with
red/blue and slow/fast wording. `run.py`, `fetch.py`, `verify.py`, `PREREG.md`,
`owner_E1.jsonl` and `design_only_queue.json` are byte-identical copies from the
prior package. The E1 metric and three-test family were frozen at board #4893,
published in 8b14bd6, before any E1 outcome access. The generic protocol and
statistical core preceded that freeze. Completion was announced in task223
#4950. The human aggregate period/colour/late-motion result #4935 was known by
then; this is a completion of the previously fixed image-change analysis,
not a new blind test of that aggregate result.

M = 255 × mean absolute grayscale pixel difference over all 92 native frame
transitions, using `e0_video.py` unchanged from 077a68c: float64 BT.601 luma,
area resize to 208×120, no alignment, crop, track, classifier or period fit.
M combines appearance, camera, lighting, deformation and object motion.
Planted-case check: **not yet; this is an unvalidated pixel diagnostic**.
It cannot establish physical speed, period, colour compliance or rigidity.

Exact setup: declared Cosmos3-Nano T2V, 832×480, 93 frames at 24 fps, 35 steps,
CFG 6, null negative prompt, requested CPU noise and shift 10; 32 clips each on
q8-5/6. The published Karras default ignores requested shift. Queue records
authenticate the request/returned video join, not the executed sampler, input,
noise tensor, checkpoint or runtime. Exact endpoint differs within some pairs;
the declared shared GPU class does not prove identical execution.

All inference treats the 16 seeds as clusters. The fixed three-member Holm
family retains the four-prompt omnibus plus red and blue fast−slow contrasts.
Randomization uses 9,999 draws and plus-one p-values. The frozen core selects
Monte Carlo rather than exact sign enumeration at n=16. Independent exhaustive
scalar values are recorded separately as software checks, not substituted for
the registered method. All percentile intervals use 2,000 whole-seed draws.
Fast−slow averaged over colour and blue−red averaged over speed are descriptive.

The inherited `complete_seed_sensitivity` field now has no excluded seeds and
equals the primary cube and all three test results. Its old generic scope text
refers to the missing-grid path; there is only one population in this complete
update. Do not count this duplicate output or the 14-seed prior snapshot as
independent replication. No data were imputed or silently removed.

`verify.py` checks scalar SS, contrasts, exhaustive sign flips, covariance,
independent FFmpeg/block-average traces and five frozen core/protocol hashes.
`verify_complete.py` additionally checks all 58 previous clip hashes, native
contracts, values and endpoints, the six additions, complete primary family,
and an exact numerical replay from saved design/outcomes. None of these checks
is a planted physics validation. The original four seed201 videos in the prior
package are unchanged examples; all 64 queue IDs and MP4 hashes are recorded
here, with exact videos downloadable from the announced private queue.

From the repository root, Python/NumPy/OpenCV/FFmpeg and queue access:

```bash
python3 work/codex-api-4/t223/e1_complete/fetch.py /tmp/e1-full-clips --frozen
python3 work/codex-api-4/t223/e1_complete/run.py /tmp/e1-full-clips --out /tmp/e1-full-replay
python3 work/codex-api-4/t223/e1_complete/verify_complete.py /tmp/e1-full-replay
cmp /tmp/e1-full-replay/results.json work/codex-api-4/t223/e1_complete/results.json
```

Without downloading videos, numerical replay and verification use the published
data directly:

```bash
python3 work/codex-api-4/t223/e1_complete/verify_complete.py
```

The observed prompt association and seed SS can coexist; SS is not a causal
allocation between text and noise. This is one T2V scene description; the seed
also changes scene layout. E2/E3 outcomes remain unopened. This package makes
no physics, recipe improvement, real-photo generalization or NVIDIA scoreboard
claim and does not modify Deliverables 1–3.
