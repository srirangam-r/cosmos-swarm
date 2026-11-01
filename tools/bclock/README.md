# bclock (ro-1): bounce clock. Impact times, frames per bounce, restitution from flight times

**Referee planted check: PASS, 12/12 within 10%** (g 8/8, of which 6 are <5% and 2 are 5-10%; e 4/4 <5%).
That was submitted as `bclock v1 @ sha256:50a4de966bd1`. The committed file is sha256 `3cde5a0351a0`, which adds
the short-flight handling, `--mode diff` and `--pen`. With default settings it gives bit-identical planted
estimates (checked in `planted_est_v1.json`), so the PASS applies to the defaults.

## Why
Impact *timing* needs no metric scale and is largely immune to perspective. A ball that moves toward the camera
changes its pixel scale, but not when it hits the floor. bclock therefore gives:
- `impact_t_frames`: sub-frame impact times, where the parabolas of the flights on either side hit the common impact level;
- `flight_frames` / `flight_s` and `frames_per_bounce_mean ± se`;
- `e_ratio_seq`: e from successive flight times, e_k = T_{k+1}/T_k (under constant g, T ∝ launch speed). **Scale-free.**
- `e_timing_first` = T_1 / (2 t_fall), for a drop from rest (the planted e). Not meaningful on clips that start mid-fall.
- g, two ways: `g_curv` (2a/ppm per flight) and `g_timing` = 8h/T² (apex height over T). Both need the scale.

## Usage
```
python3 -I bclock.py clip.mp4 --fps <conditioned fps> --ppm 539.8 --point x,y [--pframe N] --qc qc.png --json out.json
python3 -I bclock.py --planted planted.json <clipdir> --out est.json [--qcdir qc/]   # uses --diam 0.10 sizing
```
- Track: NCC template match of the seeded ball patch over a vertical strip (±`--search` px in x, full height), so
  bounces that reverse vy are not lost. Ties are broken by distance to the constant-velocity or reflected prediction
  (`--pen`). The template is refreshed (EMA) when the match score is ≥0.8.
- Scale (planted mode): colour-distance blob vs the temporal median, equivalent diameter. Grey-level diff misses a
  yellow ball whose grey matches the background (planted-14 gave 2× g before this fix).
- Impacts: strict local maxima of image-y whose prominence is ≥ `--prom` px (default 8) against the next higher
  maximum on each side. A drop with no rebound in view is fit up to the landing frame (`flag=no_impact_fall`).
- **Look at the QC.** It shows y(t) with the impact lines and flight parabolas, plus circled frames.

## Cosmos results and limits (GAUGE mid-fall ball frames, 832x480)
- ball1, fps 24, 93 f, seed 1: tracked 100%, with 11 impacts at 7.0, 16.6, 25.0, 33.0, 40.8, 48.3, 55.9, 63.8, 70.9, 77.7, 85.3.
  By eye (ro-1, shift 5) I had 8, 17, 25, 33, 41, 49, 57, 64, 72, 78, 85, which agrees to within about 1 frame.
  7.84 ± 0.25 frames per bounce. e from flight times: 0.975 ± 0.006 (log-linear fit of T_k; mean of ratios 0.976 ± 0.024). See `cosmos/`.
- **Fails** (tracker loses the ball, so use crops by eye):
  - ball2, fps 24: the dark ball over the dark board, blurred, plus a shadow. It is lost after the first rebound in both grey and diff mode.
  - both fps 12 clips: about 4-7 frames per bounce and large per-frame jumps of a blurred black ball on a black curtain.
- Static camera only. `--mode diff` (tracking on the foreground map) is NOT planted-validated.
