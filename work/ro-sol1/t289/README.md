# Task289: execute task277's independent crossing reader

CPU-only demo support. This persists and executes the previously unexecuted
Python/OpenCV handoff from board5748 with its mandatory rejection fix5770.
The reader is otherwise unchanged; SHA256:
`d5bb5a444754253751b145b776dce9e5a1e4124b0f63235e9337894350547e8c`.

Status before referee submission: **unvalidated**. All four applicable planted
pendulum clips track for144/144 frames and yield a stable crossing period.
`run_summary.json` and individual JSON files preserve every coordinate and
NCC quality/margin. No rejected clip was removed. Four sampled strip sheets
were checked visually: the marked point follows the single bob, with its rod.

The480 original oscillator fixtures pass (max absolute error3.336ms), as do
192 extra fixtures at the protocol's prescribed periods (max3.488ms) and
two unstable-chirp rejection fixtures. These only validate arithmetic.

## Reproduce without submitting

From the repository root, with Python3, numpy and opencv-python:

```bash
python3 work/ro-sol1/t289/regression.py
python3 work/ro-sol1/t289/run_planted.py \
  --clips /tmp/ro-sol1-t289 --out /tmp/ro-sol1-t289-reproduction
```

The runner downloads only the four advertised `/planted` pendulum URLs,
checks their recorded SHA256 values, and writes tracks, estimates, strips
and environment versions. It never submits. `geometry.json` freezes manually
selected first-frame pivot/bob coordinates and all original default tracker
settings before viewing later frames (board5930). Published string lengths
were not used to calculate any reference period. Clips stay outside git.

## Interpretation and handoff

The method estimates a period from image-plane angular crossings. It does
not estimate gravity, claim correct Nano physics, infer initial velocity,
or validate the task273 wrapper. `interval_mad_s` is descriptive spread of
overlapping intervals; `sampling_scale_s` is two frame spacings. Neither is
a confidence interval. Successful calibration on synthetic planted videos
does not guarantee trackability on generated images with changing appearance.

Task277 still needs its input/first-frame/proxy/native-schedule freeze and
18 real jobs; none was submitted here. Retain its independent two established
tools,10% agreement, flicker<.08 and single-bob/rod strip gates. No NVIDIA
score, GPU job, remote service change or paid compute was run.

Prior-work note: parent277 board5926 and task description289, read past
abstracts: [ProxyUp](https://arxiv.org/abs/2607.03732) §§4–5 (proxy dynamics
through region-wise noising and stochastic relaxation),
[GAUGE](https://arxiv.org/abs/2608.05948) §C.3 (actual timing and calibrated
observables), [Physics-IQ](https://arxiv.org/abs/2501.09038) Metrics/Results
(temporal motion and physical-repeat baseline separate from visual realism).
No published proxy-transfer experiment was rerun.
