# Independent replication of rahul's #1009 (Nano DROID forward dynamics follows the action input, per view)

`rep1009.py` was written from the #1009 text (not robot_pred/compare_swap.py). Gens: rahul's 40 clips on GB10
`~/jobs/rahul/gens_swap5/<item>/gen_{base528,swap5}_seed{0,1}.mp4` (DROID ep 48330, 10 items, swap = actions of item (i+5)%10;
sidecars: 640x528, 17 f, 15 fps, 30 steps, cfg 1.0, shift 10, forward_dynamics, concat_view). Real: devset real_future.npy[:16, :528].
Frames 1-16 compared (frame 0 = shared conditioning frame). LPIPS-alex (lpips 0.1.4) + PSNR; item-level mean ± SE, n=10.
Addition beyond #1009: `d_act_cross` pairs swap_s with base_{1-s}, so the action term and the seed floor both carry seed noise.
Run: `python3 rep1009.py <devset> <gens> --out rep1009.json` (CPU, ~2.5 min on 12 threads). Result: rep1009.json.
