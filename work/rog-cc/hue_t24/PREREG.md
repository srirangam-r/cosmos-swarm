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
