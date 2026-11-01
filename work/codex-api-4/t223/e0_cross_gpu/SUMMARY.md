# Independent E0 numerical summary

All distances below are gray levels (frozen result fractions ×255). This is
same-video independent-code replication of pixel-motion correspondence, with
execution provenance pending; it is not a validated physics finding.

| Requested noise | GPU labels | Seeds | Matched distance | Different-seed distance | Advantage (95% seed-bootstrap CI) | Raw p | Holm p (6) |
|---|---|---:|---:|---:|---|---:|---:|
| cpu | q8 → l40s | 8 | 0.75056 | 1.45575 | 0.70518 [0.39135, 1.03224] | 0.000100 | 0.000600 |
| cpu | q8 → a6k | 8 | 0.82801 | 1.46174 | 0.63372 [0.39813, 0.86292] | 0.000100 | 0.000600 |
| cpu | l40s → a6k | 8 | 0.82388 | 1.45716 | 0.63328 [0.38756, 0.88457] | 0.000100 | 0.000600 |
| cuda | q8 → l40s | 4 | 1.46210 | 1.47873 | 0.01663 [-0.30726, 0.34081] | 0.041667 | 0.125000 |
| cuda | q8 → a6k | — | — | — | Untested; no A6000 CUDA arm | — | — |
| cuda | l40s → a6k | — | — | — | Untested; no A6000 CUDA arm | — | — |

Pre-fixed paired secondary, q8→L40S on seeds101–104: CPU-minus-CUDA
correspondence advantage **0.34629** gray levels,
descriptive paired-bootstrap95% [-0.03855, 0.85099], n=4.
This interval includes zero. It does not establish an absence of a device effect.
CUDA and the paired contrast each have37/2000 undefined bootstrap draws
(all four resampled IDs identical). CPU n=8 comparisons have0 undefined draws.

CPU matched/different ratios are 0.516, 0.566, 0.565.
Thus these clips show detectable correspondence, not equal motion/output.
The CUDA raw exact p=1/24 is also reported despite its small point advantage;
its six-member Holm p=.125 and bootstrap interval do not support declaring
CUDA correspondence zero. No post-result equivalence threshold is used.

The CPU results use eight seed clusters per pair, not24 independent pairs
or168 independent different-seed observations. No cross-pair pooled CI.

Setup: owner E0 jobs, nvidia/Cosmos3-Nano declared local Diffusers bf16,
one real ball1_dd33 mid-fall input and exact task154 F prompt,832×480,93f,
24fps,35steps,CFG6,negative null. Requested flow_shift10; source default
Karras ignores it. Actual input bytes, sampler/sigmas, runtime/checkpoint
revisions and executed noise hashes remain unauthenticated.

Independent decoding passes32 native video contracts and3 FFmpeg/block-area
checks (<4.45e-16). A separate scalar24-permutation enumeration verifies
the CUDA p. No new clips, GPU jobs, planted submission or D1–D3 edits.
No E1–E4 outcomes inspected. Full raw matrices and native video hashes are
retained. See README.md for exact replay and limits.
