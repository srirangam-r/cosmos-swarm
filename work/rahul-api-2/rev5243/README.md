# Review of rog1 #5243 (task 255 E1: Bridge forward dynamics, action vs seed) — rahul-api-2

Design frozen in this file and in review.py BEFORE review.py was run on any clip. I have read rog1's e1.json summary
(the numbers in #5243) but not their per-clip values.

Independent code (opencv + numpy; no LPIPS, no torch, no PyAV), same 144 published clips
(work/rog1/t255/clips, own/swap x s1-3 x 24 Bridge clips) and the same real futures (tools/robot_pred/devset_bridge,
real.mp4 frames 1..16 vs generated frames 1..16, both 5 fps, 256x256).

Question 1 (replication): does the action effect exceed the seed effect under pixel metrics?
 D_seed = mean distance between seeds within an arm (3 pairs x 2 arms); D_action = mean OWN vs SWAP distance at the
 same seed (3 seeds); ratio = D_action / D_seed per clip; clip-bootstrap 95% CI of the median ratio (5000, rng 0).
 Metrics: (a) RMSE on float gray [0,255] over the whole frame; (b) 1 - SSIM (gray, 11x11 Gaussian sigma 1.5,
 standard constants), whole frame; (c) RMSE inside the MOTION MASK (below).
Question 2 (the new angle): is "correct actions barely beat a static frame" a whole-frame dilution effect?
 Most Bridge pixels are static background, so whole-frame metrics are dominated by pixels a static copy gets right.
 MOTION MASK per clip = pixels where max_t |real_t - real_0| (gray, 3x3 Gaussian blurred) > 25, dilated 7 px;
 needs >= 1% of the frame, else the clip is skipped for (c).
 E_own, E_swap, floor (= real frame 0 repeated) distances to the real future, per metric.
 Report: floor - E_own (clip mean +/- SE, sign count), E_swap - E_own (same), and the ratio (floor - E_own)/floor.
Decision wording: "replicated" if the median-ratio CI lower bound > 1 under >= 2 of the 3 metrics and E_own < floor in
the same direction as #5243; "challenged" if the masked metric reverses either conclusion; otherwise "partly".
Known-answer checks inside review.py: identical clips -> distance 0; real future vs itself -> E 0; mask of a
static repeat -> empty.

## Results (review_result.json, frozen code; posthoc_ssim.json = post hoc, after seeing the frozen result)
| metric | median D_action/D_seed [95% CI] | action>seed | E_own vs static floor (floor - E_own, clips E_own better) |
|---|---|---|---|
| RMSE whole frame | 1.33 [1.19, 1.44] | 22/24 | +5.39 ± 1.44 gray (17%), 20/24 |
| RMSE motion mask (median 34% of frame) | 1.39 [1.20, 1.54] | 22/24 | +11.1 ± 2.0 gray (21%), 21/24 |
| 1 - SSIM whole frame | 0.92 [0.81, 1.02] | 9/24 | -0.049 ± 0.008 (Nano WORSE than static), 3/24 |
Swap - own (wrong actions raise error): RMSE +9.5 ± 2.1 (20/24), masked +11.5 ± 2.3 (20/24), dSSIM +0.033 ± 0.012 (17/24).
Frozen rule -> "replicated" (CI > 1 on 2/3 metrics incl. the masked one; masked metric keeps E_own < floor).
Post hoc: Nano's re-rendered frame 0 is already 0.06 1-SSIM from the real frame 0 (encode/decode loss), but even against
a VAE-matched floor (Nano's own frame 0 repeated) SSIM still prefers the static frame: -0.025 ± 0.007, 5/24.
RMSE vs the VAE-matched floor: +5.5 ± 1.4 (20/24); masked +11.2 ± 2.0 (22/24).
