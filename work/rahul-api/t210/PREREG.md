# Task 210 PREREG (written 12:50 UTC 2026-11-01, before any full-grid clip was generated)

Question: does appending the D1 Rule R suffix to the prompt degrade Cosmos3-Nano's real-robot clip prediction?

Data: shared `tools/robot_pred/devset_bridge` (24 WidowX Bridge clips, rohith-cc-1), chunk 1 only:
real frame 0 + action chunk 0 (16x10) -> 17 frames @ 5 fps, 256x256, 30 steps, guidance 1.0, requested flow_shift 10
(board servers: Karras sigmas, flow_shift ignored, #2870), no negative prompt, guardrails off. q8-0..7 endpoints only.

Arms (make_jobs.py): base = devset prompt verbatim; R = prompt + "." + task-133 Rule R suffix (exact rog-cc text);
N = prompt + "." + task-133 length-matched neutral suffix. Seeds 0,1,2,3. 24 x 3 x 4 = 288 clips.
Smoke test (2 clips, bridge_002407 s0 base/R) was generated and scored before this file; nothing else.

Metrics (score_t210.py, shared score.py functions): PSNR, SSIM, LPIPS-alex on predicted frames 1-16 vs real 1-16.
Extra: motion_mad = mean |pred_t - pred_0| (does the arm still move?) vs the same on the real clip.

Analysis (analyze_t210.py):
- Unit = clip (n=24). Seeds averaged within clip and arm first.
- PRIMARY: LPIPS R - base. Paired t 95% CI over clips + clip bootstrap (10k).
  NONINFERIOR if CI upper < +0.010 LPIPS (about 1/3 of the model-vs-static-floor gap on the smoke clip);
  WORSE if CI lower > 0; BETTER if CI upper < 0 (it is also NONINFERIOR then); else INCONCLUSIVE.
- Seed-noise reference: the same statistic for base seeds {0,1} vs base seeds {2,3} (a null pseudo-contrast),
  and the seed-to-seed sd of per-clip LPIPS within base.
- Secondary: PSNR, SSIM for R - base; R - N and N - base for all three; motion ratio (pred/real motion_mad) R - base
  (a freeze shows as a negative shift). Per-seed sign counts.
- Not tested: chunk 2 / autoregressive rollout, DROID, AgiBot, other recipes (mid-event conditioning), other stacks.

Amendment 1 (12:53 UTC, before any full-grid result): 10/24 clips have an empty instruction and the queue rejects an
empty prompt. Those clips use "A robot manipulates an object." (NVIDIA notebook default, as in the DROID gen_vllm.py)
as their base prompt, with R/N appended to it. Report the 14 instructed vs 10 default-prompt clips separately as well.
