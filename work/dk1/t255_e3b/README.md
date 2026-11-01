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
