# Task 170: late-only activation-steering diagnostic

Adopted agy-5's **already generated** 24 jobs after automatic usage-limit release.
No new generation, GPU service, referee submission, or training. Original prereg:
[`3db3b54`](https://github.com/srirangam-r/cosmos-swarm/tree/3db3b54/work/agy-5/t170).
This is an **unvalidated image-change and visual-QC diagnostic**, not a measured
improvement in physics or an inference recipe.

## Result

Late-only L12 v12 steering reduces the late corridor pixel-change proxy on these
two real GAUGE mid-fall images and four seeds. The original preregistered
statistical decision labelled H-D is met. It establishes a late-step contribution
to this proxy, conditional on the requested hooks actually firing and the assumed
historical q8 comparability. It does **not** establish a general motion damper,
physical dissipation, equivalent effects to all-step steering, or an event-plan
mechanism. No new NVIDIA scoreboard scores were collected.

All numbers below use the **same rounded-gray implementation remeasured from all
64 original videos**. Unit = input × seed, n=8; four distinct seeds (10–13), two
closely related images. Uncertainty after ± is sample SE, not a confidence interval.
The last column averages the two images within each seed before calculating SE
and the one-sided 90% upper t bound (df=3); this is sensitivity analysis.

| Contrast | Mean ± unit SE, gray levels | One-sided 90% upper bound (df=7) | Seed-cluster SE; upper bound |
|---|---:|---:|---:|
| L10 − A0 | −0.6755 ± 0.2293 | −0.3511 | 0.2821; −0.2135 |
| L10 − random RL10 | −0.8128 ± 0.2196 | −0.5022 | 0.2409; −0.4183 |
| L10 − all-step v12 | +0.4206 ± 0.3247 | +0.8801 | 0.2976; +0.9079 |
| L20 − A0 (secondary) | −0.3439 ± 0.1051 | −0.1951 | 0.1357; −0.1216 |
| L20 − L10 (secondary) | +0.3316 ± 0.2124 | +0.6320 | 0.2282; +0.7054 |
| random RL10 − A0 (secondary) | +0.1373 ± 0.0719 | +0.2390 | 0.0478; +0.2156 |
| all-step v12 − A0 (reference reanalysis) | −1.0961 ± 0.3282 | −0.6318 | 0.3941; −0.4506 |
| early-only v12 − A0 (reference reanalysis) | +0.0132 ± 0.1793 | +0.2669 | 0.1467; +0.2535 |

L10−A0 and L10−RL10 are negative in all eight input×seed units and all four seed
averages. L10's mean reduction is about 62% of the all-step reduction on this
rounded-gray readout; this descriptive ratio has no prespecified uncertainty or
equivalence margin. L10−all-step has a wide interval: neither equivalence nor
absence of early/late interactions is established. The early-only null does not
prove that early steps are unimportant.

The **original mixed-implementation prereg** is also preserved: continuous
BT.601 L10 minus published rounded A0 = −0.6582 ± 0.2307, upper90 −0.3318;
continuous L10−RL10 = −0.8056 ± 0.2204, upper90 −0.4937. The original H-D decision
requires these two upper bounds below zero and C1 mean ≤−0.55; all are met.
Continuous, common-method L10−A0 is −0.6634 ± 0.2300. The implementation difference
does not change the decision in this dataset.

## Masked visual QC

All 24 adopted clips were shuffled under C01–C24 before inspecting outcomes.
Protocol board #3885; key hash posted #3887. Prior aggregate steering results were
known. The analyst had seen the source prompts/settings, but did not open the
masked key or numerical outcomes until codes were frozen.

Rest definition: the **same visible ball stationary throughout f72–92**. N means
visible movement within that window; U means loss of identity/ambiguity. No Y
means no confirmed full-window stationarity **by this coding**, not no physical
settling or no stillness later. Several clips become nearly still after moving
within the window. This design does not estimate time to physical rest.

| Arm | Y/N/U | Gross late artifact Y |
|---|---:|---:|
| L10 | 0/8/0 | 0/8 |
| L20 | 0/8/0 | 1/8 |
| random RL10 | 0/8/0 | 2/8 |

Sparse panels show f48–92 every four frames at native pixel scale, crop
x190:480,y100:425. Dense f72–92 inspection additionally checked near-still cases
C09/C11/C17/C19; all move within the specified window. Gross artifact Y at C05
and C10 records simultaneous balls at f88; C20 is block-like/deformed. Artifact
N means no gross artifact identified in these sampled late crops, **not** clean
object continuity through the entire video. No new masked reference-arm coding
was done, so do not compare these artifact counts causally with another coder's
reference codes or infer a population artifact rate. Full-video dynamics and
ball-speed/dial-versus-switch tracking were not assessed.

Codes froze at board #3892, corrected hash in #3893: the first post accidentally
contained a placeholder. Actual unchanged `qc/codes.csv` SHA256:
`aad1a0d003e32923586eed31fcd6ed280cbf441b3739fde588cf8c5e6ea96d63`.
The still-unopened key at that time hashed
`ea7b86cdb10ea74792b8cf5f0ed45c2ca935ba3b6b89aee34c25e85d641bb809`.
It is now public in `res/UNBLIND_key.json`.

## Setup and provenance

Cosmos3-Nano, board q8-0…7 endpoints, declared Diffusers bf16. `q8` is an endpoint
label, **not evidence of quantized weights**. Declared server sampler is
UniPCMultistepScheduler using inherited Karras sigmas; requested flow_shift=10 is
ignored per board #2870/charter v24. 832×480, 93 frames at 24 fps, 35 steps,
guidance=6, empty negative. Inputs `gauge_ball1_dd33_832x480.png` and
`gauge_ball2_dd35_832x480.png` are **mid-event diagnostics**, ineligible as steps of
the final first-frame-only recipe. F prompt, vectors and input assets are in
`work/raj-opus-1/steer128/`.

L10: layer12 v12 α4, conditional pass, steps [10,35). L20: [20,35).
RL10: rounded equal-norm random-vector control, α4, [10,35). All original 40
reference clips (A0/all-step/early-only/random-all/QT, eight each) were fetched
from owner rog-cc rather than regenerated. Requests use vectors rounded to four
significant digits. `analyze.py` verifies every element against the source assets,
the complete prompt, seed, input filename, endpoint family, and settings on all
64 sidecars. All actual video contracts are 93×480×832, 24 fps. Same-unit frame0
is pixel-identical between every adopted arm and A0. This does not verify equality
of the original input files or initial noise latents.

**Native hook-execution limitation:** queue sidecars preserve the requested spec
but omit the server's `internals.steer_applied` summary. Actual hook firings,
historical software versions and initial latents were not independently archived
in this package. Native summaries requested from the endpoint operator in compute
message #3897; no answer at analysis time. Within-q8 reproducibility #3815 supports
pairing for its sampled fresh T2V requests, not direct proof for these historical
I2V requests. The request checks and different output videos support a useful
diagnostic; exact step-causality remains conditional on this provenance.

## Measurement and verification

For frame pairs f72→73 through f91→92 (20), calculate mean absolute grayscale
change in x220:360,y130:360, then average the twenty values. Gray levels are on
0–255. This measures **image change**, including shadows, background movement,
shape and texture changes. It is not speed, motion energy, or physical dissipation.
No planted test covers this readout; it and the visual codes remain unvalidated.

OpenCV-rounded-gray results from the 40 references match the author's saved
values within 4.46e−7 gray levels (float precision). Arithmetic checks pass for
constant contrasts, a known SE and a known t quantile. Independent ffmpeg RGB
decoding for L10 ball2 s11 and RL10 ball2 s11 reproduces all 92 continuous trace
values per clip to <1e−12. No inference from these checks to physics validation.
Standalone replay reproduces all six result/key JSON files byte for byte.
Frozen CSV CRLF line endings are intentionally preserved for the posted hash.

## Files and replay

`res/` contains all 64 metric traces, exact contrasts, audits, video/sidecar/decoded
hashes, frozen-code mapping, and key. `source/sidecars.json.gz` preserves all 64
full queue sidecars (including requested vectors); source preregs/results are
snapshotted alongside. `qc/` contains frozen codes and all reviewed panels.
`late_crops/` contains native-scale f48–92 review videos for all adopted clips;
these are **recompressed**, never used for metrics. `original_examples/` preserves
three untouched original MP4s: L10 ball1 s13, L10 ball2 s11, RL10 ball2 s11.

From the repository root, using the shared queue (read-only fetch, no generation):

```bash
python3 <swarm-checkout>/scripts/cosmos_queue.py fetch --owner agy-5 --out /tmp/t170/clips
python3 work/codex-api-4/t170/fetch_references.py /tmp/t170/references
mkdir -p /tmp/t170/qc
cp work/codex-api-4/t170/res/UNBLIND_key.json /tmp/t170/qc/PRIVATE_KEY.json
python3 work/codex-api-4/t170/analyze.py /tmp/t170/clips /tmp/t170/references /tmp/t170/qc /tmp/t170/replayed
python3 work/codex-api-4/t170/verify.py /tmp/t170/clips
```

Compare replayed JSON with `res/`. Source vector/prompt assets are required, so use
the full artifact repo. Fetched originals remain on the announced shared queue
owners agy-5 and rog-cc; hashes identify them exactly. The present batch diagnostic
is complete. Native-summary verification and independent new-seed replication
would be follow-up work; neither a physics fix nor a no-regression pass is claimed.
