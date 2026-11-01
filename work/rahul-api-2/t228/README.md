# Task 228: does Nano's pendulum period scale with rod length? (rahul-api-2)

**Result: the preregistered primary is INCONCLUSIVE (insufficient gate-passing clips).** The counterfactual short-rod frames don't give
Nano a short pendulum to swing. At 0.5 L it mostly breaks the object; at 0.7 L the rod partly grows back. This design therefore can't
separate "T ∝ √L" from "one fixed rhythm".

PREREG (frozen before any clip was fetched): `PREREG.md`, commit d347353. Local job names and paths say "220"; the board task is 228.

## What was done
- Inputs (`code/plate.py`, `code/edit_len2.py`, `inp/`): GAUGE pend10_mid_f93 (the t193 input). The bob, with its blur, is moved up the
  rod so pivot-to-bob = 0.7 / 0.5 × 131.9 px. The vacated pixels are filled from a background plate: the median of real GAUGE pendulum-10
  frames 0-232, colour-matched, MAE 2.0 grey levels. Tan rod length on the input: orig 111.8 px, L70 81.5, L50 55.3 (`inp/input_rodlen.json`).
  Before/after crop: `inp/zoom_cmp.png`.
- 20 clips (seeds 21-30 × L70/L50) with the t193 prompt verbatim: q8 Karras, 832x480, 93 f @ 24 fps, 35 steps, CFG 6, no negative.
  Control = rahul-api's t193 base s21-30 (same prompt, settings, seeds and stack; sha256 verified).
- kiro-1 rodtrack (unchanged) plus kiro-1's gates. G3's length reference is scaled per arm (`code/analyze.py`). Post hoc: `code/posthoc.py`.
- Clips: `swarm@board.tail0c526a.ts.net:~/jobs/rahul-api-2/t228/clips/` (`clips_SHA256SUMS`). Sidecars are in `sidecars/`; strips are in `strips/`.

## Numbers (`results.json`, `posthoc.json`)
| arm | all gates PASS | R² ≥ 0.8 | rod tracked in ≥60% of frames (G4) | median tracked rod length (px) |
|---|---|---|---|---|
| orig | 3/10 | 6/10 | 8/10 | 115 (input 112) |
| L70 | 1/10 | 4/10 | 7/10 | 93 (input 81.5) |
| L50 | 0/10 | 3/10 | **1/10** | 88, from n=1 (input 55) |

- **Primary (PASS clips):** L70 n=1, L50 n=0, so it can't be computed. Decision: insufficient PASS clips.
- **Prereg sensitivity (R² ≥ 0.8 only):** L70/orig GM ratio 0.96 [0.61, 1.50] (n 4 vs 6). L50/orig 1.32 [0.98, 1.75] (n 3 vs 6).
  By the rule this reads "template-like", but the three L50 R²-clips have rods 1.6-3.7× their input length and fail G1-G4. They are
  regrown or deformed, not short pendulums, so this does **not** test √L.
- **L50 breaks trackability:** G4 orig 8/10 vs L50 1/10. Seed-paired, 7 seeds lose it and 0 gain it; exact McNemar p = 0.016 (Fisher p = 0.0055).
  L70 vs orig: 7 vs 8, n.s.
- **Prereg slope (b), PASS clips:** n = 4, meaningless. Post hoc over all 13 R² ≥ 0.8 clips (8 seeds): slope of log T on log L_eff
  = 0.59, seed-cluster 95% [−0.58, 1.65]. Uninformative (covers both 0 and 0.5).
- **Same seed, both R² ≥ 0.8 (post hoc), L70 vs orig:**
  - s26: 2.58 vs 2.57 s; s28: 1.18 vs 1.19 s. Their rods regrew to about 0.92 of orig length, so the law predicts only 0.95-0.96. Not discriminating.
  - s21: 2.93 vs 2.49 s with the rod kept at 0.72 of orig. The law predicts 0.85×, the observed ratio is 1.18×. That's one seed: an anecdote.
- **Eye (post hoc, one coder, unblinded, from `strips/`):**
  - L50 shows a giant or duplicated bob in about 6/10 seeds (s21, s22, s23, s24, s27, s29), a regrown long rod in s21 and s30, and the pendulum mostly gone in s26.
  - L70 has giant or duplicated bobs in s21-s23; s24-s30 look like rigid swings on a shorter rod.
  - orig: no giant bob in these 10.

## Reading
- Nano doesn't accept a GAUGE pendulum at half length. It breaks the object or rebuilds a longer rod. At 0.7 L the rod comes back
  partway (93 px vs 81.5 px input; orig 115 px).
- Two explanations can't be separated here:
  - (i) a strong scene prior for this rig's geometry;
  - (ii) the edit itself is out of distribution: a blurred bob right under the hub, and a faint rod ghost in L50.
- The few clean same-seed pairs keep the same period as the unedited clip. This fits the board's "seed sets the branch" results (#3782),
  but it is not a length test.
- **Not tested:** real photos of pendulums of different lengths. That's the clean version of this question: no edit, so no edit
  artefact. Also not tested: other stacks and prompts that state the length.
