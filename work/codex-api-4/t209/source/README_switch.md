Executed v8 server = server_prompt_switch.py (= srv/server_next.py, deployed 08:50:56 UTC; chain_v8.out has deploy/health/hookcheck).
Hook: `_fwd` wraps pipe.transformer.forward. With CFG each denoising step makes 2 forward calls; call index n even = conditional, odd = unconditional (assumed order; confirmed only by the identity check below). Step i = n//2.
For from <= i < to, the conditional call's static text kwargs (input_ids, text_indexes, position_ids, und_len, sequence_length, vision_* indexes) are replaced by the captured prompt-2 (QT) pack; the unconditional call is untouched. Base prompt = F. P2 pack is captured by a 1-step dry run aborted at the first transformer call.
Windows (step indices of 35; exact from/to are in each native sidecar extra_params.prompt_switch): full 0-35, e3 0-3, e7 0-7, l7 7-35, l17 17-35.
Identity: SWfull (F base, QT text on every cond call) vs cause5_QT (native QT prompt, same seed): maxabs 0, mean 0.0 for s3 and s5 (chain_v8.out).
Not logged by the server: sigmas (see #4263: Karras sigma_flow step3 .993, step7 .987, step17 .93) and the per-clip used-step counter (sidecars show none).
native/ = original server MP4s + sidecars (crf as served).
