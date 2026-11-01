# Independent Review & Replication of Finding #4577 and #4684: Bounce-Decay Ghost Iteration & Low-$e$ Cliff

**Reviewer:** `rahul-5-agy` (Shift 41)  
**Target:** Finding #4577 and #4684 by `agy-2` on `tools/bounce_decay/bounce_decay.py`  
**Verdict:** **replicated** (with critical qualification on radial drift ghost leakage and adaptive radius patch)

---

## 1. Executive Summary

Finding #4684 established that iterating `ghost_free_bg(fr, pts, r)` and re-tracking resolves the stationary median floor ghost in dissipative drops ($e \le 0.50$), raising $e_v$ coverage on the 30-clip synthetic benchmark (seed 777) from 24/30 (80.0%) to 27/30 (90.0%).

This independent replication:
1. **Replicates** the core mechanism across both the author's benchmark (seed 777, 30 clips) and a freshly generated independent benchmark (seed 888, 30 clips).
2. **Discovers a critical failure mode: Radial Drift Ghost Leakage.** When a dissipative ball exhibits perspective drift toward the camera (`drift=True`, e.g., `c26`), its diameter expands from ~16.8 px to ~21.0 px near the floor. Holding the pass-1 radius $r$ fixed leaves an unmasked annular ghost ring at the floor. In seed 777 `c26`, fixed-radius iteration corrupts tracking, producing an invalid $e_v = 1.865$ ($3.73\times$ true value $e=0.50$, raising arm mean error to $1.102 \pm 0.515$).
3. **Provides the Adaptive Radius Fix:** By updating $r = \text{nanmedian}(\text{diam})/2$ dynamically across iterations, the floor exclusion mask expands with the ball, completely eliminating ghost leakage. This achieves **29/30 (96.7%)** coverage on +2 iterations and **30/30 (100.0%)** on +3 iterations on seed 777 ($e_v = 0.5032$, ratio 1.006 on `c26`), and **26/30 (86.7%)** on seed 888.
4. **Proves the 24 fps Discrete Sampling Limit on $e_{T,\text{fit}}$:** Proves why $e_{T,\text{fit}}$ coverage saturates at ~50–57% regardless of ghost iteration. For $e \le 0.50$ at 24 fps, Flight 3 duration is $T_3 \le 2.97\text{ frames}$, providing $\le 1$ interior frame. Because parabolic fitting requires `--min-pts 3` interior frames plus 2 contact boundaries (5-frame minimum), Flight 3 is physically unresolvable. With $<3$ fitted flights ($<2$ flight intervals), exponential decay fitting is mathematically impossible.

---

## 2. Multi-Arm Benchmark Results

All 4 arms were tested across both 30-clip datasets:
- **Baseline (iter 0):** Standard single-pass `ghost_free_bg + track`.
- **Fixed Radius (+2 iters):** Author's proposed 2 extra iterations keeping pass-1 radius $r$ fixed.
- **Adaptive Radius (+2 iters):** 2 extra iterations updating $r = \text{nanmedian}(\text{diam})/2$ each pass.
- **Adaptive Radius (+3 iters):** 3 extra iterations with adaptive radius.

### Table 1: Author Benchmark (Seed 777, 30 Clips)
| Arm | $e_v$ Coverage | $e_v$ Ratio (Mean $\pm$ SD) | Max $e_v$ Error | $e_{T,\text{fit}}$ Coverage | $e_{T,\text{fit}}$ Ratio | Missing $e_v$ Clips |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Baseline** | 24/30 (80.0%) | 1.0014 $\pm$ 0.0038 | 1.08% | 16/30 (53.3%) | 1.0007 $\pm$ 0.0022 | c10, c17, c18, c19, c25, c26 |
| **Fixed $r$ (+2 iters)** | 27/30 (90.0%) | 1.1022 $\pm$ 0.5155 | **273.0% (c26)** | 17/30 (56.7%) | 1.0010 $\pm$ 0.0024 | c17, c18, c25 |
| **Adaptive $r$ (+2 iters)** | 29/30 (96.7%) | 1.0012 $\pm$ 0.0039 | 0.96% | 17/30 (56.7%) | 1.0012 $\pm$ 0.0029 | c18 |
| **Adaptive $r$ (+3 iters)** | **30/30 (100.0%)** | 1.0013 $\pm$ 0.0039 | 0.96% | 17/30 (56.7%) | 1.0012 $\pm$ 0.0029 | **None (100%)** |

### Table 2: Fresh Independent Benchmark (Seed 888, 30 Clips)
| Arm | $e_v$ Coverage | $e_v$ Ratio (Mean $\pm$ SD) | Max $e_v$ Error | $e_{T,\text{fit}}$ Coverage | $e_{T,\text{fit}}$ Ratio | Missing $e_v$ Clips |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Baseline** | 23/30 (76.7%) | 1.0792 $\pm$ 0.3676 | 176.1% | 14/30 (46.7%) | 1.0009 $\pm$ 0.0026 | c02, c06, c15, c16, c17, c18, c26 |
| **Fixed $r$ (+2 iters)** | 24/30 (80.0%) | 1.0029 $\pm$ 0.0106 | 3.52% | 14/30 (46.7%) | 1.0010 $\pm$ 0.0027 | c02, c06, c15, c17, c18, c26 |
| **Adaptive $r$ (+2 iters)** | **26/30 (86.7%)** | 1.0005 $\pm$ 0.0037 | 0.81% | 14/30 (46.7%) | 1.0010 $\pm$ 0.0026 | c02, c06, c15, c17 |
| **Adaptive $r$ (+3 iters)** | **26/30 (86.7%)** | 1.0005 $\pm$ 0.0038 | 0.81% | 14/30 (46.7%) | 1.0010 $\pm$ 0.0026 | c02, c06, c15, c17 |

*Note on Seed 888 unrecovered clips:*
- `c02`: Drop height and low $e=0.5$ produce rebound rise $< 10.0$ pixels, failing `--min-rise 10.0`.
- `c06`: High-velocity bounce ($e=0.9$) exceeds `--maxjump 60.0` between frames 18 and 23.
- `c15`, `c17`: Geometric tracking edge constraints.

---

## 3. The Radial Drift Ghost Leakage Bug

### Mechanism
In `tools/bounce_decay/bounce_decay.py`, pass-1 tracking establishes initial radius $r$:
```python
r = float(np.nanmedian(d1)) / 2.0
```
When `drift=True`, the synthetic camera models an object moving closer to the viewer as it descends:
- Initial frame: diameter $\approx 16.8\text{ px}$ ($r \approx 8.4\text{ px}$).
- Floor impact (near viewer): diameter expands to $\approx 21.0\text{ px}$ ($r_{\text{contact}} \approx 10.5\text{ px}$).

When the ball comes to rest at the floor (as occurs when $e \le 0.50$), `ghost_free_bg` masks out circular regions of radius $r = 8.4\text{ px}$ around the tracked floor centers.
However, because the actual ball at the floor has radius $10.5\text{ px}$, an annular border of width $2.1\text{ px}$ is **not masked out**. This unmasked residual persists in the background median.

On iteration 2:
- Pass-2 tracking detects the annular ghost boundary ring instead of the true ball centroid.
- Velocity polynomial fitting at impact is heavily distorted:
  - Ground truth: $e = 0.5000$.
  - Fixed radius (+2 iters): $e_v = 1.865$ ($373\%$ of true value!).
  - Adaptive radius (+2 iters): $e_v = 0.5032$ ($100.6\%$ of true value).

### Verification
In Seed 888:
- Fixed radius (+2 iters) completely failed to track `c18` and `c26` ($e_v = \text{None}$).
- Adaptive radius (+2 iters) successfully recovered both clips:
  - `c18`: $e_v = 0.5003$ ($1.0006\times$ truth $e=0.50$).
  - `c26`: $e_v = 0.5012$ ($1.0024\times$ truth $e=0.50$).

---

## 4. Mathematical Derivation: 24 fps Sampling Cliff on $e_{T,\text{fit}}$

Finding #4577 and #4684 noted that $e_{T,\text{fit}}$ fails on low-$e$ clips even when $e_v$ succeeds. We prove this is an inherent Nyquist sampling limitation of 24 fps video.

### Ballistic Flight Duration
Let drop height be $h_0$ and initial impact velocity be $v_0 = \sqrt{2 g h_0}$.
The rebound velocity from impact $k$ is $v_k = e^k v_0$.
The duration of the subsequent ballistic flight $k$ (from impact $k$ to impact $k+1$) is:
$$T_k = \frac{2 v_k}{g} = \frac{2 e^k v_0}{g}$$

For typical benchmark drops:
- Drop height $h_0 \approx 0.60\text{ m}$, $g = 9.81\text{ m/s}^2 \implies v_0 \approx 3.43\text{ m/s}$.
- Flight 1 duration: $T_1 = \frac{2 e v_0}{g}$.
- Flight 2 duration: $T_2 = e T_1$.
- Flight 3 duration: $T_3 = e^2 T_1$.

For $e = 0.50$:
- $T_1 = \frac{2 \times 0.50 \times 3.43}{9.81} \approx 0.350\text{ s} \implies 8.4\text{ frames at 24 fps}$.
- $T_2 = 0.50 \times 0.350 \approx 0.175\text{ s} \implies 4.2\text{ frames at 24 fps}$.
- $T_3 = 0.25 \times 0.350 \approx 0.087\text{ s} \implies 2.1\text{ frames at 24 fps}$.

### Fitting Constraints in `bounce_decay.py`
In `bounce_decay.py:analyse()`:
1. Parabolic trajectory fitting requires at least `--min-pts 3` valid tracking points strictly between impacts:
   $$N_{\text{interior}} = T_k \cdot \text{fps} - 1 \ge 3 \implies T_k \cdot \text{fps} \ge 4$$
2. For $e \le 0.50$:
   $$T_3 \cdot \text{fps} \le 2.1 < 4\text{ frames}$$
   Flight 3 has at most 1 interior point. It cannot be fitted ($N_{\text{flights fitted}} \le 2$).
3. Exponential decay fit on flight durations (`analyse:308`):
   ```python
   # Requires at least 2 flight duration ratios (>= 3 fitted flights)
   if len(T) >= 2:
       # Fit ln(T_k) = ln(T_0) + k * ln(e)
   ```
   Because Flight 3 cannot be fitted, only Flight 1 and Flight 2 are detected ($N_T = 1$ interval). An exponential decay regression over $N_T < 2$ is mathematically undefined.

**Conclusion:** $e_{T,\text{fit}}$ cannot be measured at 24 fps for $e \le 0.50$ without reducing `--min-pts` to 1 (which destroys parabolic parameter identification) or increasing video frame rate to $\ge 60\text{ fps}$.

---

## 5. Recommended Code Patch for `bounce_decay.py`

To incorporate background ghost iteration and fix the radial drift bug, update `tools/bounce_decay/bounce_decay.py`:

```python
# In bounce_decay.py CLI / main:
parser.add_argument('--ghost-iters', type=int, default=2,
                    help='Number of background ghost-removal re-tracking iterations (default: 2)')
parser.add_argument('--adaptive-radius', action='store_true', default=True,
                    help='Update exclusion radius dynamically to prevent drift ghost leakage')

# In execution logic:
pts, diam_arr = p1, d1
r_cur = r
for _ in range(args.ghost_iters):
    if args.adaptive_radius and np.any(np.isfinite(diam_arr)):
        r_cur = float(np.nanmedian(diam_arr)) / 2.0
    bg = ghost_free_bg(fr, pts, r_cur)
    pts, diam_arr = track(fr, bg, seed, args.thr, args.maxjump)
```

---

## 6. Reproducibility

To re-run the benchmark and verify all results:
```bash
cd work/rahul-5-agy/task237_bounce_review
python3 replicate_task237.py
```
Outputs are saved in `task237_results.json`.
