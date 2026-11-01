# Task 337 arm C (dk2): Time-to-Move dual clock with a weak clock. FROZEN before any clip.

**Why.** Arm A (region band, zero-mean fill outside the box at σ 0.898) turned the background into a flat wall (#6811, #6866).
dk1's t336b inj19/inj27 starts the background from pure noise (start_step 0). That is TTM's (T, t_strong) row, which TTM
reports "often produces duplicate copies", and dk-scout #6900 finds that plain Nano swings well outside these boxes.
TTM's own fix (https://arxiv.org/abs/2511.08633 §3, Table 3) is the dual clock: start the WHOLE frame from the reference
noised to a weak level t_weak, and hold only the masked region to the reference until t_strong. This is also the
signal-leak remedy (https://arxiv.org/abs/2309.15842): the background starts with the right low frequencies, the proxy's
Telea still, instead of zero-mean noise.

**Design** (`build_jobs.py` → `jobs.jsonl`, 32 jobs; derived from dk1 build_jobs_b.py @dc1a6f7):
- latent = {ref: dk1's t336 proxy, start_step: KW, init: noised, x0_inject: {steps: [KW, 19], box: dk1 boxes.json}}.
- KW=10 (σ 0.979) and KW=14 (σ 0.959). Release in the box is at step 19 (σ 0.898, the old Nano-Phys start), so the free
  phase in the box matches t336b inj19 and t276 nphys.
- Arms: dc10, dc14 (seeds 1-3); dc10_x17, dc14_x17 (×1.7 wrong-period proxy, seed 1). Scenes: real_12/17/18/19.
  Prompt, proxies, boxes, 93 f @ 24 fps, 832x480, 35 steps, CFG 6, CPU noise: all as in t336b.
- Dose ladder for the background start (whole-frame proxy signal): t336b inj19 (KW=0, none) < dc10 < dc14 < t276 nphys
  (KW=19, whole frame, no box hold).

**Readouts** (unchanged copies of dk1's analyze_b.py / quality_b.py; names only): `analyze.py <clipdir> <outdir>`,
`quality.py <scores.json> <out.json>`. DOVER ×3 with tools/nv_scoreboard/score.py, as in t319/t332.
**Decision rule (dk1 t336b, unchanged):** an arm is a fix candidate if ΔDOVER fused vs t276 plain ≥ −0.020 AND ≥ 10/12
clean ratio within 10% of real AND the x17 control ratio ≥ 1.5 on ≥ 3/4 scenes.
**QC:** a duplicate pendulum or a seam at the box edge (eye check on contact strips) counts as a failure mode.
Outside-box moving-pixel count versus plain (dk-scout #6900 §4 readout) is secondary.
**Predictions.** TTM: dc arms have no duplicates and a lower DOVER cost than nphys (TTM IQ .617 vs .623 for the reference).
The risk is that the background keeps nphys's cost when KW is close to 19. That's why there are two KW levels.
