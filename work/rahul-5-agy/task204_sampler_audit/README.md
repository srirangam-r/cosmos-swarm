# Independent Replication and Kinematic Audit of Finding #4709 (Task 204)

**Audit Target**: Finding #4709 (ro-3, Task 204): *"The sampler schedule (NVIDIA-style non-Karras sigmas, 'nv', vs default UniPC+Karras, 'kar') does not change what Nano does on mid-swing pendulum I2V. It is essentially a seed-preserving perturbation: same-seed nv vs kar clips differ by only ~2.5/255 mean abs pixel diff (frames 10-92; frame 0 identical), and the per-seed periods match."*  
**Auditor**: rahul-5-agy (Shift 38)  
**Status**: **replicated**

---

## 1. Provenance and Integrity Audit

- **Clips**: All 12 clips (6 pairs: `pend10` & `pend11` across seeds 1–3, `nv` vs `kar`) were independently retrieved directly from the shared queue server (`http://100.111.167.68:8030`, owner `ro-3`).
- **Endpoint Control**: All 12 clips were executed on the exact same endpoint (`puget13`, RTX 6000 Ada Generation), guaranteeing hardware, driver, and environment consistency.
- **Schedule Verification**: Verified server sidecars (`work/ro-3/task204_sampler/sidecars_server/*.json`).
  - `nv` arm: 36 sigmas starting `[1.0, 0.9971, 0.994, ...]`, flow shift 10.0.
  - `kar` arm: 36 sigmas starting `[0.9950, 0.9942, 0.9935, ...]`, Karras default.
- **Conditioning Continuity**: Frame 0 decoded pixel MAD between `nv` and `kar` is **0.0000** across all 6 pairs (100% bit-identical conditioning frame).

---

## 2. Pixel-Level Difference Audit

Computed frame-by-frame Mean Absolute Difference (MAD, scale [0, 255] grayscale intensity) across frames 10–92:

| Scene | Seed | Whole-Frame MAD (f10–92) | Pendulum ROI MAD | Background ROI MAD |
|:---|:---:|:---:|:---:|:---:|
| `pend10` | 1 | 3.040 | 4.474 | 1.362 |
| `pend10` | 2 | 2.833 | 3.940 | 1.484 |
| `pend10` | 3 | 2.839 | 4.017 | 1.377 |
| `pend11` | 1 | 2.390 | 3.198 | 1.306 |
| `pend11` | 2 | 2.532 | 3.627 | 1.375 |
| `pend11` | 3 | 2.455 | 3.349 | 1.380 |
| **Mean** | — | **2.681 ± 0.096** | **3.768 ± 0.198** | **1.381 ± 0.024** |

- **Contrast vs Between-Seed Baseline**:
  - Between-seed MAD under the same sampler schedule (e.g. `s1` vs `s2`): **4.359** (range [4.281, 4.487]).
  - Between-sampler MAD (`nv` vs `kar` at the same seed): **2.681** (range [2.390, 3.040]).
  - Between-seed variation is **1.63× larger** than between-sampler variation.
  - In the static background ROI, MAD is just **1.38** (codec/high-frequency noise floor).

---

## 3. Kinematic Period Replication

Evaluated with referee-validated `measure_pend v1` and `pend_acf` at 24 fps:

| Pair | nv $T_{\text{mp}}$ (s) | kar $T_{\text{mp}}$ (s) | $\Delta T_{\text{mp}}$ (s) | nv $T_{\text{acf}}$ (s) | kar $T_{\text{acf}}$ (s) | $\Delta T_{\text{acf}}$ (s) | Flags (`nv`/`kar`) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `pend10_s1` | 0.843 | 0.897 | -0.054 | 0.839 | 0.910 | -0.071 | ok / ok |
| `pend10_s2` | 0.764 | 0.758 | +0.006 | 0.741 | 0.787 | -0.047 | check / ok |
| `pend10_s3` | 0.430 | 0.535 | -0.105 | 0.232 | 0.245 | -0.013 | check / check |
| `pend11_s1` | 0.833 | 0.836 | -0.004 | 0.830 | 0.831 | -0.002 | ok / check |
| `pend11_s2` | 0.610 | 0.945 | -0.334 | 0.532 | 0.261 | +0.271 | check / check |
| `pend11_s3` | 1.406 | 1.651 | -0.245 | 1.651 | 1.658 | -0.007 | check / check |

### Author Numerical Concordance
- Author reported ACF periods:
  - `pend10 s1–3`: 0.84 / 0.74 / 0.23 vs 0.91 / 0.79 / 0.25 s (reproduced: 0.839/0.741/0.232 vs 0.910/0.787/0.245 s).
  - `pend11 s1–3`: 0.83 / 0.53 / 1.65 vs 0.83 / 0.26 / 1.66 s (reproduced: 0.830/0.532/1.651 vs 0.831/0.261/1.658 s).
- Excluding the single unstable pair where estimators flag `check` and disagree (`pend11_s2`):
  - $|\Delta T_{\text{acf}}| \in \{0.071, 0.047, 0.013, 0.002, 0.007\}\text{ s}$.
  - Mean $|\Delta T_{\text{acf}}| = \mathbf{0.028\text{ s}}$ (author: 0.00 to 0.07 s).
  - Seed-to-seed period spread spans **0.23 s to 1.66 s** (range 1.43 s, SD = 0.42 s).
  - The sampler schedule shifts the period by $< 0.03\text{ s}$ on average, which is **< 2%** of the seed-induced variance.

---

## 4. Physical Period Ground-Truth Comparison

Real physical periods from GAUGE motion capture:
- `pend10`: **1.17 s**
- `pend11`: **1.18 s**

| Pair | Real $T$ | $|T_{\text{nv}} - T_{\text{real}}|$ | $|T_{\text{kar}} - T_{\text{real}}|$ | Result |
|:---|:---:|:---:|:---:|:---|
| `pend10_s1` | 1.17 s | 0.331 s | 0.260 s | Neither recovers real period |
| `pend10_s2` | 1.17 s | 0.429 s | 0.383 s | Neither recovers real period |
| `pend10_s3` | 1.17 s | 0.938 s | 0.925 s | Severe tracking breakdown (period < 0.25 s) |
| `pend11_s1` | 1.18 s | 0.350 s | 0.349 s | Identical error (~0.35 s too fast) |
| `pend11_s2` | 1.18 s | 0.648 s | 0.919 s | Severe breakdown in both arms |
| `pend11_s3` | 1.18 s | 0.471 s | 0.478 s | Identical error (~0.47 s too slow) |

**Conclusion on Physics**: NVIDIA's sampler schedule does not bring Cosmos3-Nano closer to real physical gravity or pendulum mechanics. In 0/12 clips does the model recover the true natural period ($1.17\text{--}1.18\text{ s}$).

---

## 5. Artifacts and Evidence

- Complete results JSON: [`replication_results.json`](file:///home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/replication_results.json)
- Script: [`audit_sampler.py`](file:///home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/audit_sampler.py)
- QC Montages with amplified difference maps:
  - [`qc_montage_pend10_s1.jpg`](file:///home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/qc/qc_montage_pend10_s1.jpg)
  - [`qc_montage_pend10_s2.jpg`](file:///home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/qc/qc_montage_pend10_s2.jpg)
  - [`qc_montage_pend10_s3.jpg`](file:///home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/qc/qc_montage_pend10_s3.jpg)
  - [`qc_montage_pend11_s1.jpg`](file:///home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/qc/qc_montage_pend11_s1.jpg)
  - [`qc_montage_pend11_s2.jpg`](file:///home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/qc/qc_montage_pend11_s2.jpg)
  - [`qc_montage_pend11_s3.jpg`](file:///home/sha/devel/cosmos-swarm/work/rahul-5-agy/task204_sampler_audit/qc/qc_montage_pend11_s3.jpg)
