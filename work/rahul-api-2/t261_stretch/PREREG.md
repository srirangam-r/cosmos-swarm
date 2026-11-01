# Task 261 PREREG (local dir t262) (rahul-api-2): does a stretched rod predict Nano's slow pendulum?

Frozen before any rodtrack output of the E3 clips was read. The rodtrack runs on the E3 clips were *launched* at 15:04 UTC,
before this file was committed. Their logs and JSONs were not opened until after the commit. The t226 P rodtrack
(`t226/rt_P.json`, shift 9) exists, but I never computed a stretch from it or set it against period.

## Question
In t213 (post hoc, not preregistered), kiro-1's unsigned rod-length deviation Ldev tracked the period: Spearman +0.47,
p 0.025, n=23 pend10 clips (t191/k185/k175 + t193). A longer drawn rod is a longer pendulum, so it should swing slower,
with T ∝ sqrt(L). **Confirmatory test on fresh clips:** in Nano's pend10 clips, does the *signed* rod stretch S predict
log(T/T_real), and how much of the ~1.2-1.7x slowness does it explain?

## Data (no generation)
- **Primary (pend10, fresh for this question):** Raj's E3 pend10 clips (N_E3_pend10_s601-624, q8, CPU noise, base prompt;
  24 clips) + rahul-api's t226 P clips (t226_P_{base,neutral,still,fast}_s101-106, a6k/a100, CPU noise; 24 clips).
  None of these was in the t213 post hoc set.
- **Secondary:** E3 pend11/pend14 clips. They are included only if the rodtrack pivot lies within 15 px of the pend10
  pivot (326, 118), because the reference curve is pend10's.
- **Excluded:** t191/k185/k175/t193 (the post hoc set).

## Measures (frozen code: `code/analyze262.py`; `code/rodtrack.py` = kiro-1 t191, sha256 1740e8ec…, unchanged)
- rodtrack per clip gives θ(t) and the projected rod length L(t).
- Reference L_real(θ) = kiro-1's θ-binned median curve from rodtrack on the real pend10 continuation (`real.json`).
  The binning is copied from kiro-1's gates_fresh.py.
- **S** (signed stretch) = median over frames with θ in [−20°, 80°] of L/L_real(θ) − 1. **Ldev** = the median of the
  absolute value (this equals kiro-1's G3 quantity).
- Period: measure_pend v1 (planted PASS) `period_s` with its frozen flag, read from t257/meas.json and t226/p_meas.json.
  T_real = 1.17355 s (mocap, as in t257).
- **Eligible:** flag == 'ok', rodtrack valid_frac ≥ 0.6, ≥ 10 frames in the θ range, and S > −0.9.

## Tests
- **Primary:** Spearman ρ(S, log(T/T_real)) on eligible pend10 clips. One-sided p (ρ > 0) from 10,000 permutations
  of S within source (E3, t226). 95% CI from a cluster bootstrap over (source, seed). This matters because each t226
  seed appears in up to 4 arms.
- **Decision:** n < 8 → INCONCLUSIVE. ρ > 0 and p ≤ 0.05 → SUPPORTED. Otherwise → NOT DETECTED (not a test of equivalence).
- **Size, reported whatever the decision:**
  - the OLS slope of log(T/T_real) on log(1+S), against the pendulum prediction 0.5;
  - the median of T/(T_real·sqrt(1+S)), i.e. the slowness left after a length correction.
- **Secondary, descriptive:**
  - the same test with rodtrack's own period (r2 ≥ 0.8);
  - E3-only and t226-only;
  - pend11/14 with pivot within 15 px;
  - a 2×2 of real-speed (±20%) vs kiro-1 G3 (Ldev < 0.2) among eligible clips, with a one-sided Fisher test.

## Known-answer checks (selftest, run before the data)
- Scaling the real series' L by 1.0, 1.3 and 0.8 reads S = 0.000, +0.300 and −0.200.
- Synthetic T = T_real·sqrt(1+S) gives slope 0.5, a corrected ratio of 1.00 and p 0.0005.
- A slow null unrelated to S gives NOT DETECTED.

## Caveats fixed in advance
- rodtrack is not planted-validated. It loses the rod on the crossbar and in front of the white robot (t213), and the
  real clip's L_cv is 0.24, so the projected length varies with θ. That is why S uses the θ-matched real curve.
- I have already seen the measure_pend periods for these clips (t257, t226). So the selection of eligible clips is
  known; what is new is the stretch values.
- n is small: about 13 'ok' pend10 periods.
