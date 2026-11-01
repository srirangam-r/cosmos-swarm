# Actual E3 pendulum seed bank: pre-outcome registry

Board #5072 fixes this extension before any actual E3 status, video, sidecar,
measurement or owner analysis is opened. Earlier E0/E1/E2 and retrospective
task141 tie-leakage diagnostics are known. No E3 aggregate is known.

Owner source 14b7b8a contains 72 runs: seeds601–624 by pend10_mid_f93,
pend11_mid_f81, pend14_mid_f81; one identical pend_base prompt. Nominate
pend10 alone for TRAIN, pend11 and pend14 for HELDOUT, irrespective of outcomes.
All24 candidates must appear on both held-out inputs. Top/bottom banks have
six seeds, selected solely on training scores, descending score then ascending
numeric seed. Top is first6, bottom last6 of the same list. All-equal scores
have no ranking signal. Never use held-out labels to resolve a training tie.

Requested 832x480,93frames,24fps,35steps,CFG6,shift10,null negative,CPU noise.
Freeze the exact72 queue IDs and all request fields before opening outcomes.
Primary stratum is declared q8 GPU class only; missing assignments may later
resolve within q8-0..7. Any other executed endpoint blocks the primary stratum.
Same-class is not same-endpoint or authenticated same-stack execution. Published
Karras defaults ignore requested flow_shift; actual sigmas/runtime/checkpoint,
input bytes and sampled-noise shape/dtype/hash remain unverified.

## Outcomes fixed before access

Primary is **joint native swing and period-accuracy success**, a provisional
composite, not an already validated physical failure-rate estimator.
Native apparatus/swing QC uses Y/N/U on five fields:

- scene: the original apparatus remains recognizable.
- single: one connected rod and terminal bob, no second rod/bob or detachment.
- fixed_pivot: original axle attachment persists; no replacement suspension.
- rigid: visually persuasive persistent straight rod and pivot-to-bob geometry;
  clear bending, branching, disconnection or stretching beyond perspective is N.
  Constant projected pixel length is not required; unclear perspective is U.
- swing: visible back-and-forth motion with at least two direction reversals,
  rather than static output or one-way drifting. This is not a period estimate.

Native QC is one unvalidated LLM review. Shuffle all72 opaque IDs, hiding seed
and train/test key. Scene identity may be recognized, so masking is partial.
Review native crop x100:650,y0:400 at frames0,4,...,92 plus full-scene overview;
use consecutive followups wherever needed, with reasons recorded. Codes are
committed/tagged before opening the key, per-clip fit output or rankings.
Unknown is preserved; no fit-driven relabeling. Camera/rigidity ambiguity is U.

Period: unchanged tools/trk_ballfall/{measure_pend.py,trk.py} at planted-PASS
2e26463 (existing referee20/20;4 pendulum estimates<5%). Verify exact source
bytes; use native93 BGR float32 frames,24Hz,tol3,nboot200,seed0, no dedup,
time scaling, fit changes or alternate tracker. Tool flag must be `ok`; `check`,
exceptions and nonfinite output are UNKNOWN for period, never zero seconds.
Store raw tracks/fits privately until native codes are frozen. A planted pass
on the tracker does not validate native apparatus identity or the composite.

Real reference is independently calibrated mocap crossing period over each
nominal93-distinct-frame continuation, using frozen task8 traces/reference.py
at657e9029. Map pend10 start93, pend11/14 start81; end=start92. Use25Hz real
timebase and each trace's existing video-to-mocap sync offset. These are reference
constants, never training data; model outputs use24Hz. Task8 real-video tracker
calibration is19/20, mean tool/mocap1.00720±.00176SE; its CI coverage11/19.
The reference calculation has synthetic and real calibration, not a separate
referee pass. Naming does not authenticate the owner's input-frame bytes.
Report per-input reference values, full cycles and ±1-real-frame sensitivity.

Joint score, for a done artifact passing native/request contract:
1. Any definite native N =>0 (native event/identity failure), without inventing
   a period. This is a provisional QC outcome, not validated physical failure.
2. Otherwise any U or absent QC =>UNKNOWN.
3. All native Y plus tool `ok` and finite period: score1 iff measured/reference
   ratio is in inclusive[0.8,1.2], else0. The20% tolerance is fixed here.
4. All native Y but unresolved fit =>UNKNOWN.
Pending/cancelled/invalid contracts remain missing/invalid irrespective of QC.
Primary needs all72 known joint scores in the declared stratum; no complete-case
replacement and no imputation. The physical-period eligibility rate is reported
separately, with all denominators; definitive native failure is not a period.

Descriptive secondary: native swing success alone (allY=>1, anyN=>0, otherwise
UNKNOWN), and per-input period ratios on native-allY/tool-ok clips. No secondary
transfer p values, no ranking by period on selected available cases, and no
substitution of image change M, rest classifier, or staticness. Primary stays
blocked by any missing/unknown joint score; later completions need an additive
follow-up. Do not shrink the original24 candidates or choose another input split.

## Analysis and safeguards

One primary test: top6 mean joint success on both held-out inputs minus the mean
of ALL24 candidate seeds on those same inputs (expected uniform random bank).
Unchanged analysis_core.seedbank supplies top-bottom, per-input lifts, Spearman,
2000-draw crossed seed/input, seed-only and fixed-bank input bootstrap CIs
(RNG20261101), and9999 whole-seed-map randomizations plus-one p(RNG20261102).
Selection is repeated using TRAINING ONLY in seed bootstrap. Family size1.
Also independently enumerate all C(24,6)=134596 random banks for an exact
one-sided scalar reference; retain core MC p separately. Report training score
ties/boundary tie counts without selecting among tied banks using held-out data.
Only2 held-out inputs, all from one apparatus/camera: all cross-input intervals
are descriptive/underpowered, not population-generalization uncertainty.

Manufactured checks exercise unknown/missing/invalid preservation, training-only
selection, tie-breaks, no ranking signal, scalar subset reference, and gate
composition. Software checks are not planted validation. All source/protocol
files remain unchanged. No new generation/GPU, D1-D3 edits, recipe, cause or
NVIDIA-scoreboard claim; DOVER/DD/plausibility/robot prediction remain unmeasured.

This shift may launch a CPU-only fetch/prepare/period job in the background.
It produces masked panels and opaque fit records; no fit values or rankings are
printed. Freeze native QC in a later shift before unmasking those records.
