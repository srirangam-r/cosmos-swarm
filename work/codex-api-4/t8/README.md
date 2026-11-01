# Real pendulum continuation calibration (task8)

This extends task8's original held-frame calibration to the 93-distinct-frame
real-video continuation used in task182, on all20 GAUGE pendulum recordings.
No generated clips, training, new recipe or GPU job. The method and tracker
are byte-identical to planted-PASS commit2e26463 (existing referee20/20,
4pendulum estimates each<5%; no new referee submission).

## Reproduction

From the shared repository root:

```bash
python3 work/codex-api-4/t8/fetch.py /tmp/t8-originals
python3 work/codex-api-4/t8/analyze.py /tmp/t8-originals /tmp/t8-replay
python3 -m unittest discover -s work/codex-api-4/t8 -p 'test_*.py'
```

`source_manifest.json` records40 original HF file hashes; `dataset_revision.json`
pins the public dev-data revision. Inputs are measured only, never trained on.
`output/results.json` retains all20 records; `summary_all.json` and
`summary_ok.json` use between-recording standard errors. No seed sampling is
involved. All recordings share one rig/camera, so uncertainty does not establish
cross-apparatus generalization.

The unchanged tool uses in-memory BGR float32 frames, with no MP4 roundtrip.
Each source's first300 container frames is deduplicated with the original
0.1×median image-difference threshold. Kept distinct frames[93:186) are
resized1280×720→832×468 and padded6rows above/below. The frozen timebase is
nominal25Hz, matching task182. Some container metadata declares slightly over
30Hz and finite-prefix dedup retains varying counts above250frames; retained indices and metadata
are published for audit. These counts do not define the continuation's fps.

The primary mocap reference uses independently coded PCA/zero crossings over
the tool's post-release fit window. A second reference uses quadratic-refined
turning points and does not depend on a fitted sinusoid. Four analytic synthetic
reference checks pass. The independent reference code has not itself been
submitted to the referee; the Cosmos period tool retains its existing planted
pass. Its original positive calibration and independent real-video comparison
are checks, not permission to interpret any generated blob as a pendulum.

Video/mocap synchronization shares the old centroid onset detector (>3px,
4frames) with an independent mocap onset (>5mm,4frames); ±1video-frame window
sensitivity is reported. `release_frame` inside a mid-swing window is a tool
fit cutoff, not a physical release. The full93-frame mocap window is also
retained. Reference cycles and complete prefix trajectories appear in
`output/traces/`; original reference data can be downloaded from pinned HF.

`output/clips/` contains lossy mp4v review derivatives, each with a provenance
sidecar. Fits were computed before that encoding. QC images and fit tracks are
retained. None of these derivatives is a new generated sample.

## Limits

A calibrated real-video period tool can still return a plausible number from
branching/morphing generated geometry. This does not resolve task184's Nano
apparatus-eligibility problem, demonstrate a Nano clock, or establish a recipe
or NVIDIA scoreboard win. Neither an `ok` flag nor a bootstrap CI validates
identity. Phase, window length and nonlinear perspective can affect fits.

The first wrapper attempts stopped on timebase assertions; the nominal25Hz
protocol was then enforced explicitly before aggregation (board#4064), with
no eligibility or optimizer change. System SciPy emits a NumPy compatibility
warning; analytic checks and exact published-real10 numerical replay are
reported alongside the versions.

## Results

Unchanged `measure_pend v1` passes its own fit checks on **19/20** real
continuations; check IDs: [13]. On the eligible records, fit period divided
by independent same-window mocap crossing period is **1.007195 ±
0.001763 SE** (range 0.998191–1.018778);
12/19 within1%, 19/19 within5%.
The turning-point reference gives **1.006666 ± 0.001731 SE**.
The supplied fit CI95 covers the crossing reference on **11/19**
eligible records: descriptive observed coverage, not a calibrated coverage guarantee.
All20, retaining failures: mean ratio 1.092483 ±
0.085305 SE (max 2.712959).
Maximum reference-period change under ±1distinct-frame alignment is
0.002707s. Crossings versus turning-point reference
periods differ at most 0.002907s across all20.

The measurement tool's exact period, crossing period, R² and damping estimate
on recording10 reproduce task182 byte-level floating values (difference0).
All40 original source files match the pinned HF revision by LFS SHA256 / Git
blob SHA1. Four reference tests and independent arithmetic/contract checks pass.
Full output/traces and the failure cases are retained.

## Post hoc timebase diagnostic

Retained-container timestamps span3.632–3.700s over the nominal3.680s
window. Re-timing only the zero-crossing diagnostic at those timestamps gives
mean ratio 1.001327 ± 0.000933 SE on the same19 tool-ok records, versus1.005008 ±
0.001620 at nominal25Hz. Primary fits, eligibility and summaries remain
unchanged. This sensitivity check identifies a timebase limitation; it is
not a new validated estimator, an explanation of Nano or a repaired CI.
