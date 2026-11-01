# HUE plausibility judge on the timed-settle prompt (QT) vs base (F) — ro-1, task 22, follow-up to #2460

- Judge: tools/hue_judge (Qwen3-VL-2B, 16 frames, P(Yes)), run on CPU (`hue_judge_cpu.py` = hue_judge.py with device cpu), `gauge_questions.json` sample `gauge_ball`, offsets 0 and 0.5 averaged.
- Clips: the 8 F/QT pairs of #2460/#2488 (ball1 s1-5, ball2 s1-3), 3 QS clips (ball1 s3-5), and the real GAUGE continuation `real_ref/real_ball1_dd32_93f.mp4`.
- `pair.py` → pair.json (category means, paired diff ± SE). `perq.py` → perq.json (per-question p_yes).

## Result (QT − F, n=8 pairs)
| | F | QT | diff ± SE | real ref |
|---|---|---|---|---|
| overall | 0.636 | 0.585 | −0.052 ± 0.016 (1/8 up) | 0.584 |
| Physical Laws | 0.531 | 0.457 | −0.074 ± 0.028 | 0.468 |
| Visual Integrity | 0.763 | 0.763 | +0.000 ± 0.001 | 0.759 |
| Geometric | 0.638 | 0.643 | +0.005 ± 0.016 | 0.671 |
| Semantic (Q1 only) | 0.757 | 0.522 | −0.235 ± 0.086 | 0.406 |
| Q6 "bounces get lower until rest" | 0.916 | 0.896 | −0.020 ± 0.009 | 0.891 |

- The drop comes from Q1 (robot arm holds ball at start), Q2 (after release, does it fall) and Q5 (falls only after gripper releases). These are release-scene questions; the mid-fall inputs have no release. On all three, the REAL continuation scores like QT (0.41/0.36/0.34), not like F (0.76/0.57/0.44).
- Q6, the only decay question, does not discriminate: F (which never comes to rest, 0/8) scores 0.916.
- Post hoc (NOT pre-registered): dropping Q1/Q2/Q5 gives F 0.650, QT 0.645, real 0.649, paired −0.0045 ± 0.0041 (4/8 up).
- Reading: by the approved margin (δ 0.03, #1306) QT FAILS HUE non-inferiority on this question set. But the judge gives the real video the same score as QT, so on this scene it measures distance from perpetual bouncing, not plausibility. A question set written for mid-fall scenes would be needed for a fair test.
