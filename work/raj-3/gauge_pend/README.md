# Real GAUGE pendulum: period reference and tracker check at Cosmos resolution (raj-3, task 8)

Data: HF InternRobotics/GAUGE-Dataset `data/rigid/pendulum/{json,video}/1-20` (dev; measured only, never trained on).

## 1. Mocap reference (`pend_mocap.py` → `mocap_period.json`)
Swing-plane PCA of the 30 Hz ball position, then a circle fit for the pivot and L, and zero-crossing periods.
- L = 0.2726 m on every clip; release angle 84.1 ± 0.5° (almost horizontal; the robot holds the rod and lets go).
- Period over the first 8 s after release: **1.1713 ± 0.0027 s** (sd, n=20). Damped-sinusoid fit over the same window: 1.1722 ± 0.0013.
- Period over the whole ~130 s record: 1.0473 ± 0.0012 s. That equals the small-angle 2π√(L/g) = 1.0474 s, so the mocap clock and L are right.
- **GAUGE's baseline of 1.06 s is the small-amplitude period.** A 189-frame, 24 fps Cosmos clip covers only ~8 s from an 84° release, and over that window
  the real period is 1.17-1.18 s (finite-amplitude lengthening). Against the matched baseline, Nano's 2.36 s is ×2.0, not ×2.2.

## 2. Real video at Cosmos resolution (`pend_pseudo_cosmos.py` → `pend_pseudo_cosmos_results.json`)
Each clip: first 250 container frames, dedup (25 fps content in a 30 fps container, as for the ball), keep 7.875 s, letterbox 1280x720 → 832x468 + 6 px
(the Cosmos I2V input transform), mp4v at the distinct fps, then trk.blobs tracking.
Reference: mocap zero-crossing period over the matched window after release (1.1798 ± 0.0018 s, n=20).
The video mostly starts ~1.8-2.8 s before release, so only ~5-6 s of swing is in the window.

| estimator | period / mocap (mean ± SE) | sd | notes |
|---|---|---|---|
| trk.pend unchanged (planted PASS) | 3.81 ± 0.42 (median 5.08) | 1.88 | fits from frame 0 and includes the hold; 12/20 clips sit on the 6 s bound, only 6/20 within 10% |
| release-aware damped sinusoid on x | 1.141 ± 0.138 (median 1.0016) | 0.62 | 18/20 within 1%; clip 13 locks onto 4.46 s (β < 0, R² 0.42); clip 18 has release detected at 0.08 s (R² 0.48, +2.8%) |
| release-aware zero crossings on x | **1.0005 ± 0.0007** | 0.0032 | 20/20 within 1% (max 0.8%) |

measure_pend v1 (tools/trk_ballfall) combines these: release detection, damped fit seeded with the zero-crossing period, and flag=ok only if
|T_fit − T_zc| < 5% and R² > 0.8. That should catch clips 13 and 18. Referee planted check: PASS 20/20, pendulum 4/4 <5% (planted/referee result in msg on #findings).
`pend_cli_check.py` runs the CLI on these 20 clips with QC images (results in `pend_cli_results.json` when finished).

## Caveats
- The real swing is near the image plane, at a fixed camera. A Cosmos clip may change the camera or the swing plane; period needs no scale, but tracking can fail.
- The x-sinusoid R² on real video is only 0.92-0.94, because an 84° swing is not sinusoidal. So R² < 1 on its own does not mean bad physics.
- Not tested: SAM masks, a Cosmos pendulum clip.
