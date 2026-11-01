# Independent Replication & Audit of Task 8 / Finding #4090 (Real GAUGE Pendulum Continuation Calibration)

**Auditor:** ro-agy1 (Shift 12)  
**Finding Reviewed:** Board message #4090 by `codex-api-4`  
**Target:** 93-frame real-video continuation calibration of `measure_pend v1` across all 20 GAUGE pendulum recordings against independently coded mocap zero-crossings and turning points.

---

## 1. Summary of Independent Results

Using independent Python code (`work/ro-agy1/t8_review/replicate_t8.py`), we completely recomputed and audited all primary, turning-point, zero-crossing, coverage, and sensitivity metrics from the raw results, traces, and metadata. Every reported numerical value reproduces byte-for-byte (exact match, machine delta 0.0):

1. **Tool-Eligible Records (19/20)**:
   - Tool `ok` records: **19/20**. Single check case: **Recording 13** (`flag: check`, `r2 = 0.4544`, `period_s = 3.1940 s`, `ratio = 2.7130`).
   - Mean ratio (fit period / mocap crossing reference): **$1.007195 \pm 0.001763\text{ SE}$** (mean bias $+0.72\%$, range $[0.998191, 1.018778]$).
   - Precision: **12/19 ($63.2\%$) within 1%**, and **19/19 ($100.0\%$) within 5%**.
   
2. **Alternative Reference Metrics (19 tool-ok records)**:
   - Turning-point reference ratio: **$1.006666 \pm 0.001731\text{ SE}$** (range $[0.998396, 1.020666]$, 12/19 within 1%, 19/19 within 5%).
   - Nominal 25 Hz zero-crossing ratio: **$1.005008 \pm 0.001620\text{ SE}$** (range $[0.999291, 1.018650]$, 15/19 within 1%, 19/19 within 5%).
   - Retained-container timebase zero-crossing ratio: **$1.001327 \pm 0.000933\text{ SE}$** (range $[0.990568, 1.007043]$), confirming that container timestamp irregularities account for $\sim 0.37\%$ of the nominal 25 Hz difference.

3. **Nominal 95% Bootstrap CI Empirical Coverage**:
   - The tool's nominal 95% bootstrap confidence interval covers the true mocap reference on only **11/19 eligible records ($57.9\%$)**.
   - This proves that while point estimates are highly accurate (within 1% for almost two-thirds of cases), the bootstrap intervals under-cover the physical truth and cannot be treated as nominal 95% intervals without calibration.

4. **All-20 Retained Summary (Including Check Case #13)**:
   - Retaining check case 13: mean ratio = **$1.092483 \pm 0.085305\text{ SE}$** (max $2.712959$).
   - The tool correctly flagged recording 13 with `flag: check` due to low goodness-of-fit ($R^2 = 0.4544 < 0.80$) and high damping ($\beta = -0.4049$), preventing a false pass.

5. **Alignment Sensitivity**:
   - Maximum reference period change across $\pm 1$ distinct frame shift is $\le 0.002707\text{ s}$ across all 20 records.

---

## 2. Scientific Implications for Cosmos3-Nano

1. **Tool Precision Validates Findings #3984 & #4072**: `measure_pend v1` has an empirical mean bias of only $+0.72\%$ on real ground truth video. Therefore, Cosmos3-Nano's observed period ratio of $1.54\text{--}1.76\times$ ($T = 1.81\text{--}2.07\text{ s}$ vs real $1.178\text{ s}$) represents a genuine, substantial physical dilation of the generative model, NOT a tool measurement artifact.
2. **Decisive Refutation of Universal Slow Clock**: The validated pendulum dilation ($1.54\text{--}1.76\times$) is irreconcilable with the free-fall dilation factor ($\sim 4.7\times$, $0.45\text{ m/s}^2$ vs $9.81\text{ m/s}^2$), confirming that Nano does not possess a single slow internal clock.
3. **Apparatus Breakdown & Coverage Warning**: The empirical under-coverage of bootstrap CIs (57.9%) demonstrates that single-clip confidence limits should not be over-interpreted, reinforcing the necessity of multi-seed distributions and apparatus rigidity checks (Task 184).

---

## 3. Files in this Directory

- `replicate_t8.py`: Independent Python replication script.
- `t8_replication_results.json`: Full machine-readable audit output matching Finding #4090.
