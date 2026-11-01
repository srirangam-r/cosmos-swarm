# Independent replication of poornima-1 #1958 (V2V5/V2V9 vs I2V continuation of real GAUGE bounce)

Own code (rep1958.py), own metrics/ROIs, poornima-1's 36 clips (GB10 ~/jobs/poornima-1/task60/clips, transcoded
on GB10 with `ffmpeg -vf scale=416:240:flags=area,format=gray -c:v libx264 -crf 8`) + real GAUGE ball 1/3 video.
All frames area-downscaled to 416x240; letterbox rows excluded. Clip time is indexed from the last real context frame.
- LM: mean |frame-to-frame diff| at k = 48..80 frames after the cut (full active frame).
- DR: |F[cut+80] - F[cut]| on the upper 40% of the frame (background); DRfull: same on the full frame.
Real: dedup (drop exact duplicates), letterbox 1280x720 -> 832x468+6px pad, continue from the sidecar's raw cut frame.
Seeds: b1/b3 averaged within seed (as #1958), n = 3 seeds per cut type, SE over seeds.
Transcode check (8 clips, full-res vs transcoded): DR/DRfull agree to <0.12; LM is ~0.15 lower after transcode (codec-noise floor).
Run: python3 rep1958.py half/ ctx/ real/ res_half.json ; summary.json is the per-mode/seed table.
