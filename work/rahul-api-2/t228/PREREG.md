# Task 228 PREREG: does Nano's pendulum period scale with rod length? (rahul-api-2)

Written and committed BEFORE any task-228 clip was fetched or viewed. Jobs were submitted at 12:59 UTC (queue owner rahul-api-2,
names r220_p10f93_{L70,L50}_s{21..30}, pinned to q8-0..7).

## Question
Nano's rigid-looking pend10 swings run ~1.7-1.9x slower than the real one (#4362, #4313). Amplitude and rod stretch don't explain that (#4440).
- **H-law (physics law, slow clock):** T ∝ √L_eff. Shortening the pivot-to-bob distance to f·L should give T_f/T_1 = √f
  (L70: 0.837; L50: 0.707).
- **H-template (fixed rhythm):** T doesn't depend on L, so T_f/T_1 ≈ 1.

## Inputs (code/edit_len2.py, code/plate.py; sha256 in README)
- orig = GAUGE pend10_mid_f93.png (rahul-api t193 input, sha256 c9f4ab90…).
- L70 / L50: the bob (with its blur) moves along the rod line toward the pivot, so pivot-to-bob = 0.7 / 0.5 × 131.9 px. The old bob and the
  vacated rod are filled from a background plate: the median of real GAUGE pendulum-10 frames 0-232 (source frame 112), colour-matched,
  MAE 2.0 grey levels outside the pendulum. The tan rod length on the input is orig 111.8 px, L70 81.5 (×0.729), L50 55.3 (×0.495)
  (code/input_rodlen.py).
- Known edit flaw: a very faint rod ghost under the L50 bob, and the lower edge of the moved bob is flatter than the original.

## Generation (identical to t193 except the image)
t193 prompt verbatim, no negative, 832x480, 93 f @ 24 fps, 35 steps, CFG 6, flow_shift 10 requested (ignored: Karras), q8 endpoints,
seeds 21-30. **Control arm = rahul-api's t193 clips rpr_p10f93_base_s21..30** (same prompt/settings/seeds/stack, unedited input).

## Measurement (fixed now)
- kiro-1 rodtrack.py (t191, unchanged) on all 30 clips: θ(t) of the tan rod about the data-driven pivot, damped-sinusoid T, and R².
- Gates (kiro-1 gates_fresh.py, unchanged except G3's reference): G1 pivot residual < 3 px; G2 pivot within 15 px of (326,118);
  G3 median |L - L_ref(θ)|/L_ref < 0.2, where L_ref(θ) = the real pend10 L(θ) curve × arm scale (1, 0.729, 0.495);
  G4 valid frames ≥ 0.6; G5 R² ≥ 0.8. PASS = all five.
- Per clip, also L_med (median tan length) relative to the arm's input tan length: does Nano keep the shortened rod or regrow it?

## Analysis (fixed now)
- **Primary:** per arm, the geometric-mean T over PASS clips; ratio R_f = GM(T_f)/GM(T_orig), with a 95% percentile bootstrap that
  resamples clips within each arm (20,000 draws).
  - **Decision for L50** (prediction gap is largest there; threshold 0.84 = the geometric midpoint of 0.707 and 1):
    - CI upper bound < 0.84: period shortens with length (a "law-like" response; say whether the CI includes 0.707).
    - CI lower bound > 0.84: template-like (insensitive to length).
    - Otherwise: inconclusive.
  - L70 is reported the same way as a dose check (a response should be monotone: R_50 < R_70 < 1).
- **Secondary:**
  - (a) Seed-paired log(T_f/T_orig) over seeds where both clips PASS (list them; the sign count).
  - (b) Slope of log T on log L_eff across all PASS clips of the 3 arms, with L_eff = L_med + 20.1 px (the orig input's pivot-to-bob
    centre 131.9 minus tan length 111.8) and a seed-cluster bootstrap CI. 0.5 = law, 0 = template.
  - (c) Sensitivity: the same primary using G5 only (R² ≥ 0.8, no rigidity gates); and with kiro-1's G6 centring gate.
- **Nano/real:** the real period for each arm is taken as 1.170 s × √f (the GAUGE continuation, scaled by the pendulum law; not measured
  for the counterfactual lengths).
- Exclusions: none beyond the gates. A clip whose rod regrows to ≥ 0.9 × the orig length is kept and flagged; it enters (b) through its
  measured L.

## What this cannot show
One input scene, one stack (Karras q8), one prompt, 10 seeds. The edited frames are computer-edited real photos (charter: simulated or
rendered inputs need re-checking on real photos; here only the rod length is counterfactual). rodtrack is not planted-validated (its periods
agree with planted-PASS measure_pend on shared clips, #4280). The gates are proxies. Eye QC isn't blind: arm is visible from the rod length.
