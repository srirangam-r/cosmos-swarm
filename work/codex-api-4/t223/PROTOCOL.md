# Program N independent analysis, version 1

Task 223, assigned by Raj in board #4464. Written without fetching or inspecting
any `raj-noise` clips, outcome scores, or rankings. This protocol fixes estimands
before outcome access. Job names, planned factor levels, reference GPU,
train/test input IDs, and validated outcome registry are still awaited from Raj.
They will be recorded in a separate **design-only manifest amendment** before
any outcome access. A missing design item is not filled in from observed results.
No Deliverables 1-3 edits and no q8 submissions.

## Interpretation and units

Test whether **matched initial noise predicts motion across the tested
conditions**, and how much measured variation is associated with seed, prompt,
input, and their interactions. Seed influence and text influence can coexist.
Large seed variance does not prove that text has no effect, and a large prompt
effect on colour does not establish control over dynamics. Report both positive
and negative results. Any claim is conditional on the selected prompt contrasts,
inputs, length, sampler, stack, and eligible clips.

Seed is the primary repeated-measure cluster: every input, prompt, and host
using a seed moves together when resampled. No seed-by-input clip is treated as
an independent seed. Inputs are a second generalization unit; the E3 primary
uncertainty resamples held-out inputs and seeds together. Report seed-only CIs
as well. With fewer than 3 distinct seeds or 3 held-out inputs, label intervals
descriptive and underpowered. No result is called equivalent from p>0.05.

Use 2,000 bootstrap draws, percentile 95% intervals, RNG 20261101. Report counts
of constant/undefined bootstrap draws. Randomization uses 9,999 permutations
(plus-one Monte Carlo p), seed 20261102, unless the full permutation set is
smaller and enumerated. Tests are descriptive until eligibility and classifier
validation are established; no physics constant comes from an unvalidated tool.
Primary tests across GPU pairs/outcomes are Holm-adjusted within each experiment;
raw p-values and the family size are retained. No pooled headline across tasks.

## Data contract and exclusions

Freeze a planned row per `run_id`: experiment, seed, input ID/hash, prompt
ID/hash, endpoint, GPU type, stack/code/checkpoint identifiers, CPU/CUDA noise
device, base-noise shape/dtype/hash if logged, sampler/sigmas/settings, split
(train/test), frames/fps/size, duplicate lineage, and planned outcome definitions.
Use a separate outcome file keyed by `run_id`, with value, validity, reason,
method/version and evidence. Keep run sidecars and clip hashes. Validate the
one-to-one join, planned factorial cells, exact settings and pairing first.
Repeated copies of one artifact are provenance checks, not new observations.

Requested CPU noise is not proof that CPU noise was executed. Require execution
metadata or a published live sentinel/hash check; absent records are marked
unverified, not called a malfunction. Equal hashes establish the sampled base
noise only if shape/dtype/packing are equal. They do not guarantee equal outputs
or every internal random draw. CPU noise is a factor, not a free permission to
pool different stacks. Until E0 is resolved, all paired E1-E3 inference is within
GPU type. Even if E0 passes, primary results remain stack-stratified.

Do not drop artifacts or failures silently. Rest/moving and release/identity
success are distinct outcomes. Task 222 supplies rest only after validation.
Report rigid/trackable rate for period, and period conditional on that eligibility;
report unknown labels and missingness by seed/prompt/input. A period failure is
not zero motion or a zero-second period. No complete-case period result is an
unconditional model effect. A fully populated planned cube is required for the
primary factorial decomposition; otherwise report missingness and explicitly
label any complete-case sensitivity. No imputation for primary outcomes.

## E0: cross-GPU seed correspondence

Within fixed input/prompt/settings/noise-device/stack-comparison strata, build
an all-by-all matrix `D[i,j]` comparing reference-GPU seed i to target-GPU seed j.
The reference GPU and compared GPU pairs are frozen from design metadata.

Primary continuous clip distance: decode at native frame rate, remove frame 0,
convert RGB to grayscale in [0,1], area-resize to 208x120, and compare consecutive
frame differences (including the f0-to-f1 transition). `D` is the mean absolute
difference of these temporal-change arrays. This is an unvalidated pixel-motion
proxy, not a physics estimator. Videos with mismatched frame count, fps or
geometry fail the contract; no temporal alignment or optical-flow registration.
Same-host repeat should give D=0 (codec differences are recorded separately).

Primary estimand: mean off-diagonal D minus mean diagonal D. Positive means
matching a seed improves cross-GPU agreement over a different seed. Also report
both distances, their ratio when the null distance is nonzero, and every seed's
contribution. Bootstrap source seeds as whole matched source/target clusters;
off-diagonal comparisons exclude equal ORIGINAL seed IDs even when a bootstrap
resample repeats an ID. Use a one-sided column-label permutation test for the
positive correspondence alternative. This null controls for shared background,
static outputs, and large outcome prevalence.

Secondary: raw RGB distance, validated rest agreement minus its different-seed
null, categorical release/identity agreement, and paired period correlation
only on jointly eligible clips. Constant labels make kappa undefined; report
prevalence and agreement lift instead. Where CPU and CUDA grids are both present,
report their seed-paired difference in correspondence advantage. Same-prompt
different-seed and same-seed same-host repeat controls are required.

Passing E0 means detectable correspondence on this test, not bit identity or
cross-stack equivalence. Exact noise/output identity is reported separately.

## E1/E2: seed, prompt, input, interactions

For each frozen outcome and compatible stack stratum, form the balanced
`seed x prompt x input` cube. E1 colour compliance is a separate outcome from
rest, motion or period. Colour is scored against the requested colour, rather
than treating a requested blue bob as an error because the base bob was red.

Decompose total sum of squared deviations into the orthogonal balanced-design
seed, prompt, input, seed:prompt, seed:input, prompt:input and three-way terms.
Report every SS/total-SS share (eta squared), its seed-cluster bootstrap interval,
the factor level counts, and cell means. The three-way term also absorbs
unmeasured within-cell numerical variability when there is one sample per cell;
it is not identified as a physical interaction. A constant cube has zero total
SS and undefined shares, not a claim of zero effects.

The seed main-effect share measures stability of a seed's outcome averaged over
the tested prompts and inputs. Prompt main effects and prompt:seed interactions
both matter to whether text changes dynamics. Do not sum seed-containing terms
and call them a text-free cause. Compare absolute paired prompt contrasts with
the across-seed spread, preserving paired seeds; report all prespecified contrasts.
For two prompts use whole-seed sign flips of the paired differences; for more
prompts permute prompt labels independently within seed, sharing each permutation
across that seed's inputs. Never permute each clip independently. No eta-squared
threshold alone is used to accept the sweeping 'noise, not text' claim.

## E3: ranking transfer, with held-out inputs

Freeze training and held-out inputs/prompts from the design manifest. Rank
seeds ONLY on the designated training cells' mean predeclared success score.
For binary event success, this must include release/event initiation and object
identity plus the intended ending; rest alone can reward a static failure.
If only rest is available, label the analysis 'rest-ranking diagnostic' and
do not call it an improvement. Other quality/motion safeguards remain separate.

Default bank size is `ceil(n_seed/4)`; top and bottom banks are disjoint, ties
break by ascending numeric seed in a single descending-score list (top takes
the first k positions and bottom takes the last k), fixed before held-out scores
are opened.
Report the number and position of training ties; all-equal training values mean
no ranking signal. A bank size chosen by the experiment owner before outcome
access is recorded as a design amendment, with the default retained as sensitivity.

Primary test score: top-bank mean minus the mean over ALL candidate seeds on the
same held-out cells (the expected equally likely random bank from this candidate
pool). Also report top-minus-bottom, per-input effects, and train/test seed-rank
Spearman correlation when defined. The random-bank reference is an expectation
from the candidate pool, not a new independent generation arm. If only selected
seeds were generated on held-out data, this estimand is unavailable; use a
separately nominated random control and retain that limitation.

Primary CI: resample whole seed clusters and whole held-out input clusters,
retaining every prompt within an input; redo selection using TRAINING VALUES
ONLY in each seed bootstrap. Also report seed-only and fixed-bank held-out-input
bootstrap CIs. A one-sided transfer randomization permutes the mapping between
training ranks and held-out seed trajectories, as whole seed clusters. Do not
rerank on held-out clips, select a favourable held-out input, or use a held-out
input for a cutoff. Failure to transfer, or a static-bank failure, is a result.

Report DOVER, dynamic degree against the real reference at the same fps, event
initiation, identity and rest for top/bottom/random seeds. Thresholds/margins for
scoreboard noninferiority must be approved/frozen before results; none is invented
here. A bank that selects static clips does not count as a fix. No deliverable
claim until both scoreboard and target checks are actually measured.

## Publication and follow-up

Publish this protocol and tested statistical core before fetching outcomes.
Use manufactured arrays only for verification, explicitly marked synthetic.
Freeze any design amendment with a commit and board timestamp. Publish native
manifest, joins, outcome validity, per-seed values and reproducible output.
Any post-outcome change is an explicit exploratory sensitivity; preserve version 1.
Task 223 remains in progress until the actual E0-E3 data are independently analyzed.
