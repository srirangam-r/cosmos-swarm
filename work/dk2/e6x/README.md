# E6 period cross-check with a referee-PASS tool (dk2, task 258)

E6 (work/raj-noise/e6) and E6-W (work/dk2/e6w) read periods with tools/pend_acf. pend_acf got 4/4 planted pendulums within 5%, but it has
no formal referee verdict, because the rule needs at least 10 estimates. tools/trk_ballfall/measure_pend.py v1 has a referee PASS (20/20).
`xcheck.py` runs both tools on every clip, at --fps 24 (periods in frames, as in analyze_e6), so the E6 and E6-W decisions can be
stated with a planted-pass method behind them.

## Frozen rule (committed before any stage B, C or E6-W generated clip exists)
1. Agreement: among clips where pend_acf flag == ok and measure_pend returns a period, the share with |P_mp/P_acf - 1| <= 0.05.
   measure_pend's own flag is reported but does not gate. On noisy Nano tracks it says 'check' because R2 < 0.8 (zero-crossing jitter),
   even when its fitted period agrees with pend_acf.
2. Re-decision: recompute analyze_e6's per-arm median ratio and within-10% count, and analyze_e6w's f (tlo primary), using P_mp in
   place of P_acf. For the real reference, use measure_pend on real_XX. A target whose real clip is not 'ok' on measure_pend is dropped
   from this variant: real_13 reads 80 f, 'check', so t13 is dropped.
3. The E6 or E6-W conclusion is "planted-backed" if the decision category is the same under (2). If it is not, I report both and treat
   the result as tool-dependent.

## Results so far (no B, C or W clips yet)
- real_01..20 (codex-api-4 t8): measure_pend ok 19/20. mp/acf median 1.005 [0.997-1.010 over the 19]. real_13 fails on measure_pend.
- E6 stage A recon (A_rec01-09) plus the E6-W warped donors realw_* (8): 17/17 within 5%, median 1.005, range 0.985-1.026.
  measure_pend ok 12/17. The 5 'check' are recon clips with R2 0.6-0.8.
- Known answer for the warped donors: 20.6 f expected. measure_pend reads 20.41-20.70, pend_acf 20.22-20.70.
Files: real.json, stageA_n9.json.

## Rule 2/3 as code (committed before any B/C/W clip was visible to dk2)
- `redecide.py`: E6 arm categories ("real clock" if |median P/P_real - 1| <= 0.10, else slower/faster) and E6-W f decisions, computed
  with pend_acf and with measure_pend. Verdict "planted-backed" when they match, otherwise "tool-dependent". Tested on synthetic rows only.
- `run_q8.sh DEST`: fetches Raj's q8 outputs (E6 and E6-W were generated on raj-q8, #5525; dk2's H100 copy was stopped as a duplicate) and runs
  xcheck.py and redecide.py.
