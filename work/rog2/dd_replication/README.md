# Replication of finding 159 (raj-4): real-GAUGE VBench dynamic degree (rog2, task 14)

Goal: check `tools/nv_scoreboard` dynamic degree against VBench's **original** code path, which raj-4 flagged as "not bit-identical"
(they use torchvision `raft_large` C_T_V1 and pyav).

## Independent pieces
- Code: `vbench_dd_orig.py` copies the logic of VBench `vbench/dynamic_degree.py`: cv2 decode, `interval=max(1,round(fps/8))`,
  VBench's `third_party/RAFT` (princeton-vl RAFT) with the original `raft-things.pth`
  (Dropbox models.zip that VBench downloads; sha256 fcfa4125…a7e1), iters=20, InputPadder, top-5% mean,
  `thres=6*min(H,W)/256`, `count_num=round(4*n_sampled/16)`. It adds dd_norm/dd_frac with raj-4's definitions.
- Clips: my own downloads from HF InternRobotics/GAUGE-Dataset (dev, measured only). These are bouncing ball 1-4, pendulum 1-4 and
  slope slider wood task-1 1-4, re-encoded by me with raj-4's stated spec:
  `ffmpeg -vf scale=832:480,fps=24 -frames:v 189 -c:v libx264 -crf 18 -pix_fmt yuv420p`.
- Shared with raj-4: the clip spec and the dd_norm/dd_frac definitions.

## Run
```
python3 vbench_dd_orig.py --vbench <VBench clone> --ckpt raft-things.pth --out dd_orig_matched.json clips/*.mp4
python3 compare_raj4.py dd_orig_matched.json ../../raj-4/nv_scoreboard_real/gauge_real_matched.json compare_raj4.json
```
CPU only: ~100-150 s per clip on 12 threads (i9 laptop).

## Results
See `compare_raj4.txt` (per clip) and the board review of msg 159.
Sensitivity: slope_1 with raj-1's letterbox geometry (832x468 + 6 px pad top and bottom) instead of a stretch:
dd_norm 4.70, dd_frac 0.226, dd_binary 0 (`dd_orig_letterbox.json`; only 1 clip, because the job was stopped to save CPU).
