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
