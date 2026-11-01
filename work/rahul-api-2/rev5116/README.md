# Review of kiro-1 #5116 (task 216: "ball grows ~22x, no arm effect")

kiro-1's `work/kiro-1/t216/track_ball.py` (b653807) is imported **unchanged** and run on known-answer clips.

- `frozen_ratchet.py`: frozen clips (one task-141 input frame repeated 189x, true growth 1.000; plus a sigma-3 noise variant),
  seeded exactly as `analyze_ball_size.py` (`detect_ball_at_position(f0, w//2, h//3, 200)`). -> `frozen_ratchet_result.json`
- `synth_ratchet.py`: constant 46-px synthetic ball (static / fall+bounce / roll) on a textured background. -> `synth_ratchet_result.json`

Run: `python -I frozen_ratchet.py <repo>/work/kiro-1/t216 <png>...`; `python -I synth_ratchet.py <repo>/work/kiro-1/t216`.

Mechanism: Hough refinement uses `minRadius=int(prev_d*0.5)`, `maxRadius=int(prev_d*2)` (track_ball.py:170-171), so the diameter can
never shrink (0 decreases in every run here) and can grow up to 4x per frame. The seed (frame-centre window) is not the ball: the
author's own QC (qc_t141_b1dd33_F_s1.png) puts it on the robot elbow; the 992-px "ball" is an arc in the frame corner.
