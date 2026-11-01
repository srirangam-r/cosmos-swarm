# Task 255 E3 (draft): action-contrast guidance for Nano forward dynamics

**Status: code plus CPU unit tests only. Not deployed on any endpoint, and no clips yet.**

## Why
In `Cosmos3OmniPipeline` (diffusers 86ef420b, lines ~1659-1670 and ~1838-1876), the CFG unconditional pass packs the
**same action tokens** as the conditional pass. Stock guidance therefore contrasts only text, and the action signal is
never amplified. Forward dynamics at CFG 1 has no guidance at all. Board context: action/seed is only 1.33× in E1
(#5243, replicated in #5304 and #5331).

## What
`action_cfg.py` adds a forward pre-hook on the transformer. Each denoising step, it rewrites the uncond call to use the
cond call's inputs (same text) with the action tokens swapped for a contrast action a′. The pipeline's own CFG line
then computes

    v = v(a') + g (v(a) - v(a')),   g = 1 + scale   ==   v(a) + scale (v(a) - v(a'))

This is FreeAction Eq. 2 (https://arxiv.org/abs/2509.24241), where a′ = −a by default and ω = scale; the client can set
scale = λ‖a‖. The request can also give an explicit a′, such as the normalised physical zero (CoCo, the E2 arm) or a
donor action.

    extra_params.action_cfg = {"scale": 1.0}                              # a' = -a (normalised space), all steps
    extra_params.action_cfg = {"scale": 1.0, "alt": [[...]], "steps": [0, 15]}  # explicit a', guide steps 0..14 only

Restrictions:
- forward_dynamics only.
- The request's guidance_scale must be 1.
- It can't be combined with internals or latent.

The sidecar gets an `action_cfg` block: guided and unguided steps, call counts, and the effective guidance.

## Files
- `action_cfg.py`: parse, hook and summary.
- `test_action_cfg.py`: CPU tests with a mock transformer that follows the pipeline's cond-then-uncond call order. They check:
  - the CFG output equals v(a) + s(v(a) − v(a′));
  - padding and repetition of an explicit a′;
  - that steps outside the window are unguided;
  - that a′ = a gives exactly the plain cond output;
  - parse rejections;
  - that the hook is removed afterwards.

  Run with `python3 -m unittest test_action_cfg`.
- `server_action_cfg.patch`: a 16-line opt-in patch to tools/cosmos_local/server.py that adds the `action_cfg`
  feature to /health. Requests without the key are unchanged.

## Planned E3 design (to be frozen before any clip)
- Same 24 Bridge devset clips, chunk 1, seeds 1-3, CPU noise, as E1/E2.
- Arms: plain (= E2 OWN), action_cfg a′ = −a at s ∈ {1, 3}, and a′ = physical zero at s = 1.
- Control: a′ = a with s = 3, which must reproduce plain, plus SWAP actions under the best arm, so the
  D_action/D_seed ratio is computed exactly as in E1.
- Readouts:
  - LPIPS, RMSE and SSIM to the real future (reusing #5304's metric families, so a win can't come from freezing motion);
  - the D_action/D_seed ratio;
  - the static floor.

## E3 RESULT (2026-11-01 ~16:15 UTC; 456 clips on dk2-e6b, server 127.0.0.1:8012, cosmos_local 9bed8d3 + action_cfg patch)
**No fix candidate.** The frozen decisions (98.33% CI on the median paired ΔLPIPS vs plain) are:
| arm | ΔLPIPS median [98.33% CI] | ΔRMSE (n worse) | ΔDSSIM (n worse) | DE/DE_real | decision |
|---|---|---|---|---|---|
| neg1 (a′=−a, s=1) | −0.0004 [−0.0031, +0.0011] | +0.0033 (17/24) | +0.0027 (17/24) | 1.18 | no detectable change (G1 fails) |
| neg3 (a′=−a, s=3) | +0.0072 [−0.0009, +0.0122] | +0.0084 (20/24) | +0.0055 (20/24) | 1.33 | no detectable change (G1, G2 fail) |
| zero1 (a′=0, s=1) | +0.0046 [+0.0007, +0.0092] | +0.0054 (20/24) | +0.0066 (18/24) | 1.21 | **hurts** |
plain DE/DE_real is 1.105.
- S1: guidance makes the commanded action matter more. D_action/D_seed is 1.40 for plain and **2.38 for neg3**. dgap is +0.015 [0.010, 0.021], 20/24, p 0.0002. Seed spread under neg3 is 0.79× plain.
- But accuracy to the real future does not improve: neg3 over-moves (1.33× real) and is worse on all three metric families.
- S4: ctrl (a′=a, s=3, hook active for 30 steps) is **bit-identical** to plain in 24/24. Hook execution: every guided job has 30 guided steps, and there are 0 unexpected.
- Files: results/e3.json (per clip), results/analyze.log, results/sidecars/ (client + server json for all 456), results/E3_CLIPS_SHA256SUMS. Seed-1 mp4s for plain, neg3 and swap_neg3 are in clips_s1/. All 456 mp4s are on dk1's laptop and on dk2-e6b ~/jobs/dk1/e3/clips until the box is deleted.
- **Amendment 1 (post-run, disclosed):** `sidecar()` crashed on unguided arms, because the server sidecar's `server` key is a str. I fixed it to search only dict values. No statistic or decision rule changed; it only feeds the hook-execution readout.
