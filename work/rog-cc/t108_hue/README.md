# t108 HUE judge: ball3 F vs QT (codex-1 task 108 clips), n=3 seeds
- Clips: codex-1's 6 originals (a100, 93 f/24 fps/35/6/10, no negative, ball3_frame34.png, seeds 1-3), SHA256SUMS.
- Real reference real_ball3_dd34_93f (GAUGE ball3, dedup frame 34 = best f0 MAE match to the t108 input, 4.74) and its trunc36 control. **Added at 09:25 UTC, after the chain launched but before it judged**, so that V1 could run.
- Judge: tools/hue_judge 2B, 16 f, offsets 0/0.5, midq question set (same as task 113). Analysis: midq/analyze_midq.py (summary.*), ratio_audit/refdist_ball3.py (refdist_ball3.json).
