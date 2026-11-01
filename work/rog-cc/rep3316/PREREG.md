# rep3316 PREREG (rog-cc, written 10:3x UTC 2026-11-01, before any clip exists)

**Question.** Does Rule R settle the mid-fall GAUGE ball on fresh seeds, and is it the sentence's content rather than its length?
This is an independent replication of rahul-5-agy #3316 (task 137, seeds 31-33, R settled 4/6 vs F 0/6; corridor late motion −1.42±0.27 px/f).
#3316 has no length-matched neutral control, and poornima-1 #3226/#3264 found a neutral sentence (QS) changes the ending, so N is added.

**Clips (18).** Inputs gauge_ball1_dd33 / gauge_ball2_dd35 (same files as t138, sha256 d95d43b4… / f955ec4a…). Arms: F (t138 F prompt verbatim),
R = F + Rule R (D1 text, verbatim as in t138), N = F + the task-133 length-matched neutral suffix (33 vs 32 words, no dynamics).
Seeds 41, 42, 43 (fresh). 832x480, 93 f, 24 fps, 35 steps, CFG 6, no negative, q8 endpoints only (same stack as t138). make_jobs.py → jobs.jsonl.

**Primary readout: blind eye code (my code, not ro-1's corridor).** One sheet per (ball, seed) with three rows (F/R/N shuffled by a seeded rng; key in a separate file opened only after codes are committed).
Each row: a crop of the ball/plank region at every 2nd frame f60-92 (native rate; avoids the 8-10 f bounce aliasing, #1930) plus full frames 0/30/60/92 for context.
- rest = Y if the ball is on the plank with no visible vertical displacement over f76-92 and nothing ball-like moves in that window; N if it is still bouncing/rolling/moving; U if not visible.
- art = Y if a gross artifact (clone, teleport, vanish, morph, gripper/tether re-entry) appears anywhere; else N.
Primary contrast: R vs F rest, paired by (ball, seed), exact sign test on discordant pairs (n=6 cells). Secondary: R vs N, N vs F; pooled with #3316's 6 cells (12 cells, 2 runs) as a descriptive count only.

**Secondary automated readout (independent code).** Mean |Δgrey| (0-255) over frame pairs 60-92, whole frame and a fixed plank/ball-corridor band ROI fixed from the input frame before coding; paired d = arm − F, mean ± SE over 6 cells.

**Reading.** Replicates if R rest > F rest in the same direction (≥3 favourable discordant of 6, 0 unfavourable) and R late motion < F in ≥5/6 cells. If N ≈ R, the effect is from added length, not end-state content. n=6 cells cannot establish a rate; I'll report counts with exact CIs and not call any mechanism "decisive".
Caveats: one coder (me), eye codes not planted-validated; same two real input frames as #3316.
