# t331: where does Nano-Phys lose DOVER? (task 331, parent 319; dk2)

No generation. Inputs: the 36 plain/nphys t276 clips scored in t319 (9e92945; sha256 in work/dk2/t319), 12 proxies (work/dk2/t276/proxies), inputs f0_real_*.png.
Scorer: tools/nv_scoreboard/score.py unchanged, `--no_dd --dover_reps 3 --device cuda` (RTX 4060, DOVER.pth sha f4a42c0b).

## Scripts (run from a dir holding ../t319)
1. `build_swaps.py <gen> <proxies> swaps` builds the 2x2 region swap per scene x seed. The corridor mask M is the union of moving pixels (max_t|f_t−f_0|>25 grey, 3x3 open) of the plain clip, the nphys clip and the proxy, dilated 21 px and feathered (σ 6). Cells: pp, nn, np (corridor nphys, bg plain), pn (corridor plain, bg nphys). All 4 are re-encoded identically (x264 crf 12). M covers 20–49% of the frame (swap_meta.json).
2. `analyze_t331.py scores_t331.json swaps/swap_meta.json ../t319/scores_gen.json t331_results.json` gives the main effects: corridor = ½[(np−pp)+(nn−pn)], background = ½[(pn−pp)+(nn−np)]. CIs are an exact 6-scene bootstrap of scene means.
3. `bg_fidelity.py` measures background fidelity vs the input PNG (PSNR, Laplacian-var ratio, luma shift).
4. `tone_ctrl.py` is a control: plain clips with −1.5 grey (ppdark) and Gaussian σ 0.5 (ppblur).
5. `tone_match.py` is a candidate fix: one clip-level BGR offset matching the static background to the input frame, applied to both arms (scores_tm.json).

## Results (fused DOVER; n = 6 scenes x 3 seeds, paired)
| quantity | value [95% CI] | pairs < 0 |
|---|---|---|
| total nn − pp (re-encoded) | −0.064 [−0.077, −0.056] | 18/18 |
| background effect | **−0.045 [−0.053, −0.037]** (70%) | 18/18 |
| corridor effect | −0.020 [−0.026, −0.013] (30%) | 16/18 |
| interaction | −0.008 [−0.017, −0.002] | 11/18 |
| re-encode shift, plain / nphys | −0.019 / −0.026 | |

Aesthetic: 90% background (−0.014 of −0.016). Technical: 67% corridor (−0.0075 of −0.011).
Proxies themselves: DOVER fused 0.475 (real 0.546, nphys output 0.487, plain 0.544). They are mpeg4 at 0.75 Mb/s.
Background vs the input PNG: PSNR proxy 41.3, plain 34.4, nphys 33.7 dB. Laplacian-var ratio 0.91 / 0.82 / 0.80. Luma shift −1.8 / −2.0 / −3.5 grey.
DOVER sensitivity controls on plain: −1.5 grey gives −0.026 (18/18), σ 0.5 blur gives −0.077 (18/18).
Tone match: nphys − plain −0.062 [−0.076, −0.053], so no recovery (gain +0.002), and luma is NOT the cause.

## Reading
Most of the cost is in the static background, which neither arm moves. It is not tone. The remaining candidate is a loss of fine detail or texture, a subtle change: −0.7 dB and −2% Laplacian variance vs plain. DOVER is that sensitive: a 0.5 px blur costs more than the whole drop. That fits whole-frame noising of a proxy with no region mask (ProxyUp §5.4, TTM Table 3).
Fix to test (needs GPU): region-wise noising. Start the background from fresh noise (plain), or from a higher σ, and use the proxy latent only inside the corridor (ProxyUp RLN, TTM dual-clock).
Limits: one rig, 6 near-fps takes, shared seeds. The swap is a counterfactual attribution through a learned metric, and seams are in the interaction term. Re-encoding shifts absolute DOVER by −0.02 to −0.03, so compare only within the re-encoded set.
