# E2 partial snapshot: unvalidated image change

The full 192-cell primary is blocked: 127 valid videos, 48 cancelled, 4 running,
13 pending; all four registered primary p values remain null. The pre-fixed
sensitivity uses 9 complete seed clusters and 108 cells. Intervals resample these
seeds (2,000 percentile draws), conditional on the three scenes and four recipes.
They do not estimate a scene population or physical constants.

| SS component | Share | 95% seed-bootstrap interval |
|---|---:|---:|
| seed | 19.49% | 2.92–32.52% |
| prompt | 1.75% | 0.72–5.17% |
| input | 30.34% | 18.33–55.68% |
| seed:prompt | 4.60% | 2.42–5.94% |
| seed:input | 28.52% | 13.49–35.00% |
| prompt:input | 4.01% | 2.39–10.42% |
| seed:prompt:input_or_residual | 11.30% | 3.84–16.59% |

No undefined bootstrap draws. Input bundles image and base text. QT asks for
settling on ball/held scenes, and 1.2-second swings on the pendulum. These are
associations, not a causal allocation between noise and text. The three-way term
also absorbs unidentified within-cell numerical variability.

| Recipe contrast averaged over inputs | M difference ± seed SE | 95% interval | Raw p | Holm p (4 tests) |
|---|---:|---:|---:|---:|
| R_minus_F | -0.097897 ± 0.076620 | [-0.233654, +0.042536] | 0.218750 | 0.218750 |
| N_minus_F | -0.088811 ± 0.035892 | [-0.158508, -0.023913] | 0.042969 | 0.085938 |
| QT_minus_F | -0.181389 ± 0.054219 | [-0.280937, -0.087743] | 0.015625 | 0.046875 |

Units are gray levels per native frame transition. The four-recipe omnibus has
raw p=0.0061 and Holm p=0.0244 (9,999-draw Monte Carlo). Contrasts use all 512 sign
flips. These tests describe the selected nine-seed sensitivity, not the blocked
primary. Intervals are unadjusted; p values include multiplicity adjustment.

| Scene | R−F | N−F | QT−F |
|---|---|---|---|
| ball | -0.147 [-0.415, +0.074] | -0.120 [-0.290, +0.019] | -0.220 [-0.426, -0.051] |
| held | +0.081 [-0.259, +0.370] | +0.045 [-0.105, +0.213] | -0.310 [-0.633, -0.069] |
| pend | -0.228 [-0.396, -0.073] | -0.191 [-0.286, -0.096] | -0.014 [-0.125, +0.082] |

Within-scene means and unadjusted 95% intervals are descriptive, with no extra
hypothesis tests. Neutral wording changes M too. A reduction in whole-frame image
change does not establish settling, release, identity or correct physical speed.

All 127 native/request contracts pass. Three independent FFmpeg/block-area traces
agree to 5.56e−16. Independent scalar seven-term SS, contrasts/SE, 144 covariances
and exhaustive sign-flip checks pass. Five original protocol/core/adapter files
remain byte-identical. Source hashes confirm ball/held text matches within all
four recipes, whereas every pendulum prompt differs.

Exact endpoint pairing holds in only 3–7 of 9 seeds per contrast, despite the
declared common q8 GPU class. Noise-tensor/input-byte identity, runtime, checkpoint
and actual sampler sigmas are unverified. Published Karras defaults ignore the
requested shift 10. No NVIDIA scores, planted physics validation, equivalence,
seed-bank transfer, improved recipe or noise-versus-text cause is established.

The three native examples (F, seed 301, one per scene) were fixed before metric
inspection. They illustrate inputs, not the outcome distribution. Other native
clips can be fetched by exact saved ID with `fetch.py --frozen`.
