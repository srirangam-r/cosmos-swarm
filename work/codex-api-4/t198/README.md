# Task198: independent native geometry and period review of #4165

The two fresh clips judged visually eligible before opening their identities
both run slowly with a different, unchanged planted-PASS estimator. The third
author-gate pass remains visually unclear. This is narrow same-video replication,
not a fresh generation, proof of rigid mechanics, or a clock mechanism.

| Seed | Opaque ID | Native rigid QC | Author rod-angle T (s) | Independent measure_pend T (s) | Tool fit CI95 (s) |
|---|---|---|---:|---:|---|
|23|Q05|Y|1.680|1.691|1.654–1.735|
|16|Q07|U|2.440|2.485|2.438–2.538|
|24|Q08|Y|1.750|1.733|1.678–1.783|

All three independently measured clips have the tool's `ok` flag. Their mean
is **1.969 ±0.258 s seed SE (n=3)**, or **1.672 ±0.219** times the real
continuation measured by the same tool (1.177659 s; mocap 1.173449 s).
The two native-Y clips alone read **1.712 ±0.021 s (n=2)**, ratio
**1.453 ±0.018**. These are descriptive, selected-sample SEs; n=2 is very small,
and the SEs omit selection, systematic measurement and reference uncertainty.
The CIs are conditional residual-bootstrap fit intervals; task8 found only
11/19 nominal95% coverage on eligible real recordings, so these are not
calibrated physical confidence intervals.

The author's fresh selected mean reproduces 1.956667 ±0.242510 s, ratio
1.672365 ±0.207274 versus its rod-angle real reference 1.170 s. The selected
pooled six-clip arithmetic reproduces 1.975 ±0.131422 s. All12 fresh gate
decisions and G3 median values independently reproduce exactly (<1e-12).

## Apparatus QC and scope

Frozen native codes across all12 fresh clips: rigid **Y2/N6/U4**, single
rod/bob **Y7/N5/U0**, recognizable scene/fixed attachment/visible motion **Y12**.
Q02/Q03/Q06/Q09/Q10 have clear extra branches or ball-like objects; Q12 has
a clearly curved rod in consecutive frames65–66. Four uncertain geometry
judgments are retained. All three author passes are native Y2/U1, with zero
definite N in the intersection. This supports, rather than contradicts, a slow
oscillation in the two visually eligible clips. Visual Y means a plausible
apparatus under the stated review, not validated metric rigidity.

The G3 rule scores a median on theta∈[-20°,80°], not every frame or angle.
It scores 57/78 tracked frames for s23, 69/93 for s16 and48/70 for s24.
Within those scored frames, relative deviations ≥20% occur in23/57,34/69,
and13/48, respectively. This does not contradict the median gate. S24 reaches
113.9° in the author's angle series; overswing was explicitly retained as a
separate physical issue, not used to exclude it from rigidity QC.

These measurements do not establish an apparatus-preserving rate for all
seeds, the period of rejected/unclear clips, a universal slow clock, a cause,
a recipe improvement or NVIDIA no-regression. The intervals and apparent
agreement do not remove selection bias. No training, new generation or
referee submission occurred.

## Protocol and provenance

Protocol fixed in task198 thread #4193 before viewing fresh movies/per-clip
outputs. Aggregate #4165, including named passing seeds and its visual caveats,
was already known. One unvalidated LLM coder, partial masking only. The key
hash posted #4195 before review is
`1f42b08d274430e20946ceed35437c1d59585c7450af8ce92a95f03918ea3028`.
Codes froze in #4212 and tag `codex-api-4-t198-qc-freeze` (original cc2daf6),
before key/gates/periods were opened. Frozen CSV SHA256:
`913d14657644cbe2e070bc1b71c8afa964791b6d1a86e18b4890200d22824608`.
Native stride4 crops,8 consecutive-frame followups and full-frame overviews
are included. A known real10 continuation was viewed to calibrate perspective
before final coding; it is copied from task8's review derivative, not used to
derive the real measurement (which used unencoded transformed source frames).

Settings: original task191 base prompt/input, seeds14–25, Cosmos3-Nano I2V,
q8-0..7,832×480,93f@24fps,35steps,CFG6,empty negative. Source reports Karras
sigmas with requested flow_shift10 ignored. Sampler/checkpoint/initial tensors
were not authenticated independently. All12 queue request/sidecar/movie
contracts pass; all12 decoded f0s match each other byte for byte. Original
submitted input bytes are not authenticated by this fact. Sidecars, request
manifest, original-video hashes and decoded contracts are included.

Independent estimator: unchanged `measure_pend.py` + `trk.py` from2e26463,
byte hashes checked. Composite planted referee PASS20/20, with all4 period
cases <5% error; copied referee response in source/. This tracker is separate
from the author's rod-angle code. It often tracks a rod centroid rather than
the bob, so frozen apparatus eligibility still matters. Native validity and
the author's rod gates are not planted-validated. Real reference is copied
from task8's immutable `657e902` record, with nominal25Hz after duplicate-frame
removal; task8 documents timebase sensitivity. A 93f real and a 93f Nano clip
cover different elapsed durations, accounted for by their fps.

## Reproduce

From this directory (Python3, numpy, scipy, opencv-python, Pillow, matplotlib):

```sh
python3 verify.py
python3 analyze.py /tmp/t198-results.json
python3 measure_existing.py examples
```

`examples/Q05.mp4`,Q07 andQ08 are untouched originals. The measurement runner
also accepts the full fetched directory containing original source names;
the bundled opaque names are accepted for standalone replay.
`prepare.py <clips_dir>` re-fetches the exact12 completed queue jobs if missing
and recreates the36 review panels and opaque key. It never submits generation.
All36 panels replay byte for byte locally. Queue URL is recorded in code;
bulk originals remain local and fetchable by their published queue IDs.

`versions.json` records the local libraries. SciPy1.8.0 warns that local
NumPy1.26.4 is outside its supported range; retained source, arithmetic,
contract and deterministic replay checks pass. Cross-decoder pixel identity
is not guaranteed; original MP4 hashes are the portable provenance check.
