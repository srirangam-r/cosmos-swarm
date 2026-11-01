# pend_acf: tracker-free pendulum period (ro-3)

`python -I pend_acf.py clip.mp4 --fps F [--skip 12] [--release] [--max-s S] [--qc out.png]` prints JSON to stdout.

It reads the period off the image self-similarity curve D(lag) = mean_t |I_t − I_{t+lag}|, computed over the moving pixels (top 10% temporal std, 1/8-scale gray). The first prominent minimum is P. There is no bob or pivot detection and no scale, so it survives the things that break centroid trackers on Nano clips: the bob going behind the post, 90° swings, the bob leaving the plane. Use `--skip 12` on Nano clips, because Nano outpaints and reframes in frames 0-11. Use `--release` on real clips that start with a hold.

## Validation
- **Referee planted pendulums:** 4/4 within 5% (`pend_acf @ sha256:8e5b67b612fb`, see work/ro-3/task25_fps_pendulum/pend_acf_v1/referee_submit1.json). The formal verdict is "fail" only because the rule needs ≥10 estimates, and the planted set has only 4 pendulum clips.
- **20 real GAUGE pendulum videos** (84° release, letterboxed to 832x480 as Cosmos input, 7.9 s window; reference = raj-3's mocap zero-crossing period over the matched window):
  - period/mocap = **1.0016 ± 0.0008 (SE)**, sd 0.0034, 20/20 within 1%;
  - with flag=ok: 19 clips, 1.0021.
- **Short windows** (real clips cut to 2.0 / 2.4 / 3.0 s after release, i.e. 1.7-2.5 cycles, the regime of a 93-189 f Nano clip): ratio 1.019 / 1.018 / 1.016, sd ~0.013, 18-19/20 within 5%, 1 fail (no minimum).
  - Part of the +2% is physical: early large-amplitude cycles are longer than the 6 s-average reference.
  - So read a single short-clip period as ±5%.

## Flags
- `ok`: the 2nd minimum agrees with P within 5%, and windowed re-estimates spread < 10%.
- With fewer than ~2.3 cycles in the clip, neither check can run, so the flag is `check` with `window_spread=nan`. Then judge by the QC plot: one deep, isolated minimum is trustworthy (see the short-window validation above).
- The tool assumes the camera is static after `--skip`.
