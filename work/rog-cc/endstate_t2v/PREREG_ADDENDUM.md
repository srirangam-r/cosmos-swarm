# Task 133 PREREG addendum (EXPLORATORY), written 10:15 UTC, before any late-motion number was computed

The PREREG says "Not tested here: whether R improves physics on these prompts". It still isn't: there is no validated physics metric for free-form T2V. But Raj #2930 req. 2 asks for "the numbers for whatever the recipe targets". Rule R targets late motion ("come to rest ... staying completely still"), so I add one EXPLORATORY readout, `late_motion.py`:

- **Per clip:** lateM = the mean whole-frame |Δgrey| over frame pairs 60-92 (the last ~1.4 s). earlyM = the same over pairs 1-32. ratio = lateM/earlyM, which normalises per scene.
- **Analysis:** unit = prompt (mean of seeds 1-3). Paired R−base, N−base and R−N, each with a t 90% CI; for all prompts, physics_* and robot_*.
- **Reading:** R cuts late motion if R−base lateM < 0 with CI90 upper bound < 0 AND R−N < 0 likewise. If only R−base is negative, any suffix does it.
- **Caveats, stated in advance:**
  - Whole-frame Δgrey counts camera motion, lighting flicker and artifacts as "motion". It is not a rest detector, and it has not been through the planted cases (no planted case covers settling).
  - raj-api-3 (#3036 #3059) used a similar crude metric on 4 non-ball scenes with a timed clause and found nothing resolved.
  - Robot prompts aren't about falling objects, so R should matter less there. That is a weak built-in check.
  - Disclosure: I have seen three seed-1 QC sheets (physics_049, physics_163, robot_055; commit 1a636aa), but no motion number.
- **Before any descriptive claim:** a blind eye check on a subset (R vs base, labels hidden).
