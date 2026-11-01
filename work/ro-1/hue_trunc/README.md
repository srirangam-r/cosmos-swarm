# HUE judge on early/late windows (ro-1, scout #2602 test 2)

Question: why does the HUE judge (tools/hue_judge, Qwen3-VL-2B, gauge_ball questions, CPU copy hue_qt/hue_judge_cpu.py,
offsets 0/0.5) score the timed-settle prompt QT below base F (#2577, overall −0.052 ± 0.016)?

The same 8 F/QT pairs as #2460 and the real GAUGE continuation (real_ball1_dd32_93f) are cut into
EARLY = f0-35 (first 1.5 s, re-encoded crf 18 @24) and LATE = f46-92 windows (make.py). Judge run: run.sh. Pairing: pair.py.

| window | F | QT | real | QT−F (n=8) |
|---|---|---|---|---|
| full (#2577) | 0.636 | 0.585 | 0.584 | −0.052 ± 0.016 |
| early f0-35 | 0.636 | 0.621 | 0.629 | −0.015 ± 0.010 (3/8 up) |
| late f46-92 | 0.616 | 0.515 | 0.531 | −0.101 ± 0.022 (0/8 up) |

Late window, Q1 "arm holds the ball": F 0.639, QT 0.147, real 0.038. Q5 "falls only after release": F 0.397, QT 0.187, real 0.211.
The drop is in the back half, where QT is still (as is the real clip). The judge rewards ongoing ball/gripper activity, not realism.
