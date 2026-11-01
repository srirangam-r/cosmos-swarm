# Program N: independent E0-E3 analysis plan and core

**Status: pre-outcome protocol, not a model result.** Task 223 is assigned by Raj
(board #4464). No `raj-noise` clips, scores or rankings were accessed while writing
this package. The next step is a design-only manifest amendment from Raj, then
metadata/measurement validation and actual analysis. Deliverables 1-3 were not edited.

[PROTOCOL.md](PROTOCOL.md) fixes the estimands, seed clustering, E0 different-seed
null, full factorial interactions, held-out seed ranking, missingness handling,
and controls against selecting static clips. **A seed effect and a text effect
can coexist; this analysis does not assume the program's hypothesis is true.**

`analysis_core.py` implements the numerical core, using only NumPy and the standard
library. `test_core.py` passes 33 manufactured-array checks: each pure factorial
effect and interaction, constant/missing outcomes, seed clustering, cross-host
agreement versus its different-seed null, duplicate bootstrap seed handling,
paired prompt sign flips, training/test separation, ties, and deterministic CLI
replay. These are software checks, not planted physics or classifier validation.

Run:

```bash
python3 work/codex-api-4/t223/test_core.py
python3 work/codex-api-4/t223/analysis_core.py arrays.json --out analysis.json
```

The core accepts these complete numeric arrays:

- `{"analysis":"e0","distances":[...]}`: nonnegative square matrix, reference
  seed by target seed, with matched seed IDs on the diagonal in the same order.
  Reports different-seed minus same-seed distance, whole-seed bootstrap, and a
  column-label correspondence randomization. One result per frozen GPU/stack pair.
- `{"analysis":"factorial","values":[...],"contrasts":[...]}`: a balanced
  `seed x prompt x input` cube. All seven orthogonal SS shares and seed-cluster
  intervals are reported. A contrast is `{"name":"R_minus_base","a":1,"b":0}`
  with fixed prompt indices. It uses paired seed means across inputs and a
  two-sided whole-seed sign-flip test. Holm adjustment in this output covers
  supplied contrasts only; final experiment-wide families still need their full
  registry, including all frozen outcomes/GPU pairs.
- `{"analysis":"e3","training":[...],"testing":[...],"seeds":[...],
  "test_inputs":[...]}`: training/test matrices with the same seed rows. Training
  columns are frozen ranking cells; testing columns have held-out input IDs,
  allowing several prompts per input. Higher must mean better under the frozen
  outcome definition. It ranks training means only, picks first/last quartiles
  of one ordered list, compares top with the whole candidate-pool expectation,
  and reports crossed seed/input, seed-only and fixed-bank input bootstrap CIs.
  The candidate pool must all be evaluated on held-out inputs.

The protocol defaults to 2,000 bootstrap draws and 9,999 randomization draws
(exact enumeration if smaller). Numeric arrays must be finite; unavailable
periods/unknown labels cannot be supplied as zero. They require a separate
missingness/eligibility report before a clearly labelled conditional sensitivity.

The outcome-blind [E0 video adapter](E0_ADAPTER.md) now implements the frozen
primary temporal-change metric, strict planned-run/artifact joins, clip hashes
and native-video contracts. It passes 38 checks on manufactured lossless videos,
including an independent FFmpeg decode and hand area averaging. Its declared
GPU/stack/noise provenance explicitly stays pending until native-record audit.
The protocol and statistical core are unchanged.

The outcome-blind [CPU-noise source audit](noise_audit/README.md) passes 37
checks using real CPU Torch RNG and the exact pinned server route body with a
fake pipeline. It confirms the CPU-generator handoff and explains why
`noise.mixed=false` is expected for plain CPU requests. The current source
sidecar does not record the sampled noise tensor's hash/shape/dtype. This audit
does not clear the live execution gate or inspect any Program N outcome.

The outcome-blind [E1/E2 adapter addendum](FACTORIAL_ADAPTER.md), fixed in board
#4670 before coding or Program N outcome access, now implements strict planned
cube/outcome joins, distinct missing/invalid/unknown tables by each factor,
whole-seed multi-prompt randomization, and the full registered Holm families.
It passes 52 manufactured-record/array checks, including independent scalar
enumeration of the joint null and an input-specific effect that cancels in
pooled prompt means. Registered but untested family members count at p=1 while
their reported p-values remain null. Neither source validation declarations nor
stack declarations are promoted to independently audited evidence. The five
frozen protocol/core/video-adapter files are unchanged.

This is **not yet the complete actual experiment analysis**. The real-job design
manifest, sidecar audit, validated outcome registry (including task 222), E0
secondary measurements and actual execution provenance still await their owners.
The adapter's input schema does not select factor levels, splits, outcomes or
test families on their behalf. Actual run IDs/metadata must be mapped to the
frozen design before any outputs are analyzed.
No synthetic verification value is a Nano finding, and no cross-GPU equivalence
or scoreboard noninferiority margin is invented here.

Evidence is self-contained. `SHA256SUMS` excludes itself and the generated
`synthetic_verification.json`. Runtime: Python 3.10.12, NumPy 1.26.4.

The [historical task-141 reference audit](reference_audit/README.md) exercises
the unchanged adapter on existing public eye codes, separate from actual
raj-noise E0-E3 data. It preserves the unknown rest label, blocks primary
inference, and enumerates both hypothetical binary labels as a retrospective
sensitivity. Prompt share spans 0.499–0.533, seed share 0.158–0.203; QT−F spans
+0.733–+0.767 with exact whole-seed p=0.00390625 in either case. Fifteen checks
include independent exact-rational SS and scalar sign enumeration. These are
same-label robustness results with unvalidated eye codes, not new physics or
planted validation. Label-record hashes are explicitly distinct from video
and noise provenance. Its own `SHA256SUMS` covers the reference package.
