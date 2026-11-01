# Task 255 E3b: held-out replication of E3 (action-contrast CFG) on 24 NEW Bridge episodes

Frozen before any E3 metric was computed or looked at (E3 clips were still being generated; only a md5 wiring check,
ctrl == plain, had been seen). Purpose: charter requirement (8): a recipe must work on inputs it was not designed on.

- **Data:** `devset_bridge_ho/`, 24 episodes of IPEC-COMMUNITY/bridge_orig_lerobot, built by the unchanged
  tools/robot_pred/build_devset.py (n_chunks 2). Selection: `random.Random(20261102).sample(episodes with length>=33
  minus the 24 devset_bridge episodes, 24)` (selection_ho.json). The original devset selection (seed 20261101)
  reproduces exactly with the same code, so this is the same procedure with a new seed. 14/24 have empty task text
  (Bridge has many; the FD prompt effect is ~0.1x the seed effect, #5331). Actions: 3.9% of values outside [-1,1]
  (devset README expects 1-5%). Same caveat as the devset: Bridge train split, Nano may have seen these episodes.
  Do not train on them.
- **Jobs:** `jobs.jsonl` = ../t255_e3/make_jobs.py (e8325a9, unchanged) run on this devset: same 7 arms, seeds 1-3,
  CPU noise, 17 f @ 5 fps, 256x256, 30 steps. Job names keep the t255e3_ prefix (episode ids do not overlap E3's).
- **Analysis:** ../t255_e3/analyze.py (e8325a9, unchanged): `python3 analyze.py devset_bridge_ho <e3b_clips> e3b.json`.
  Same primary, Bonferroni 98.33% CI and guards G1-G3.
- **Held-out decision rule:** an E3 arm that is a FIX CANDIDATE on the dev set is "replicated held-out" if, on E3b,
  its d_A 95% CI upper bound is < 0 (one pre-chosen arm, so no Bonferroni) and G1-G3 hold. If E3 has several fix
  candidates, the one with the most negative E3 median d_A is the pre-chosen arm; others are reported descriptively.
  If E3 has none, E3b is reported descriptively (all arms, Bonferroni CIs) as a second dev sample.
- **Run:** on the same on-box 127.0.0.1 server as E3 (run_onbox.sh reuses a healthy server with action_cfg),
  started automatically after E3 prints E3_DONE (chain_after_e3.sh).

## Result (2026-11-01 16:33 UTC): E3 had no fix candidate, so E3b is descriptive. It reproduces E3 on held-out episodes.
Analysis: ../t255_e3/analyze.py with Amendment 1 (sidecar parse fix, 55349f4; no statistic changed). The server was the
same 127.0.0.1:8012 server on dk2-e6b (H100) as E3. Run on 456/456 clips with 456 server sidecars. ctrl == plain bit-identical 24/24 (S4).

| arm | ΔLPIPS median [98.33% CI] | n worse | ΔRMSE (n worse) | ΔDSSIM (n worse) | DE/DE_real | decision |
|---|---|---|---|---|---|---|
| neg1 (a′=−a, s=1) | +0.0003 [−0.0039, +0.0022] | 12/24 | +0.0018 (16/24) | +0.0005 (13/24) | 1.23 | no detectable change |
| neg3 (a′=−a, s=3) | +0.0074 [−0.0021, +0.0123] | 16/24 | +0.0071 (19/24) | +0.0051 (19/24) | 1.33 | no detectable change (G1, G2 fail) |
| zero1 (a′=0, s=1) | +0.0016 [+0.0003, +0.0066] | 19/24 | +0.0029 (20/24) | +0.0019 (17/24) | 1.24 | **hurts** |
| plain | (mean LPIPS 0.110, static floor 0.128) | | | | 1.09 | |

S1 (action sensitivity): the own-vs-swap LPIPS gap grows under neg3 by +0.019 [0.003, 0.028] (18/24, sign-flip p 0.0007),
and D_action/D_seed goes from 1.17 to 2.10 (E3: 1.40 to 2.38). E3 replicates on all points: guidance strengthens action control,
overshoots the real motion, and does not move the rollout closer to the real future. A zero contrast hurts.
Files: results/e3b.json, results/sidecars (client + server JSON for all 456), results/E3B_CLIPS_SHA256SUMS (456 mp4s),
clips_s1/ (plain/neg3/zero1 at seed 1, 72 mp4s). The other mp4s are kept locally by dk1 (hashes above).
