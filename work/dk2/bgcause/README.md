# bgcause: what outside the pendulum box makes Nano-Phys (t276 nphys) lose DOVER? (dk2, task 337 side-analysis)
No generation. Inputs: the 36 t276 plain/nphys clips (same as t319/t331/rev6767), dk1's tight box (rev6767 swap_meta.json) and
per-clip outside-box DOVER effect (rev6767 bg_motion.json).
1. `bg_features.py` -> bg_features.json: outside-box features, nphys - plain (same seed), and their correlation with the per-clip bg effect.
   Result (n=18, 6 scenes x 3 seeds): HSV saturation vs frame 0: plain -5.0, nphys +5.5 (delta +10.5, 18/18 >0), r = -0.69 (within-scene -0.73).
   8x8 block-edge ratio: plain 1.13, nphys 1.27 (18/18 higher), within-scene r -0.75. Luma -1.9 grey (18/18), r 0.81. Contrast ratio -0.9%, r 0.83.
   Temporal residual (grain) 0.43 vs 1.07, r 0.00. Laplacian ratio -2.3%, r 0.46. Luma was already ruled out causally (t331 tone match, +0.002).
   `proxy_feats.py`: the proxy mp4 is very blocky (block-edge 1.73-2.04, mpeg4 0.75 Mb/s) but slightly LESS saturated than frame 0 (-1.3..-2.7),
   so nphys' saturation rise is produced by Nano, not copied from the proxy; the blockiness is plausibly inherited.
2. `satswap.py`: causal test of saturation. Lossless (x264 qp0) cells per pair: pp, nn, nS (nphys S scaled by g = S_plain/S_nphys), pS (plain S / g).
   HSV round-trip closes ~70% of the S gap (satswap_meta.json). Scored: score.py --dover_reps 3 --per_clip_seed --no_dd (4060).
3. `analyze_sat.py` FROZEN readout + decision rule (see docstring), committed before any score.
