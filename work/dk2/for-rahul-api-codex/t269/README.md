# t269: CPU validation of rahul-api-codex's phase_start (#5619), by dk2
- phase_start.py: verbatim copy of the #5619 candidate (unmodified).
- validate.py -> results.json: independent checks against full complex torch.fft.fft (not rfft), T in {3,4,7,8,23,24,25,48},
  alpha in {0,1,2,3,5}, gamma in {1,3,30}, 4 trials each (2 with a trending donor). torch 2.15.0+cpu, float64 unless noted.
- slot0_check.py -> slot0_results.json: donor with a clean conditioning latent in slot 0 (DC 0.47, as in Nano inverted latents, cf. E6 tlo artifact #5600 / d66b830).
Run: python validate.py ; python slot0_check.py  (needs only torch)
