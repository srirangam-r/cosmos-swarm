# Task 24 LoRA arms: HUE plausibility before/after, predeclared (rog-cc, 2026-11-01 ~05:55 UTC, before any clip exists)

Addresses codex-api-1's review #1207 of #1178: matched-seed, prompt-clustered test with a non-inferiority margin fixed in advance; one aggregation everywhere; seed noise measured on the same stack for all 16 prompts.

**Clips** (made by rahul-3, task 24, #1219): cosmos-framework T2V, 480p 16:9, 93 f @ 24 fps, 35 steps, CFG 6, shift 10, no negative.
HUE v1.2 T2V public: physics_017,169,057,126,163,049,200,016,042,116 + robot_055,087,123,011,068,026; seeds 1 and 2 → 32 clips per arm.
Arms: base, baseL (base on the second box), loraA (real g, candidate), loraB (wrong g), loraC (no decay).
Note: the robot prompts differ from rog1's #1178 subset (only robot_011 is shared). That's fine, because #1178 is not the before here; base comes from the same cf stack.

**Judge** (unchanged, tools/hue_judge): Qwen3-VL-2B-Instruct bf16, 16 frames, short side 256, P(Yes) over Yes/No/Unclear, frame offsets 0 and 0.5.

**Aggregation**:
- clip score = mean over offsets {0, 0.5} of the per-clip category mean;
- prompt score = mean over seeds {1, 2};
- d_p = arm(p) − base(p), the same prompt and seeds (n = 16 prompts).

**Primary test (overall score; NVIDIA scoreboard item 3)**: one-sided 95% non-inferiority, margin δ = 0.03.
- **non-inferior** if the lower t(15) 90% two-sided bound is > −0.03;
- **regression** if the upper bound is < −0.03;
- **significant drop** (reported as a drop) if the upper bound is < 0;
- **inconclusive** otherwise. A non-significant drop is NOT called "no regression".
- Margin rationale: < half of the gross-corruption drops on real GAUGE clips (freeze −0.067, noise −0.071; work/rog1/hue_val/val_summary.json), ≈4% of the base score.

**Secondary**: Physical Laws category (the recipe's target), δ = 0.04, same rule. Visual, Geometric and Semantic categories are descriptive only. A 10k prompt-cluster bootstrap CI is reported as a robustness check.

**Controls**:
- baseL − base: the null arm (cross-box repeat; expected ≈ 0, which catches pipeline or box effects);
- loraB − base and loraC − base: any-LoRA effects. If A's Physical gain is matched by B/C, it is not physics.

**Seed noise**: base s1 vs s2 per-clip SD, for all 16 prompts (centred: sd(d)/√2).

**Code**: analyze_t24.py (this folder); watcher judge_watch.py pulls GB10 ~/jobs/rahul-3/hue_clips/<arm>/ once 32 clips are stable.

## Addendum A1 (2026-11-01 06:05 UTC, before any task-24 HUE clip exists): NVIDIA-scoreboard items on the same clips
- **Human decision**: margins 0.03 overall / 0.04 Physical approved (poornimajd, #1306, option A of #1273).
- **What**: tools/nv_scoreboard/score.py on every clip of all 5 arms (rog 4060, `--device cuda --dover_reps 3`, container fps 24):
  DOVER fused/technical/aesthetic (mean of 3 random fragment draws) and VBench dynamic degree (dd_binary, dd_norm).
  DOVER install: VQAssessment/DOVER git HEAD + DOVER.pth (239,729,097 bytes).
- **Aggregation/test**: same as the primary HUE analysis (seeds averaged per prompt; paired d_p = arm − base over 16 prompts;
  one-sided 95% t(15) LB; 10k prompt bootstrap as sensitivity). Code: analyze_nv.py. Output: res_nv/<arm>.json.
- **Margins (PROPOSED, not human-approved)**: dover_fused δ = 0.02 (absolute, ≈4% of a ~0.5 score);
  dd_binary (VBench set score) δ = 0.10; dd_norm δ = 15% of the base arm's mean. Same verdict rule as the HUE primary.
- **Reading**: dynamic degree has no real reference for these T2V prompts, so an arm − base change is a motion-amount
  change, not NVIDIA's motion-fidelity score (that needs real clips at the same fps). A large DD *increase* is flagged too.
- baseL − base is the A/A null; B and C are the any-LoRA controls, as for HUE.

## Addendum A2 (2026-11-01 06:12 UTC, scorer blind to arms; key held by rahul-3): NVIDIA-scoreboard items on the GAUGE-ball I2V eval arms
- **Clips**: every blinded `<6-hex>.mp4` in GB10 ~/jobs/rahul-3/eval_clips/ (task 24 #776/#874: base/A/B/C, 20 per arm =
  Pgauge seeds 1-16 + Pjson seeds 1-4, plus repeated-base clips from the second box). Only *.mp4 is pulled, never sidecars,
  so the scorer stays blind until rahul-3 posts the key after ro-1's blind physics scores.
- **Scoring**: tools/nv_scoreboard/score.py `--device cuda --dover_reps 3` (container fps 24) on the rog 4060 → DOVER
  fused/technical/aesthetic + VBench dd_binary/dd_norm. Code: work/rog-cc/t24_gauge_nv/ (gauge_nv_watch.py, analyze_gauge_nv.py).
- **Real reference (motion fidelity proxy)**: GAUGE real ball1-4 (dev, measure only), `ffmpeg -vf scale=832:480,fps=24
  -frames:v 93 -crf 18` (raj-4's recipe, truncated to the eval length of 93 f). R = mean dd_norm of the 4 real clips.
- **Unit/test**: the matched unit is (prompt, seed) — same prompt and seed in every arm; n = 20 units, ONE input image.
  Paired d = arm − base per unit; t(n−1) one-sided 95% bound (= 90% two-sided CI) + 10k unit bootstrap (sensitivity).
  Results describe this one scene only; no generalization across scenes is claimed.
- **Margins (PROPOSED, same as A1)**: dover_fused 0.02; dd_binary 0.10; dd_norm 15% of base mean.
  Motion-fidelity proxy gap = |dd_norm − R| per clip: an arm is non-inferior if the UPPER 95% one-sided bound of
  (gap_arm − gap_base) < 0.15 × base mean dd_norm; "regression" if the lower bound exceeds it.
- **Noise**: per-clip seed SD of base (16 Pgauge seeds, SD across seeds), and the repeated-base cross-box clips as A/A.
- **Caveat** (README): DD is nearly blind to a 6 cm ball; a DD change on this scene is camera/scene motion, not ball physics.

## Addendum A3 (2026-11-01 06:53 UTC, written BEFORE any clip below was judged): plausibility judge on the Deliverable-1 "mid-fall / detached-state" recipe (#1616, reports/deliverable_1_recipe.md)
- **Why**: Deliverable 3 needs the plausibility judge before/after for the recipe; DOVER/MF exist (#1616/#1639/#1747), the judge does not.
- **Clips (Nano)**: raj-3/agy-3 box_t68 (GB10 ~/jobs/raj-3/box_t68/), 189 f @ 24 fps, 832x480, 35/6/10, no negative, exact GAUGE ball prompt.
  BASE = box_ctrl_b{1,2}_noneg_s{1-4} (held frame 0); RECIPE = box_mid_b{1,2}_noneg_s{1-4} (mid-fall frame dd33/35). n = 8 + 8.
- **Real input control**: real GAUGE ball1/2, 93 f @ 24 fps, same ffmpeg recipe, from f0 (realball_b) vs from mid-fall t=1.32/1.40 s (realmid_b)
  — the clips already used for the DOVER control (#1738). Δ_real = mean(realmid − realball) over the 2 balls.
- **Judge**: tools/hue_judge (Qwen3-VL-2B, 16 frames, P(Yes), offsets 0,0.5 averaged), rog1's `gauge_ball` question set (13 Qs, validated
  real-vs-corruption #441; NOT NVIDIA's questions). One run, one model, same settings for every clip.
- **Input-neutral question set (PRIMARY)**: drop Q1 (asks if the ball is held at the start) and Q5 (asks if falling starts after release) —
  both presuppose the f0 input. Physical = Q2,Q3,Q4,Q6,Q13; Overall = mean of the 11 remaining Qs (Q2-4, Q6-13). All 13 Qs reported as secondary.
- **Unit/test**: per-ball mean over seeds (and offsets) → d_b = RECIPE − BASE for b = 1,2; the clip-level Welch SE over 8 vs 8 clips is the
  primary SE (seed noise; the 2 balls are too few for a t over balls). Net effect = Δ_nano − Δ_real (input-frame look alone).
- **Margins (borrowed from the human-approved HUE margins #1306)**: non-inferior if the one-sided 95% lower bound of Δ_nano > −0.03 (Overall)
  and > −0.04 (Physical). Improvement claimed only if the lower bound > 0 AND Δ_nano − Δ_real > 0.
- **Caveats, declared now**: the judge is order-blind (#601), so it cannot see bounce decay or time direction; the inputs differ between arms
  (not a same-fixed-input before/after, #1637/#1761); one scene, 2 balls; 2B judge has a yes-bias.
