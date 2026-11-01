# E2 native-video image-change diagnostic (pre-outcome registry)

Board #5003 fixes this addendum before E2 outcomes, sidecars or clips were
opened. E0 and E1 aggregate and independent results were known. No E3 outcomes
are accessed. Original PROTOCOL/core/decoder/factorial adapter remain unchanged.

Owner E2.jsonl: 192 planned runs, seeds 301–316 × F/R/N/QT × ball/held/pend.
Design-only queue snapshot records all 192 IDs and exact request fields, copied
without status, sidecars or outputs. Owners are raj-noise-e20/e21/e22/e23
(48 each); e23 was found from E2_part3 after the initial owner list missed its
48 cells. All planned endpoints q8-0..7; 125 assigned and 67 unassigned at
snapshot. Freeze allows later assignments only within that declared GPU class.
No new generation or GPU reservations. Requested 832×480, 93 frames, 24 fps,
35 steps, CFG6, shift10, null negative prompt, CPU noise. Published default
Karras ignores shift10; authenticated actual sigmas/runtime/checkpoint/input
bytes/noise tensor records remain unavailable, so execution is unverified.

Outcome M is exactly E1's unchanged diagnostic:
255 × mean(abs(e0_video.decode_changes)), all92 native transitions, whole-frame
float64 BT.601 luma then 208×120 INTER_AREA. Units gray levels/native transition.
It is UNVALIDATED: image change combines motion, appearance, lighting, camera
and codec effects. It does not measure physical speed/period, rest, release,
identity, requested-colour compliance or model accuracy. No classifier, fit,
referee submission or threshold tuning is introduced.

These are prompt-RECIPE classes, not four verbatim prompts across three images.
Ball and held share text, but pend F has a different base prompt; pend QT asks
for1.2s swings whereas ball/held QT asks for settling. Input SS therefore bundles
image and base-text variation. QT and its interactions compare different
interventions across scenes. Do not read the cube as a pure image effect or a
universal causal allocation between noise and text. Shared seed is a requested
factor; absence of actual sampled-noise shape/hash prevents tensor identity.

Primary: full16×4×3 cube within declared q8 GPU class. Seven SS/total-SS shares
and seed-cluster percentile95% CIs, 2000 draws/RNG20261101, frozen analysis_core.
One Holm family4: within-seed4recipe omnibus, plus R−F, N−F, QT−F, each averaged
over the three inputs. Omnibus permutes recipe labels within each seed with one
permutation shared across inputs; contrasts use whole-seed sign flips. 9999
permutations/plus-one MC, RNG20261102, or exact if frozen core chooses exact.
No p>0.05 equivalence and no arbitrary eta threshold.

Descriptive secondary: all9 within-input R/N/QT−F effects, seed-level percentile
CIs and SE; per-input seed-mean SD; each recipe effect compared with that spread;
12×12 sample covariance/correlation; per-seed cells and endpoint pairing counts.
These have no extra hypothesis tests. Whole seed clusters only; no clip pooling.
Independent scalar SS/Mobius decomposition and contrast/covariance checks, plus
exhaustive scalar sign tests if complete-seed n≤16. Report these reference exact
p values separately without replacing the frozen core's MC primary p values.

Every192 planned cell retained. Invalid native dimensions/fps/framecount is
invalid, pending/running/cancelled is missing, neither is zero motion or model
failure. If any planned cell is missing/invalid, full primary SS/tests blocked;
all4 family members retained. Pre-fixed sensitivity uses only whole seeds with
all12 valid same-declared-q8 cells. Never drop individual scene/recipe failures
or impute. Later completion requires a follow-up preserving this snapshot.

Hash each fetched native MP4, join exact queue ID/name/owner/request and request-
derived sidecar, audit frame count/geometry/fps. Sidecars are NOT authenticated
execution metadata. Three lexically first valid fetched clips get independent
FFmpeg RGB decode and4×4 block-area full-trace agreement checks. Software
agreement is not planted validation. Log decoder/library versions. Freeze scripts
and registry in git before fetching. No E3, D1–D3 edits or recipe/scoreboard claim.
