# E6 / E6-W tlo arm is a washout artifact (dk2, task 258)
- washout.py: a frame counts as washed if |luma mean - frame0| > 30 or luma std < 0.6*frame0. Results on q8 clips (Raj, :8031):
  tlo C s1 32/32 clips >=10% washed (median 50% of frames, max |dmean| 96 gray); W-tlo 16/16. All other arms 0: recon 0/10, base 0/8,
  slo 0/32, all 0/32, W-all 0/8, WA 0/8.
- In all 32 C-tlo clips, the luma-flash ACF period (median 28 f, range 27-28) is within 2 f of the pend_acf period that E6 read (median 27.6).
  So the tlo "period" measures the flash.
- Candidate cause: latent slot 0 of x_inverted is the clean conditioning latent (spatial-DC rms 0.466 vs 0.025 for noise). noise.mix_noise's temporal
  FFT includes it, so the hard |f|<=0.125 cut (bins k<=3 of T'=24) spreads channel offsets over time with Dirichlet period 24/3.5 = 6.86 latents
  = 27.4 video frames, which matches the flash. Fix to test: filter latent frames 1..T'-1 only (or put fresh noise in slot 0 first) and use a smooth edge.
- rev_det.py: H100 vs q8 A_rec01-10 (same frozen driver) are not bit-identical: MAE 2.4-3.7 gray (A_rec03 8.1), frame0 0.33.
- gauss_h100_n10.json: on frames 1+, inverted noise is ~Gaussian (std 0.946x; tlo band 0.973x after shrink; slo 1.001x; ex. kurtosis <= 0.05).
## Proposed fix (not applied to tools/; Raj owns tools/cosmos_local)
- noise_skip_slot0.patch: opt-in `"skip_slot0": true` in the band dict. For temporal bands, mix_noise filters latent frames 1..T-1 only, and slot 0 comes
  from the fill. The default behaviour is unchanged (test_default_unchanged). With T-1=23, cut 0.25 keeps k<=2, a slightly narrower band than k<=3 at T=24.
- test_noise_slot0.py: 2 tests, and existing test_noise.py still passes (8 passed).
- On A_rec01 x_inverted: spatial-DC rms in frames 1,2,22,23 goes from 0.121/0.084/0.085/0.119 to 0.023-0.029 (Gaussian 0.025).
  Caveat: the leak is largest at the clip ends, while the washout peaks mid-clip, so a GPU rerun must confirm that the fix removes the washout.
  Suggested check: 4 C-tlo clips with latent.band {"band":"temporal_low","cut":0.25,"skip_slot0":true} + washout.py.
