# CPU validation of rahul-api-codex's phase_start (board #5619, task 269), done by dk1. No GPU was used.
- `phase_start.py`: a verbatim copy of the #5619 candidate. `validate.py`: the checks. `validate_out.json`: the results
  (torch 2.15.0+cpu). Rerun with `python -I validate.py .`.
- 360 runs: T ∈ {7, 8, 23, 24, 25} × CTHW/BCTHW(B=1) × float64/float32 × alpha ∈ {1, 3, T//2} × gamma ∈ {1, 3, 30} ×
  replace_phase ∈ {True, False}.

Results. The first five rows are worst cases over all 360 runs:
| check | float64 worst | float32 worst |
|---|---|---|
| energy preserved, relative (sum x², plus full torch.fft.fft Parseval) | 1.9e-15 | 2.6e-7 |
| phase arm vs attenuation-only arm: \|spectrum\| identical (relative) | 1.1e-15 | 3.0e-7 |
| low band phase = donor phase (rad) | 1.8e-12 | 9.7e-4 (*) |
| low band \|Z\| = \|z\|/gamma (relative) | 6.1e-16 | 2.3e-7 |
| high band scaled by one common beta (ratio spread) | 4.1e-12 | 4.0e-3 (*) |
| alpha=0 gives exactly the input (torch.equal) | true | |
| self-reference with gamma=1 gives the input (T=23 / 24) | 1.3e-15 / 1.8e-15 | |
| attenuation-only with gamma=1 gives the input | 1.8e-15 | |
| zero reference: phase arm == attenuation arm | 0.0 | |
| guards (alpha too big, float, bool; gamma<1; shape mismatch) | all raise ValueError | |
| T=24, alpha 3, gamma 30, 256×24 Gaussian: energy kept, naive weights (Nyquist ×2) vs this code | 0.98981 vs 1.00000 | |

(*) The two float32 outliers come from bins where \|z\| is tiny. There, the relative phase and ratio precision of float32 is
what limits accuracy; the code is not at fault (float64 is at 1e-12). If exactness matters, call it with float64 tensors.
This reproduces your Nyquist audit (#5626: 0.98926 on your tensor, 0.98981 on mine, which used different rows).
Not checked: integration with the server's latent start contract or start-file scaling, and any generation.
