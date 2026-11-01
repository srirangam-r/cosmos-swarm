# t226 P (pendulum) result: frozen pipeline, 14:26 UTC 2026-11-01

Frozen code: measure_t226.py / analyze_t226.py (d41ff48), run by post_t226.sh on all 72 clips -> measures.json, results.json,
analyze_t226.log; explore_t226.py -> explore_results.json; sens_a6k.py (Amendment 7) -> sens_a6k.json.
Input pend10_mid_f93 (real GAUGE frame), 93 f @ 24 fps, 35 steps, CFG 6, Karras (flow_shift ignored), noise.device=cpu requested;
s101-104 a6k, s105-106 a100 (a100 may not apply CPU noise: rahul-api-2 #5058; pairing within seed holds, one stack per seed).

## Preregistered decisions
- P still (ME_roi, still - neutral, paired by seed): mean -2.30 [-5.94, +1.33], sign-flip p 0.22, 1+/5-, sd_neutral 4.11
  -> NOT DETECTED (not equivalence).
- P fast (log period rec_period v1): INCONCLUSIVE. rec_period reads only 3/24 P clips (base s102, still s101/s102); 0/6 neutral
  and 0/6 fast clips are readable (flag shallow). w025 window: same 3 clips.
## Reported, not decisive
- ME_roi variance split (4 arms x 6 seeds): seed 0.55, prompt 0.185, residual 0.265.
- ME_roi: still-base -0.77 (p 0.34); fast-neutral +1.02 (5+/1-, p 0.16); fast-base +2.56 (5+/1-, p 0.06); base-neutral -1.54 (3/3).
- ME_full (whole frame): fast-neutral +0.94 [-0.15, 2.03], 6+/0-, p 0.031; fast-base +1.24, 6/0, p 0.031; still-neutral -0.46 (1/5, p 0.125).
- Real pend10 continuation (same frame onward): ME_roi 4.28, ME_full 1.00, period 1.171 s (ok). Nano neutral ME_roi 4.7-15.1 (median 7.2).
- a6k-only (s101-104, n=4, descriptive): still-neutral ME_roi -1.04 (1/3); fast-neutral +1.24 (4/0, p 0.125). Signs kept.
## Eye QC (analyst, NOT blind; the analyst is not a coder): qc/psheet/P_<arm>.jpg (rows = seeds, ROI crops every 6 frames).
- P_still: the rod swings in 6/6 seeds, often to near horizontal, with rod doubling. All arms swing large and irregularly.
## Pending: P still -> STILL via blind codes (3 external coders, strips 74a7a45), McNemar per Amendment 3/6.
