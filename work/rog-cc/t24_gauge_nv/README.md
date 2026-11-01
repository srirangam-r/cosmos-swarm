# Task 24: NVIDIA-scoreboard items (DOVER, VBench DD) on the blinded GAUGE-ball eval arms (rog-cc)

Predeclared in work/rog-cc/hue_t24/PREREG.md, addendum A2. The scorer is blind: only `<6-hex>.mp4` files are pulled
from GB10 ~/jobs/rahul-3/eval_clips/, never sidecars or the key.

- `gauge_nv_watch.py ROOT [hours]`: polls every 10 min, scores new clips with tools/nv_scoreboard/score.py
  (`--device cuda --dover_reps 3`) under a GPU flock shared with the HUE judge watcher.
- Real reference: GAUGE real ball1-4 (dev, measure only), `ffmpeg -vf scale=832:480,fps=24 -frames:v 93 -c:v libx264 -crf 18`.
- `analyze_gauge_nv.py gauge_nv.json real93.json KEY`: paired (prompt, seed) arm − base, t one-sided 95% bound, bootstrap,
  PROPOSED margins (DOVER fused 0.02, dd_binary 0.10, dd_norm and |dd_norm − real| gap 15% of base dd_norm).
- Results land in res/ once the key is posted.
