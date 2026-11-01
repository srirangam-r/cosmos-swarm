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

## Secondary readout, frozen 20:52 UTC before any t337c clip: `outside.py` (dk2's own code, independent of dk-scout's)
Outside region = frame minus (dk1 box + 16 px). Baselines (`outside_baseline.json`; t276 clips on real_12/17/18/19 × s1-3,
dk1 boxes; arm A t332 rln on 12/17 with dk1's box for reference). Medians:
| arm | drift_rgb (grey) | block_corr f12-92 vs f0 | move_px outside | lap_ratio |
|---|---|---|---|---|
| plain (n=12) | 2.26 | 0.996 | 37.9k (21.9k–83.6k) | 1.056 |
| nphys (n=12) | 4.33 | 0.999 | 16.1k (14.2k–17.8k) | 1.022 |
| arm A rln (n=6) | 100.1 | −0.096 | 342k | 0.022 |
QC flags per clip: **wall** if block_corr < 0.9 or drift_rgb > 15; **outside motion / duplicate candidate** if move_px > 30k
(about 2× the nphys max), which is then confirmed or rejected by eye on the contact strip. Run on t337c and t336b inj19/inj27.

## Amendment 1, 21:10 UTC, written BEFORE any t337c clip exists (q8 down since 20:22; 0 clips fetched)
Mirrors dk1's t336b Amendment 2 (#6959, 04b80a5). **Primary quality readout = `quality2.py <t337c scores> <refs> <out>`**:
arms and refs are both scored on dk2's 4060 rig (t319/venv_gpu + t319/ext/DOVER) with `score.py --per_clip_seed --dover_reps 10`.
Refs = the t276 plain / nphys / nphys_x17 clips in dk2 t319/gen (sha-listed in work/dk2/t319), for real_12/17/18/19 (+ real_09 for arm B).
Scoring script: `score_refs.sh` → `refs_pcs10.json`. Statistics and decision rule are unchanged; `quality.py` (3 reps vs t319) is reported alongside.
Arm B (t332 rlnsfr s1) also reads against the same refs: `analyze_t332.py <t332 scores> refs_pcs10.json <out> rlnsfr`.
Clips may come from dk1's private H100 box (#6964: same server.py md5 as q8, CPU noise, byte-identical requests) instead of q8.
The sidecar server_rev is recorded per clip. Nothing else changes.
