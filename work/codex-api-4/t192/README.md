# Task 192: independent audit of input-blur result #4104

The published 24-clip counts and seed-paired discordances reproduce exactly.
The observed changes are small, but do **not** rule out a useful blur effect.
This is a same-video review with new coding and independent analysis, not
fresh-seed replication, a validated physical measurement, or a successful fix.

## What is supported

One edited real GAUGE v8 frame, seeds 1–4 and 11–14, 8 clips per arm:

| Author's readout | Raw b0 | Blur σ0.5 | Blur σ1.5 |
|---|---:|---:|---:|
| Hover (upward drift allowed) | 4/8 | 5/8 | 3/8 |
| Clean first descent (author's convention) | 1/8 | 0/8 | 2/8 |
| Strict hover (upward drift excluded) | 4/8 | 5/8 | 2/8 |
| Strict clean (borderline excluded) | 0/8 | 0/8 | 2/8 |
| Clone | 8/8 | 8/8 | 6/8 |

Their predeclared count rule selects “AGAINST softness”; that arithmetic is
correct. Their broader statement that softness does not explain the gap is
stronger than this experiment establishes. Relative to raw:

| Paired change | Mean ± seed SE | Descriptive t7 95% | Conservative paired 95% |
|---|---:|---:|---:|
| σ0.5 hover | +12.5 ± 12.5 pp | [−17.1, +42.1] | [−42.0, +57.5] |
| σ1.5 hover | −12.5 ± 12.5 pp | [−42.1, +17.1] | [−57.5, +42.0] |
| σ0.5 clean | −12.5 ± 12.5 pp | [−42.1, +17.1] | [−57.5, +42.0] |
| σ1.5 clean | +12.5 ± 12.5 pp | [−17.1, +42.1] | [−42.0, +57.5] |

All four primary contrasts have just one discordant pair; two-sided exact
sign p=1, favorable one-sided p=0.5 for σ1.5 hover/clean. The strict σ1.5
contrasts are −25.0 ± 16.4 pp hover and +25.0 ± 16.4 pp clean; two-sided p=0.5.
Even a 37.5 pp improvement (the author's 3/8 threshold) is not excluded.
A nonsignificant result does not establish equivalence.

The conservative interval is a post-coding arithmetic addition: take separate
97.5% Clopper–Pearson intervals for the probabilities of positive and negative
paired changes, then subtract their endpoints. A union bound gives at least
95% coverage for the paired probability difference under independent,
exchangeable seeds at this one input/settings. It does not generalize across
scenes. Marginal 95% directional bounds and descriptive 40,000-replicate
seed bootstrap results are also in `results/results.json`. Empirical bootstrap
support can be one-sided or degenerate with these data; it is not a useful
exclusion bound. Zero sample variance produces `t95: null`, never [0,0].

## Independent native-video QC

Protocol posted as #4117 before per-clip outcomes/key; opaque key hash #4126
before panels; codes frozen in #4134 and tag `codex-api-4-t192-qc-freeze`
(original commit f12b7e1). `codes.csv` SHA256:
`084951d4e5ccbb9058003075aff27d66f0039eefaf789c69e092373a871f70f2`.
The key was opened only after freezing. The aggregate source result was known;
blur is visible, so masking is partial. One unvalidated LLM coder.

Reviewed native 320×360 crops every four frames, eight full-frame overviews per
clip, and consecutive f0–23 on 11 ambiguous clips. Q15 received all 93 frames.
These are the published `panels/`; `prepare.py` and `dense.py` reconstruct them
from the original movies. No inferred physical acceleration or period.

| Independent code, Y / N / U | Raw | σ0.5 | σ1.5 |
|---|---:|---:|---:|
| Original descends continuously ≥1 diameter | 2 / 5 / 1 | 1 / 5 / 2 | 3 / 3 / 2 |
| Original stays near initial height | 4 / 3 / 1 | 4 / 2 / 2 | 2 / 4 / 2 |
| Clean throughout whole clip | 0 / 8 / 0 | 0 / 8 / 0 | 1 / 7 / 0 |
| Simultaneous distinct ball-like objects | 6 / 0 / 2 | 7 / 0 / 1 | 5 / 1 / 2 |

U means unresolved identity, disappearance, or sampling ambiguity; never count
it as a negative. These labels use different operational definitions from the
author's. In particular, their `fall` means **leaves the spot by any route**,
including disappearance/morphing; it is not a physical-descent measurement.
Their `hover` allows substantial upward drift. My strict clean rule requires
one continuously identifiable ball throughout the entire clip, whereas the
author's primary clean rule focuses on the first descent.

Consequently, author/independent agreement is 18/19 certain hover codes
(5 unknown), 22/24 clean codes, and 18/19 certain clone codes (5 unknown).
These are descriptive comparisons, not validation. Q21 (σ0.5/s1) moves upward
with a redrawn strap: allowed by author hover, excluded by my near-height rule.
Q04 (raw/s11) is the author's explicitly borderline ghost descent. Q10
(σ1.5/s12) descends, then has separate rear-table and plank balls later in the
clip. `examples/Q10_postfreeze.png` is a source-aware full-frame follow-up,
**made after freezing**, with a clear simultaneous pair at f60. It illustrates
the whole-clip rule; frozen labels were not changed. Q15 (σ1.5/s11) is the only
independent whole-clip clean Y and is included in full.

## Intervention and provenance audit

All 24 metadata/job pairs agree: 832×480, 93 frames at 24 fps, 35 steps,
CFG 6, requested flow_shift 10, identical prompt, no negative prompt, and
matched seed IDs. All 24 originals were decoded on the explicitly shared
machine: exact frame count, dimensions and fps are in `panels/key.json`,
with original-file and decoded-RGB SHA256. Three complete example movies are
bundled and byte-checked against those hashes. The other 21 remain at the
explicit source below, with every sidecar included here.

Decoded RGB bytes differ across the remote ARM ffmpeg 6.1.1 and local x86
ffmpeg 4.4.2 conversions, despite byte-identical MP4 files and frame counts.
The failed exact-RGB replay check is retained in `attempt2_decode_versions.txt`.
Four lossless remote frame samples in `decode_check/` differ from local
conversion by at most **2/255 per channel**, with MAE 0.781–0.803/255; see
`comparison.json`. This is a version/architecture comparison, not an isolated
cause test. The key hashes specify the actual remote decoder used for coding;
`verify.py` reports cross-decoder RGB equality separately and does not require
it. Preserve the MP4s/key and decoder provenance for exact reproduction.


σ0.5 and raw use different endpoint URLs for all eight seed pairs; σ1.5 and
raw share an endpoint in all eight. Both endpoints are declared A6000-class
by the source. Same seed and GPU class alone do not prove identical initial
tensors across endpoints. We did not capture initial tensors, checkpoint
revision, package versions or actual sigma schedule. Karras/ignored
flow_shift is the source/charter report, not a new instrumented observation.

The blur files are byte-exact `cv2.GaussianBlur(raw,(0,0),sigma)` results;
Pillow's approximate GaussianBlur is not byte-equivalent. Full-frame grayscale
Laplacian variances are raw **718.117**, σ0.5 **269.297**, σ1.5 **8.123**;
mean absolute RGB changes are 0.841 and 2.905 levels out of 255. Two proxy
inputs have variances 578.393 and 465.469. Thus the tested blur doses are
substantial, but these global measures neither isolate latent conditioning
nor match local texture, seams or all properties of the compared edits.
`source/SHA256SUMS` is the author's larger manifest: only the seven present,
relevant input/job entries are checked, as enumerated in `results.json`.
The two frozen source-code hashes and blind/unblind joins also pass exactly.

## Reproduce

Python 3, NumPy, SciPy, OpenCV, Pillow, and ffmpeg/ffprobe are required.
From this directory:

```sh
python3 analyze.py source panels /tmp/t192-reanalysis
python3 verify.py
sha256sum -c MANIFEST.sha256
```

`verify.py` independently checks CP intervals using binomial-tail bisection,
exact sign tests with integer binomial sums, the one-discordance SE and t
critical value, zero-variance handling, frozen code/key hashes, source count
and job/input consistency, and byte-identical reanalysis. The local SciPy
1.8.0 warns that NumPy 1.26.4 exceeds its supported range; the independent
closed-form/tail checks are included and this warning is preserved.
The first audit attempt assumed Pillow blur; its failure is retained in
`attempt1_blur_implementation.txt`, followed by the exact OpenCV check.

Source: finding #4104, task174, explicitly shared
`swarm@board.tail0c526a.ts.net:~/jobs/rahul-api/holder_rep/`.
Remote panel generation used only those originals and our own directory
`~/jobs/codex-api-4/task192/`; it started no service or GPU job.
No generation, training, sealed-test access, referee submission, NVIDIA
scoreboard run, improvement, or causal mechanism claim. Planted validation:
**not yet**. No physical number here is validated by these visual codes.
