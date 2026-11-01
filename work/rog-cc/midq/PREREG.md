# midq: does the QT timed-settle prompt lose plausibility, or does the judge's question set penalise settling?

Predeclared by rog-cc on 2026-11-01 ~08:40 UTC. This was committed **before any clip below was judged by me.**
Disclosure: ro-1's #2577 results (gauge_ball set) were already public. The mid-fall items below were written knowing that Q1, Q2 and Q5 drive the QT−F drop and that Q6 does not discriminate (#2593).

## Clips
ro-1 cause_v5 (GB10 ~/jobs/ro-1/cause_v5/): F and QT for ball1 s1-5 and ball2 s1-3 (8 pairs), QS ball1 s3-5, and real_ball1_dd32_93f. Settings: 832x480, 93 f, fps 24, 35/6/10.

Controls I build (make_controls.sh):
- `trunc36_<stem>`: the first 36 frames (1.5 s) of every F, QT and real clip. By then QT is still bouncing.
- `static_<stem>`: f0 of F s1 for ball1 and ball2, and of the real clip, repeated for 93 f at 24 fps (3 clips). The ball hangs in mid-air for 3.9 s. F and QT share a bit-identical f0 (MAE 0.0), and the real f0 is 1.9 MAE from it, so it is not inverted.

## Judge
tools/hue_judge, Qwen3-VL-2B, 16 f, short side 256, offsets 0 and 0.5 averaged. Score = P(Yes); negated items are scored as 1 − P(Yes).
Questions: midq_questions.json. q1-13 are gauge_ball verbatim. q14-22 are the new mid-fall items, and q17, q19 and q20 are negated twins.

## Primary
- **mf_physical** = q3, q4, q13, q15, q16, q17−, q18, q19−, q20−, q21.
- **mf_overall** = mf_physical plus q7-12, q14 and q22.

The contrast is QT − F, paired by (input, seed), n = 8, with a t CI90 (df 7). Non-inferiority holds if the CI90 lower bound is above −δ. The margins are δ 0.03 for overall and 0.04 for physical. Those values were human-approved for the HUE judge in #1306; carrying them over to this new question set is my extension.

## Validity (predeclared; if V1 fails, the mf result is reported as uninformative)
- V1: the real clip's mf_physical minus the mean of the 3 static clips must be ≥ 0.10. A set that can't tell a ball hanging in mid-air from a real fall can't judge QT.
- V2: twin sums P(Yes) q16+q17 and q18+q19, reported as is. A sum near 2 means yes-bias, near 1 means the judge is reading the video.

## Secondary
- gauge_overall, gauge_physical and gauge_Q125 QT − F. This is a re-run of #2577 using the same tool, so it is NOT independent code.
- **J-S test (scout-1 #2602):** QT − F on the mean of Q1, Q2 and Q5, full clip vs trunc36. J-S predicts the Δ shrinks toward 0 once both clips are cut to 1.5 s, while both are still bouncing.
- QS − F (n=3).
