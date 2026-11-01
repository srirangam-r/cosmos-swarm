# Large-angle pendulum correction: independent review

The published angle tracks do not support larger amplitude as an explanation
for the selected slow periods. Independent code reproduces the arithmetic in
board **4312** and **4313**. This is a same-data model/sensitivity review;
physical amplitudes remain unvalidated, and it does not identify Nano's cause.

## Results

The unchanged six gate-PASS pend10 clips have six distinct seeds
(6, 9, 12, 16, 23, 24). Geometric mean ratios and selected-seed log-t 95% CIs:

| Calculation | Period ratio |
|---|---:|
| Original periods / real period | 1.670 [1.416, 1.970] |
| Published half-range amplitudes, independent ODE correction | 1.735 [1.467, 2.051] |
| Published one-side peaks for both real and Nano | 1.668 [1.343, 2.073] |
| Independent raw-angle extrema, median-5 primary | 1.717 [1.465, 2.012] |
| Independent raw-angle extrema, no filter / median-3 | 1.729 / 1.724 |
| Nano peak, deliberately zero real amplitude | 1.448 [1.166, 1.799] |

All source corrections and CIs reproduce within 2e-9. The independent extrema
code uses the original valid angle samples, not either author's amplitude code.
The source amplitude/period Spearman rho is -0.029 (p=0.957); this small selected
sample does not establish a population correlation of zero.

For #4313's fit-A0 definition, independently recomputed ratios are
**1.664 +/- 0.085 clip SE** (17 clips), and **1.694 +/- 0.109 seed SE** after
averaging repeated arms within each of 13 seeds. Maximum per-clip arithmetic
error versus its saved result is 2.94e-14.

The two clips eligible under task 198's earlier frozen native QC, s23/s24,
have independently measured raw ratios 1.436/1.471. Using #4312's primary
amplitudes gives 1.527/1.495: mean **1.511 +/- 0.016 selected-seed SE**.
Using peak amplitudes gives 1.560/1.280, with a very wide two-seed interval.
The independent period method passed planted period cases; this does not
validate the angle amplitude or its correction. No fresh-seed replication.

## Independent calculation and its assumptions

A fixed rigid body with a fixed pivot obeys
`I*theta'' = -m*g*d*sin(theta)`, where angle is the centre-of-mass displacement
from its stable equilibrium. The small-amplitude time scale is
`sqrt(I/(m*g*d))`; it is not determined by image rod length alone.
See [MIT's physical-pendulum equations, pp. 2-3 and appendix 24A](https://ocw.mit.edu/courses/8-01sc-classical-mechanics-fall-2016/mit8_01scs22_chapter24.pdf).

After rescaling time, `audit.py` directly integrates `theta''=-sin(theta)`
with zero initial velocity. Four times the first downward zero crossing is
the period. Dividing by `2*pi` gives `F(A)`; corrected ratio is
`T_nano/T_real * F(A_real)/F(A_nano)`. This agrees with the finite-angle solution
in [NIST DLMF 22.19(i)](https://dlmf.nist.gov/22.19.i).
No author fit/correction code or elliptic-function library is imported.
Numerical checks are software checks, not referee validation.

The correction assumes a conservative fixed-geometry planar oscillator.
Applying a single amplitude to damped, asymmetric, deforming, driven, or
changing-plane motion is a sensitivity model, not an exact physical inference.
The tracked rod direction need not be the centre-of-mass direction if geometry
changes. A tilted fitted centre alone does not prove a physically impossible
equilibrium without the mass geometry.

## Qualifications that should survive report integration

**A common camera does not cancel angle projection.** For an orthographic
vertical swing plane foreshortened by `c`, observed angle is
`atan2(c*sin(theta), cos(theta))`. A common `c=0.5` maps real/Nano amplitudes
70/50 degrees to 53.95/30.79 degrees. The true `F_real/F_nano` is 1.04988;
using the two image angles gives 1.03932. This is a mathematical counterexample,
not an estimate of the GAUGE camera or its error.

**The peak sensitivity is not an unconditional lower bound.** Using the real
peak adds a real-amplitude factor. Even setting that factor to 1 leaves a
selected geometric mean of 1.448. Under the additional orthographic vertical
plane assumption, any true excursion is at most `max(90 degrees, observed
absolute peak)`: below horizontal the true angle is below 90; above horizontal,
foreshortening increases the observed angle. Using this cap and real `F=1`
gives 1.381 [1.144,1.669]. On the native-QC subset the individual values are
1.216/1.111, but its two-seed CI is [0.655,2.062]. These calculations require
complete extrema, correct vertical/equilibrium, fixed geometry, and the stated
projection model. They are not a proof about arbitrary 3D generated motion.

**Tracking misses matter.** The six published angle tracks have maximum gaps
0.042-0.542 s, including 0.292/0.542 s for s23/s24. Interpolation does not recover
unobserved extremes. Independent extrema algorithms share the same input tracks
and cannot independently validate their completeness. The source's own #4412
reports loss of tracking near horizontal in other seeds.

**G3 does not impose a physical 1.10x maximum period change.** G3 checks the
median absolute projected-length discrepancy in an angle-restricted subset,
not a maximum real length. Independent reconstruction reproduces every G3
median. Among its eligible tracked frames, s16 has **34/69** at >=20% error,
and s23/s24 have **23/57** and **13/48**. Discrepancies may reflect projection
or tracking rather than deformation. A pointwise 20% bound on an unchanged
pendulum's effective physical length would imply sqrt(1.2)=1.095, but G3 does
not supply those premises. This corrects the reasoning in board **4440**;
it does not show that length actually explains the slow periods.

All intervals condition on selection and omit angle/period calibration error,
model mismatch, shared input, and apparatus validity. The same real GAUGE
pend10 continuation is the control. Setup: q8 Karras; requested shift 10 ignored;
832x480, 93 frames at 24 fps, 35 steps, CFG 6, empty negative; base/neutral/Rule R
arms inherited unchanged. These are diagnostic mid-event inputs, not proof of
a deployable first-frame recipe. No NVIDIA scoreboard improvement is claimed.

## Reproduce

Run `python3 work/codex-api-4/t219/audit.py` from a checkout with NumPy and SciPy.
Only bundled `source/` snapshots are read; hashes and runtime versions are saved
in `results.json`. Run `python3 work/codex-api-4/t219/verify.py` for source,
join, synthetic/numerical sanity, and deterministic output replay checks.
No video download, model, GPU, secret, network, or referee access is required.
Recorded runtime: Python 3.10, NumPy 1.26.4, SciPy 1.8.0. SciPy warns that
this NumPy version is outside its declared range. Independent ODE/quadrature
agreement, synthetic checks, and standalone byte replay all pass in this
environment; the versions and checks are retained for reproducibility.

Protocol: board task 219 messages 4450/4455, copied into `PREREG.md`.
Prior independent native QC/periods: work/codex-api-4/t198 at 91f6aff.
Source results: work/rahul-api-2/t205 at 92ceb8d and
work/kiro-1/t206_amplitude at 9835d81. Sources here match the hashes in results.
