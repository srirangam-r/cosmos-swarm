# raj-2 task 9: does Nano stretch the prompted events to fill the stated clip duration?
Endpoint: raj-1's cosmos_local (diffusers Cosmos3OmniPipeline bf16, 100.111.167.68:8011). Inputs: GAUGE ball video 1/2 frame 0, letterboxed 1280x720 -> 832x468 + 6 px black pad (gauge_ball{1,2}_f0_832x480.png).
Arms (24 fps, 35 steps, guidance 6, flow_shift 10, no negative prompt unless stated):
- A: 189 frames, GAUGE flat prompt, default templates ("The video is 7.9 seconds long and is of 24 FPS." / inverse in uncond) -- raj-1's batch.
- B: 93 frames (stated 3.9 s); C: 61 frames (stated 2.5 s). Same prompt (jobs_dur.jsonl).
- E: 61 frames but stated 7.9 s: add_duration_template=False, the identical sentence appended manually to the prompt, inverse sentence as negative prompt (string-equal to the pipeline's 189-frame text; jobs_dur2.jsonl).
- F0: 189 frames, model-card JSON caption format (templates off), GAUGE content with vague timing "0:00-0:07". F1: same JSON but physically correct timeline (release ~0:01, ~0.3 s fall, at rest by 0:02). prompts_F.json, jobs_F.jsonl.
Prediction if Nano fills the clip: g ∝ 1/T² (A 0.45 -> B ~1.9 -> C ~4.5); E ≈ A; F1 > F0.
Measure: measure_dur.py (tools/realball v1.1 + trk_ballfall measure_ball v5 with QC images, 539.8 px/m).
