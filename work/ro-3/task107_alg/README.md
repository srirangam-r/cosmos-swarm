# Task 107: ALG (early low-pass of the conditioning latent) on the pendulum rest frame

Question: does Nano's failure to release the pendulum from the rest frame (#2361: 0/6 swing from rest, 6/6 from mid-swing)
come from a high-frequency lock on the conditioning frame (scout-1 hypothesis F, #2365; ALG arXiv 2506.08456)?

Method: `server_alg.py` (diff vs the plain server in `server_alg.diff`) adds `extra_params` `alg_steps=k`, `alg_factor=f`.
For the first k of 35 denoising steps the clean conditioning latent (latent frame 0, shape 48x30x52) that the
transformer sees in both CFG passes is bilinearly down-sampled by f and up-sampled back. From step k on, the exact
clean latent is restored, so the decoded frame 0 is the real input (smoke test: PSNR 34.5 dB vs input, VAE level).
Default k=0 is the unmodified pipeline.

Arms (jobs_alg.jsonl, queued on puget13 only): GAUGE pendulum 10/11 rest frames (task 99 inputs), seeds 1-3,
neutral prompt, 832x480, 93 f, fps 24, 35 steps, cfg 6, shift 10, no negative.
- alg4: k=4, f=2.5 (ALG paper default, ~10% of steps)
- alg8f4: k=8, f=4 (stronger dose)
- alg0: k=0, same-server control

Readout: eye codes on ROI strips (rigid swing / deformed / held) + ROI motion (task 99 roi_qc.py).
