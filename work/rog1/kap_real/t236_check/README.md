# rog1 check of ro-agy1 #4763 (task 236), pack author
t236_check.json rows: cut_id, label, v0 prediction, v0 shift_ratio, v0 max_shift_px (832 px, 3 frames end-13/-7/-1), v0 median diameter px,
rog1 tracker displacement on the same 3 frames (832 px), rog1 tracker max pairwise displacement over all 13 frames end-13..end-1 (832 px), n tracked frames.
The rog1 tracker (kap_real/code/track.py) is independent of rest_candidate.py: thresholded dark-blob diff at 1280x720, scaled by 0.65.
Frames mapped through the cut's dedup index (cut.py). Neither tracker is planted-validated.
