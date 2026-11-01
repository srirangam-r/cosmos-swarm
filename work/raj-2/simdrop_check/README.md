# raj-2: independent check of rahul-3 sim_drop v1 real-g clips (task 11 ask, msg 239)
Data: 21 clips, every 21st of ~/jobs/rahul-3/simdrop_v1/real/train on the GB10 (files.txt), copied at 03:12 UTC. Scale is meta px_per_m only.
The fit and the y track never use the ground-truth tracks. In run_seeded.py the frame-0 ball position (centers_px[0]) is the click seed only.
- firstfall v1 (referee PASS msg 264), seeded: g/g_true = 1.009 ± 0.010 (SE; sd 0.042; median 1.002), n=18 of 21 flag=ok, 17/18 within 10%.
  The 3 non-ok clips: 2 weak (9.34, 10.46) and 1 no_free_fall (00105, hand holder).
- firstfall auto-seed (run.py): the trk.blobs auto seed lands on the holder in most clips, so only 4/21 are ok (1.015 ± 0.011).
- realball v1.1, blind (trk.blobs largest change blob): 2/21 within 10%, median ratio 0.015. It works only on holder='none' clips (00063 9.63, 00126 8.79, 00378 10.26).
  On every hand/gripper clip it tracks the retracting holder.
=> The clips do encode ~9.81 m/s². But the planted-passing trk.blobs tools (realball, trk_ballfall v5) cannot measure them, and won't measure
   Cosmos outputs on similar scenes either, so evaluate any sim_drop LoRA with a seeded tracker (firstfall/samball) and check the QC (qc/).
