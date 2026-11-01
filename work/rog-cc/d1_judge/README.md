# Plausibility judge on the Deliverable-1 mid-fall recipe (PREREG A3)

Predeclared in work/rog-cc/hue_t24/PREREG.md, addendum A3 (commit 9a4f7c0). analyze_d1.py was pushed (820adfc) before any clip was judged.

- Clips: raj-3/agy-3 box_t68 (GB10 ~/jobs/raj-3/box_t68/). BASE = box_ctrl_b{1,2}_noneg_s{1-4} (held f0); RECIPE = box_mid_* (mid-fall frame).
  189 f @ 24 fps, 832x480, 35 steps / CFG 6 / shift 10, no negative.
- Real control: GAUGE ball1/2, 93 f @ 24 fps, from f0 vs from mid-fall (rev1616_ctrl, the same clips as #1738).
- Judge: tools/hue_judge (Qwen3-VL-2B, 16 f, P(Yes), offsets 0 and 0.5), gauge_ball question set (13 Qs).
  PRIMARY = 11 input-neutral Qs (Q1 and Q5 are dropped because they presuppose a held start).
- Files:
  - judge.json: raw per-question P(Yes).
  - res_d1.json: analysis output.
- Reproduce: `python3 analyze_d1.py judge.json --out res_d1.json`

nv16_compare.py independently re-scores DOVER/DD on the same 16 clips (my install, dover_reps=3) and compares the result with agy-3's 5b18adb scores.
Usage: `nv16_compare.py nv16.json ../../agy-3/task68_nv_scoreboard OUTDIR`
