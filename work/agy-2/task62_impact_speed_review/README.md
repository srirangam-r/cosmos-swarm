# Independent Replication and Review of Finding 1283 (Task 62)

**Reviewer:** `agy-2`  
**Target:** Finding `#1283` by `rahul-5-agy` (Task 52, commit `9939e44`)  
**Scope:** 4-condition drop height ladder (`dd33` 34.5 cm, `dd35` 24.4 cm, `dd37` 9.4 cm, `dd58` 5.3 cm; impact velocities $2.60\text{ m/s}$ down to $1.02\text{ m/s}$; seeds 1 and 2, $n=8$ clips).

---

## 1. Summary of Finding 1283

Finding `#1283` evaluated whether Nano's near-elastic bounce restitution ($e_T \approx 1.0$) is caused by neural network difficulty in resolving large velocity jumps at impact ($\Delta v \propto v_{impact}$, the smoothness hypothesis from learned-contact literature: arXiv:2103.15406, 2009.11193, 2610.33562).

The author reported:
- $e_T = 0.977 \pm 0.054$ at $v_{impact} = 2.60\text{ m/s}$ (drop 34.5 cm, seed 1, $n=4$ adjacent ratios).
- $e_T = 1.028 \pm 0.077$ at $v_{impact} = 1.02\text{ m/s}$ (drop 5.3 cm, seed 2, $n=4$ adjacent ratios).
- Difference $\Delta e_T = +0.051 \pm 0.094$ (n.s.), concluding that restitution is independent of impact speed.
- Identification of a mid-air levitation attractor at low release heights.

---

## 2. Independent Verification of Numerical Results

We independently analyzed the author's trajectory data, contact sheets, and generated video frames using both adjacent-ratio averaging and log-linear regression ($\ln(T_k) = \ln(T_0) + k \ln(e_T)$).

### A. Restitution across Drop Heights ($e_T$)

| Condition | Initial Drop | $v_{impact}$ | Author $e_T$ | Recomputed Adjacent $e_T$ | Independent Log-Linear $e_T$ |
|---|---|---|---|---|---|
| **High (`dd33_s1`)** | $34.5\text{ cm}$ ($186.2\text{ px}$) | $2.60\text{ m/s}$ | $0.977 \pm 0.054$ | **$0.9767 \pm 0.0621$** | **$0.9638 \pm 0.0236$** |
| **Very Low (`dd58_s2`)**| $5.3\text{ cm}$ ($28.6\text{ px}$) | $1.02\text{ m/s}$ | $1.028 \pm 0.077$ | **$1.0280 \pm 0.0889$** | **$0.9956 \pm 0.0343$** |
| **Difference ($\Delta e_T$)** | $-29.2\text{ cm}$ ($-2.6\times$) | $-1.58\text{ m/s}$ | $+0.051 \pm 0.094$ | **$+0.0513 \pm 0.1084$** ($t=0.47$, n.s.) | **$+0.0318 \pm 0.0417$** ($t=0.76$, n.s.) |

*Note on uncertainty:* The author reported standard error using $N$ in the sample variance denominator ($0.0537$ and $0.0770$). Using Bessel-corrected sample standard error ($N-1$) yields $0.0621$ and $0.0889$, confirming that $\Delta e_T$ is statistically indistinguishable from zero in both formulations.

---

## 3. Key Physical Discoveries from the Audit

### A. Velocity-Jump Smoothness Hypothesis Refuted
If neural smoothing of large velocity jumps were the bottleneck, reducing initial impact speed by $2.6\times$ ($2.60 \to 1.02\text{ m/s}$) and drop height by $6.5\times$ ($34.5 \to 5.3\text{ cm}$) would allow the model to dissipate energy toward real physics ($e_{real} \approx 0.693$). Instead, $e_T$ remains completely undamped ($0.96\text{--}1.03$).

### B. Massive Energy Creation ($5.8\times$ Gain)
In clip `ball1_dd58_s2.mp4`:
- Initial drop: $5.3\text{ cm}$ ($28.6\text{ px}$).
- Maximum rebound rise: **$30.8\text{ cm}$ ($166.0\text{ px}$)** on the second bounce (frame 24 to 42)!
- **Energy Amplification:** $h_{rebound} / h_{initial} = 5.80\times$, corresponding to an apparent velocity restitution $e_v = \sqrt{5.80} = 2.41$!
- This directly demonstrates that Nano does **not** obey an energy bound from the conditioning frame; it injects kinetic energy to reach its internal limit cycle amplitude (~$30\text{ cm}$). This strongly confirms the finding in U Tokyo (arXiv:2610.05135, Literature Digest 4 #1100), where Nano crossed impassable barriers on ramps by rising to $1.15\times$ its starting height.

### C. Proximity-Induced Mid-Air Levitation Attractor
At drop heights $\le 24.4\text{ cm}$, Nano exhibits a bifurcation into a static mid-air levitation state:
- `dd35_s2` ($24.4\text{ cm}$): 0 impacts; ball hovers/drifts slowly without contacting the plank.
- `dd37_s1` ($9.4\text{ cm}$): 0 impacts; ball remains suspended at $y \approx 200\text{--}266\text{ px}$.
- `dd37_s2` ($9.4\text{ cm}$): 1 impact at frame 16, then halts and hovers.
- `dd58_s1` ($5.3\text{ cm}$): 0 impacts; ball never falls to the plank.
- **Overall rate:** In **4 out of 6 clips** (66.7%) at drop heights $\le 24.4\text{ cm}$, and **3 out of 4 clips** (75.0%) at drop heights $< 10\text{ cm}$, the ball completely fails to execute sustained bouncing and is captured by the levitation attractor.

### D. Limit-Cycle Rhythms
The flight durations do not scale continuously with drop height:
- High drop (`dd33_s1`): settles into a high-frequency limit cycle of $7.8\text{--}9.0\text{ frames}$ ($0.33\text{ s}$ period).
- Low drop (`dd58_s2`): settles into a subharmonic limit cycle of $15.0\text{--}18.0\text{ frames}$ ($0.65\text{ s}$ period).

---

## 4. Control Comparison with Real GAUGE Ground Truth

Across all 19 real GAUGE mocap ball drops:
- Ground truth restitution is $e_{real} = 0.693 \pm 0.020$.
- A real drop from $34.5\text{ cm}$ comes to rest in $1.40\text{ s}$ after 4 bounces.
- A real drop from $5.3\text{ cm}$ settles in $<0.30\text{ s}$ with at most 1 tiny bounce.
- Real physics exhibits **inelastic capture** at low speeds (Bartz, arXiv:2204.10917): restitution drops sharply to zero below critical impact speed. Nano exhibits the polar opposite: non-dissipative bouncing ($e_T \approx 1.0$) or mid-air levitation.

---

## 5. Artifacts and Evidence
- Independent replication script: `replicate_finding_1283.py`
- Full numerical audit results: `replicate_finding_1283_results.json`
- Multi-panel QC diagnostic figure: `qc_finding_1283_ladder.png`
