# Task 133 PREREG: the end-state rule on unseen HUE T2V prompts (rog-cc, written before any clip exists)

**Question.** Raj #2930 req. 2 / charter steering (8): the recipe has to be a *rule* that works on prompts it was not designed on (HUE T2V prompts included), with ≥3 seeds and a matched control. The board's settle result (#2460 #2720 #2726: Nano follows text that says how an event *ends*) was only ever shown on GAUGE ball prompts. Does the rule, appended verbatim to unseen T2V prompts, keep NVIDIA's scoreboard (plausibility judge, DOVER, dynamic degree)?

**Rule R** (a fixed suffix appended after the prompt, with no per-prompt editing):
> By the end of the video, every object that was falling, sliding, rolling or bouncing has lost its energy and come to rest, staying completely still for the rest of the video.

**Control N** (a length-matched neutral suffix, 33 vs 32 words, with no dynamics content):
> The scene is lit by soft, even lighting that stays constant throughout the video, and the colours remain natural and true to life, with realistic textures and fine surface detail on every object.

**Base**: the prompt unchanged.

**Inputs**: the 16 task-24 HUE T2V prompts (Cosmos-HumanEval v1.2 public: physics_016 017 042 049 057 116 126 163 169 200; robot_011 026 055 068 087 123), exact text from the task-24 base sidecars. None was used to design the rule.
**Generation**: T2V (no image), 832x480, 93 f, 24 fps, 35 steps, CFG 6, no negative prompt. flow_shift 10 is sent, but the board servers ignore it (Karras sigmas, #2870). Seeds 1, 2, 3. Shared queue, `--endpoints q8-0..q8-7` only (one hardware/software stack). 144 clips (`jobs.jsonl`, `make_jobs.py`).

**Readout** (`run.sh`, `analyze_es.py`, both committed with this file):
- HUE: tools/hue_judge (Qwen3-VL-2B, 16 f, offsets 0 and 0.5 averaged). The per-sample HUE questions come from the ORIGINAL prompt; the suffix is not judged.
- DOVER (score.py, reps=1, a declared change from task 24's reps=3, made to fit the time left) and VBench RAFT dynamic degree.
- Unit = prompt (n=16). Prompt value = mean over seeds 1-3. Paired d_p = arm − ref. Report the mean, SE, t(15) 90% CI (= one-sided 95% bound) and a 10k prompt bootstrap.

**Primary**: R − base on HUE overall (margin 0.03) and HUE Physical Laws (margin 0.04); both margins are human-approved (#1306). Non-inferior if the 90% CI lower bound > −margin.
**Secondary**:
- R − base DOVER fused (margin 0.02, PROPOSED) and dd_norm (15% of base, PROPOSED);
- R − N and N − base (does any added sentence do it, or the end-state content?);
- physics_* and robot_* subsets, as CIs only.

**Reading.**
- R non-inferior on HUE + DOVER: the rule ships on T2V without a scoreboard cost.
- R's dd_norm drop larger than N's: the rule suppresses motion on unseen prompts. Report it as a cost, and as a sign the rule acts beyond GAUGE.
- R significantly worse than N on HUE: the end-state content (not length) hurts.

**Not tested here**: whether R improves physics on these prompts. There is no validated physics metric for free-form T2V scenes, so this is a no-regression check plus a motion-amount readout. Not tested either: I2V, 189 f.

**Order** (time-limited, SWARM_END 13:00 UTC): judge base, R → DOVER/DD base, R → analyze (primary) → judge N → DOVER/DD N → analyze. If not all 144 clips arrive by the fetch deadline (95 min), only prompts with all 3 seeds in both arms of a contrast enter it, and I report that.
