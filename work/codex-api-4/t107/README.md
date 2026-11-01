# Task 107 completion: early conditioning-latent low-pass on pendulum inputs

**No preserved single rigid swing was confirmed in the 14 existing clips.**
Masked visual review codes all 12 low-pass clips and both controls N for the
fixed rigid-swing criterion. This does not establish no motion or no release:
visible rod/bob motion was coded in all 14. This is an unvalidated same-data
completion of ro-3's experiment, with one LLM coder, rather than an independently
replicated physical finding or a successful recipe.

## Coverage and frozen review

The shared queue has 14 finished jobs, all pinned to `puget13`, and 18 cancelled
earlier requests. Only finished jobs were adopted; nothing was generated here.
The published design called for 18 clips, but the re-submitted `jobs_alg2.jsonl`
contains 14: controls at seeds 2 and 3 were never in that second manifest.

| Requested arm | Input × seeds | Preserved scene Y | Rigid swing Y | Visible motion Y |
|---|---|---:|---:|---:|
| alg0 | pend10/11 × seed 1 | 2/2 | 0/2 | 2/2 |
| alg4: 4 steps, factor 2.5 | pend10/11 × seeds 1–3 | 2/6 | 0/6 | 6/6 |
| alg8f4: 8 steps, factor 4 | pend10/11 × seeds 1–3 | 0/6 | 0/6 | 6/6 |

These are observed qualitative codes, not validated population rates. Both
treatment doses have visible geometry failures in 6/6; controls have Y1/U1.
Scene loss includes substantial early viewpoint/apparatus reconstruction,
not necessarily a hard edit cut. A newly reconstructed pendulum that moves
is not a preserved original rigid swing. “Rest” is the original input filename
label, not an independent claim that the real rig was at physical equilibrium.

Protocol: [PREREG.md](PREREG.md), written before inspecting the clips or metrics.
Original four seed-1 aggregate descriptions were already known and disclosed.
Panels show only randomized IDs: eight full-scene frames, native 396×320 crops
every fourth frame, and four consecutive-frame followups for the original-scene
cases. Arm may be guessed from visual damage, so masking does not guarantee
effective blinding. Codes froze before opening key or metrics:

* Key SHA256: `d2185b479f89525fc3b560d8676e599bac4879d230f1c31f000d55541e73e083`
* Frozen-code SHA256: `b18a7dcc51a2f5b7674377ff957bea50e362b37c49e36649d4d73d99e7c66b34`
* Pre-unblind local commit: `8695bba` (immutable published freeze tag links the
  same files even if shared-main rebasing changes the commit hash).
* Board freeze messages #3958/#3959; key commitment #3951.

## Pixel-change diagnostic, not physics

Independent code reproduces all 12 published seed-1 scalar values with maximum
absolute difference **1.78e−15 gray levels**. The original ROI is x240:420,
y90:300. Gray is arithmetic RGB mean; early uses pairs 0→1 through 23→24,
late uses 68→69 through 91→92, and all uses all 92 pairs. A second larger
ROI x218:614,y0:480 is retained as sensitivity data in `results.json`.

| Arm | All-pairs ROI change, mean ± seed-cluster SE | Late ROI change |
|---|---:|---:|
| alg0 | 4.3394; seed SE unavailable (n=1) | 5.1462 |
| alg4 | 4.1894 ± 0.8835 (n=3 seeds) | 1.9938 ± 1.1936 |
| alg8f4 | 3.6130 ± 0.8709 (n=3 seeds) | 2.7834 ± 1.2714 |

Units: gray levels on 0–255. Each seed value averages the two input scenes.
The pooled treatment/control means use different seed sets and are **not**
matched effects. At the only matched control seed, all-pairs alg4−alg0 is
+4.0960 on pend10 and −0.8696 on pend11; alg8f4−alg0 is +2.5085 and −0.7820.
Their across-input means are +1.6132 and +0.8633, with no seed SE estimable.
The fully paired high-minus-low contrast is −0.5764 ± 0.4238 seed-cluster SE
(3 seeds × 2 inputs), also only a pixel-change diagnostic.

The larger apparent early motion in reconstructed scenes and the low later
motion of nearly static replacements illustrate why these quantities cannot
be read as rigid swing, physical speed, release or dissipation. No planted
validation or referee submission was made, and no physical constants are
estimated from these damaged clips.

## Provenance and checks

Shared original PNG inputs are copied under `inputs/`; their hashes and decoded
frame-0 PSNR are in `verification.json`. All seven clips for each input have
pixel-identical frame 0; PSNR against the shared PNG is 34.4637 dB (pend10)
and 35.0701 dB (pend11). This is consistent with a VAE round trip; it does
not authenticate the original submitted image bytes or initial noise tensors.

All 14 queue request/video contracts pass: prompt, input basename, seed,
dimensions 832×480, 93 frames, 24 fps, 35 steps, CFG6, requested shift10,
empty requested negative, and requested ALG fields. Four original native
seed-1 treatment sidecars additionally report **Nano Diffusers bf16, RTX 6000
Ada, UniPCMultistepScheduler, torch 2.15.0+cu132**. A native `null` negative
corresponds to the empty requested negative. Exact checkpoint/diffusers
revision, sigma array and execution telemetry were not preserved.

`source/server_alg.py` captures the original code: it inherits the loaded
pipeline's scheduler configuration, constructs UniPC with requested shift10,
low-passes latent frame 0 in `prepare_latents`, then restores the clean frame
through the end-step callback. Source inspection describes intended behavior,
not proof that each hook fired on the live model. **Do not assume this Puget
server used the board's Karras schedule or that shift10 was applied.** The
actual sigma schedule remains unverified. No live server or GPU was touched.

Independent ffmpeg decoding on two clips reproduces all 184 consecutive
per-frame pixel-change values within 1e−10 (observed exactly zero error).
The published analysis, codes/key and panel replay are reproducible from the
saved snapshot and clips. These are software/reproduction checks, not physical
measurement validation. No NVIDIA scoreboard scores were collected.

## Reproduction

Dependencies: Python3, numpy, opencv-python, Pillow; ffmpeg for decoder checks.
`prepare.py` uses the saved shared-queue snapshot, downloads only missing
completed clips (no submission), and reconstructs the masked panels/key.

```sh
python3 work/codex-api-4/t107/prepare.py /path/to/clips
python3 work/codex-api-4/t107/analyze.py /path/to/clips
python3 work/codex-api-4/t107/verify.py /path/to/clips
```

The two original job manifests, all queue statuses/sidecars, source hook,
published four-clip metrics/native summaries, clip hashes, full continuous
ROI traces and frozen review evidence are included. Three untouched original
pend10 seed-1 clips (one per arm) are in `original_examples/`; every other
clip can be fetched with its recorded queue ID.

## What remains unresolved

This existing-batch audit is complete, but the high-frequency-lock hypothesis
is unresolved. The missing two control seeds, unverified hook/sigma provenance,
one scene pair, and unvalidated rigidity codes prevent a cause verdict or a
general ALG claim. Any new cause test needs matched controls at ≥3 seeds,
verified model-input intervention logs, preserved geometry and validated
measurements. No recipe benefit or NVIDIA no-regression pass is established.
