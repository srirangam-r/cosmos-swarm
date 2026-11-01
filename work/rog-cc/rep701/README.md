# Independent replication of #701 (rahul): base Nano robot FD vs a frozen frame, per view

`rep701.py` was written from the text of #701 only (not from robot_pred/score_seeds.py). It scores the 12 base528 gens
on GB10 `~/jobs/rahul/gens_base528/` (7 DROID ep-48330 items, 5 of them with seeds 0 and 1) against
`~/jobs/rahul/devset/<item>/real_future.npy[:, :528]`. Gen frames 1-16 are compared with real frames 0-15.
- Views: wrist rows 0-360; ext1 rows 360-528 x cols 0-320; ext2 rows 360-528 x cols 320-640; all = full 528x640.
- Frozen baseline: gen frame 0 held for 16 frames.
- Metrics: LPIPS-alex (lpips 0.1.4) and PSNR, both per frame and averaged.
- Statistics: per item, average over seeds, then mean ± SE over items.

Run: `python3 rep701.py <devset> <gens> --out rep701.json` (CPU, ~1 min). Result: rep701.json.
