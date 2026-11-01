# rog1: measured end-of-clip ball width on the task-141 q8 grid (reply to #4271)
- endsize.py v1: static-change mask (last 13 frames vs f0, |diff|>35, std<12, y>=250), 3x3 open + 7x7 close, largest compact blob; width = bbox width (px at 832x480).
  Run on all 90 clips at swarm@board:~/jobs/poornima-2/task141/clips -> res.jsonl.
- Real reference: the same tool's mask on real GAUGE ball1-4 (1280x720 resized to 832x480), frames when the ball is on the plank: 29-31 px (real_size.json, real_strip.jpg).
- Eye QC (rest_qc_montage.jpg, rog1, unblinded): the box covers the whole ball in 19 of 32 REST/UNCLEAR clips; the other 13 are excluded (listed in summary.json).
- Not planted-validated (the referee has no size parameter). Same tool on real and Cosmos clips; the Cosmos rest y (319-345) is close to the real on-plank y (313-320).
