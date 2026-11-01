# E1: text changes an image-change proxy alongside a large seed association

This is an **unvalidated diagnostic on a partial snapshot**, not a result about
pendulum period, physical speed, colour compliance, rigidity, causality or a
recipe improvement. The full planned 16-seed analysis is blocked: 58/64 clips
were done, two running and four pending when fetched. Seeds 208 and 216 are
excluded only from the pre-fixed, explicitly labelled complete-seed sensitivity.
These queue states are not model failures. No E2/E3 outputs were accessed.

For 14 complete seed clusters (56 clips, all four prompts per seed), fast wording
increases whole-frame image-change M by **0.7387 [0.4888, 1.0073] gray levels per
native transition**, averaged over requested red/blue. Every seed's averaged
fast−slow contrast is positive. The across-seed SD of the four-prompt seed mean
is 0.7390 gray levels: the mean speed-word contrast and this descriptive spread
are similar in magnitude. This comparison does not identify actual motion speed.

| Diagnostic, complete seeds only | Estimate | 95% seed-bootstrap interval |
|---|---:|---:|
| Red fast−slow M | +0.6770 | [0.4219, 0.9732] |
| Blue fast−slow M | +0.8005 | [0.5086, 1.1113] |
| Fast−slow, average over colour | +0.7387 | [0.4888, 1.0073] |
| Blue−red, average over speed | −0.0202 | [−0.2056, 0.1289] |
| Seed SS / total SS | 0.6797 | [0.1205, 0.7989] |
| Four-prompt SS / total SS | 0.1843 | [0.1044, 0.6007] |
| Seed×prompt SS / total SS | 0.1360 | [0.0791, 0.3395] |

The pre-fixed sensitivity family of three tests has raw p-values
omnibus 0.0001, red 0.0002, blue 0.0003; Holm 0.0003/0.0004/0.0004.
These are the frozen core's 9,999-draw Monte Carlo values, not exact p-values.
An independent exhaustive scalar sign-flip check gives red 2/16384 and blue
4/16384; it checks the directional arithmetic and is not substituted for the
pre-fixed Monte Carlo procedure. The primary family retains all three members
with reported p=null because its 64-cell cube is incomplete. The colour interval
crossing zero is not an equivalence claim.

High seed SS can coexist with a consistent paired text effect. SS shares are
descriptive and depend on the chosen seeds, prompts and outcome; they do not
support the universal claim “motion comes from noise, not text.” Here even a
text effect on M can reflect appearance changes, camera movement, lighting or
deformation. T2V seed variation also changes appearance, unlike an I2V test.
Physical motion claims need eligible, validated measurements of actual objects.

## Setup and method

Owner's exact E1 grid: seeds 201–216; red/blue bob descriptions crossed with
“slowly, each full back-and-forth swing taking about three seconds” and “quickly,
each full back-and-forth swing taking about half a second.” T2V, 832×480,
93 frames at 24 fps, 35 steps, CFG 6, requested shift 10, null negative prompt,
requested `noise.device=cpu`. All completed clips are on queue endpoints q8-5/6
within the declared q8 GPU class. Only 6/14 complete seeds have all four prompts
on one endpoint; exact endpoint matches are 8/14 red speed pairs and 12/14 blue
speed pairs. The protocol stratifies by declared GPU/stack class, not endpoint;
endpoint execution equality remains an unauthenticated assumption. These results
therefore do not isolate text from endpoint-specific execution variation.
The label q8 is not evidence of quantization. The published server default is
Karras, where requested shift is ignored; actual native sigmas/checkpoint/runtime
and sampled-noise hashes are unavailable. Request echoes do not authenticate
execution. This is not independent evidence of an SM-only mechanism.

M uses unchanged `e0_video.py` from 077a68c: native RGB decode, float64 BT.601
grayscale, area resize to 208×120, absolute consecutive-frame differences,
averaged over all 92 transitions and multiplied by 255. No ROI, tracking,
frame alignment, threshold, classifier, colour detector or period estimator.
Planted-case check: **not yet; this is deliberately a pixel proxy**. No NVIDIA
scoreboard pass or real-photo generalization is claimed.

Protocol/core preceded actual outcomes; E1-specific metric/contrasts/missingness
were fixed board #4893 and commit 2149661 (rebased/published 8b14bd6), before
any E1 video, sidecar, author analysis or per-clip output. E0 results were known.
The scalar implementation was written after the source/request-only design
freeze. `PREREG.md` is unchanged. The post-result fetch CLI addition only permits
replaying the frozen queue snapshot after pending jobs finish; it does not
change selection or numerical methods.

## Reproduce the snapshot

Requires Python, NumPy, OpenCV and ffmpeg, plus private queue access. From repo root:

```bash
python3 work/codex-api-4/t223/e1_diagnostic/fetch.py /tmp/e1-clips --frozen
python3 work/codex-api-4/t223/e1_diagnostic/run.py /tmp/e1-clips --out /tmp/e1-replay
python3 work/codex-api-4/t223/e1_diagnostic/verify.py /tmp/e1-replay
cmp /tmp/e1-replay/results.json work/codex-api-4/t223/e1_diagnostic/results.json
```

`--frozen` reuses this package's saved queue records and fetches only the 58 clips
already done in the analyzed snapshot. Omitting it refreshes status and may
produce a follow-up result as missing clips finish; do not overwrite this result.
All queue IDs, owners, requested prompts/settings, hashes and records are saved.
Native clips remain downloadable by exact ID from the announced shared queue.
`examples/` contains the four original seed-201 clips, chosen by seed ID before
looking at the measurements. No GPU requests or referee submissions were made.

58/58 request/native geometry, frame-count and fps contracts pass. Three complete
videos independently decoded with ffmpeg and explicit 4×4 block averaging agree
with the OpenCV traces within 5.56e-16. Independent scalar checks verify the SS
decomposition, contrasts, exhaustive sign flips, all 16 covariance entries and
the blocked primary family. The five pre-existing protocol/core/adapter files
are unchanged. See `verification.json`; arithmetic validation is not a planted pass.
