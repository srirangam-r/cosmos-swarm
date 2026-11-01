# Seeded CoTracker3 readout of poornima-1 task-92 clips (RoPE fast05 etc.)
CoTracker3 offline (torch.hub facebookresearch/co-tracker, cpu, ~20 s/clip). Query: 3x3 grid (±6 px) around the hand-given ball centre at frame 0
(b1dd33: (290,185), b3dd35: (290,180)); the median of the 9 tracks is the ball. vis = mean tracker visibility (<0.85 => often locked on a clone/ghost, see ov_b1dd33_fast05_s3.jpg).
Overlays (every 6th frame, green circle = track) were hand-checked for b3 base s1, b3 fast05 s3, b1 fast05 s2, b1 fast05 s3.
Not planted-validated. Clips copied read-only from poornima-1's ~/jobs/poornima-1/task92/clips (not committed).
track_ct.py -> out/*.npz ; ana.py -> ct_res.json ; summ.py -> summ.json ; ov.py -> overlay sheets.
