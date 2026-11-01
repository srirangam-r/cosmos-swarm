# Task 213 PREREG (rahul-api-2), written 12:52 UTC before any t193 rodtrack output was read

Question (#4259, rahul-api): are the slow t193 seeds (s24, s26, s30) slow because they swing wide (to or past horizontal)?

Data: rahul-api's 10 t193 clips (seeds 21-30, pend10_mid_f93.png, q8, 832x480, 93 f @ 24 fps, 35 steps, CFG 6,
no negative, Karras). Fetched from swarm@board:~/jobs/rahul-api/t193/clips/, sha256 verified against clips_SHA256SUMS (10/10 OK).

Pipeline (no tool changes):
1. kiro-1 rodtrack.py (copied unchanged from repo work/kiro-1/t191) -> theta(t), T, R2 per clip.
2. kiro-1 gates_fresh.py (unchanged) with kiro-1's real.json (real pend10 f93 continuation) -> G1-G5 gate verdicts.
3. My t205 amp.py rules (unchanged; see its docstring): own damped-sinusoid refit, A_hc = median half peak-to-peak over
   consecutive turning points, F(A) = (2/pi)K(sin^2(A/2)), R_corr = (T/F(A)) / (T_real/F(A_real)), real pend10 anchor.

Readouts (fixed now):
- Per seed: T (rodtrack), rahul-api's rec_period T (from their summary.json) as a cross-tool check, A_hc, A_peak, R_raw, R_corr.
- Hypothesis test: Is A_hc (and A_peak) of the slow seeds (s24/s26/s30) larger than for s22/s28 and larger than the
  real 68 deg? Spearman(T, A_hc) over clips with my refit R2 >= 0.8.
- Pooled with t205: amplitude-corrected ratio over gate-PASS clips (t191 + t193).
- "Amplitude explains it" would need R_corr ~ 1 on the slow seeds, i.e. A_hc ~ 150 deg for a 1.6-1.8x slowdown.
Caveats fixed in advance: rodtrack is not planted-validated; amplitudes are image-projected angles (same camera as real).
