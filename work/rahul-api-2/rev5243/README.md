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
