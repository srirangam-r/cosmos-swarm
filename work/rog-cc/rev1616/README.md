# Review of #1616 (agy-3, task 68): NVIDIA scoreboard before/after for mid-fall conditioning

Re-analysis of agy-3's per-clip score JSONs (commit 5b18adb, work/agy-3/task68_nv_scoreboard/).
It does NOT re-score the video: the 16 clips are on agy-3's machine (raj-3/brev_box/out) and not on GB10.

`python3 rev1616.py [path/to/task68_nv_scoreboard]` writes rev1616.json.

What it computes:
1. MF/MC with the same algebra as tools/nv_scoreboard/motion_fidelity.py (ddof=0, zero policy, ref dd=0):
   - MC = var/(var+mean^2) is a PENALTY: MF = (1-|dd_gen-dd_ref|)*(1-MC).
   - It runs over all 16 choices of 3-of-4 seeds per ball, not only seeds 1-3.
2. Paired recipe-baseline deltas on DOVER fused/technical/aesthetic, dd_norm and dd_binary over 8 (ball,seed) pairs.
   It gives t(7) one-sided 95% bounds and per-ball means. Balls are the real cluster, so n=2 scenes.
