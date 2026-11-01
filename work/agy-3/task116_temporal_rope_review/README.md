# Task 116: Independent Replication and Review of Finding #2622 (Temporal RoPE fast05 Multi-Seed Evaluation)

## Executive Summary

We performed an independent multi-cue kinematic replication and statistical review of **Finding #2622** (Task 101, `poornima-1`), which retracted Finding #2239 (Task 92). Finding #2239 had provisionally claimed that editing temporal RoPE inverse frequencies (`fast05`, $j=0,3 \times 0.5$) damped bouncing ball motion ($\Delta D = -0.46 \pm 0.12$).

Our independent replication confirms poornima-1's retraction and formalizes the negative result:
1. **Statistical Null on Fresh Seeds ($n=8$ matched pairs, seeds 4–7)**:
   - `fast05` vs `base`: $\Delta D = \mathbf{-0.077 \pm 0.085}$ (95% bootstrap CI $[-0.251, +0.057]$, $t = -0.908, p = 0.394$, n.s.). The claimed $-0.46$ damping effect is completely refuted as seed noise on seeds 1–3.
   - Single-component dose `j0x05` ($j=0$ only $\times 0.5$): $\Delta D = -0.052 \pm 0.100$ ($t = -0.524, p = 0.617$, n.s.).
   - Strong dose `j0x025` ($j=0$ only $\times 0.25$): $\Delta D = +0.012 \pm 0.109$ ($t = +0.112, p = 0.914$, n.s.).
2. **Zero Dissipative Settling (Pooled Seeds 1–7, $n=28$ clips)**:
   - Settled rate at clip end ($y > 300\text{ px}$, $\Delta y < 3\text{ px/f}$): **0.0% (0 / 14)** in `base`, **0.0% (0 / 14)** in `fast05`.
   - Energy gain rate (apex height rising above real gripper release height $y < 110\text{ px}$ after frame 40): **$25.0\%$ (3/12)** in `base` vs **$45.5\%$ (5/11)** in `fast05`! Temporal RoPE edits increase the probability of unphysical energy inflation ($e_v > 1.0$).
3. **Artifact Analysis & Seed Dominance**:
   - **Seed 4 (Gripper Re-Tethering)**: In 4/4 arms across both inputs (`b1dd33` and `b3dd35`), Seed 4 pulls the ball up on an elastic tether back into the gripper jaws ($y \approx 70\text{--}105\text{ px}$).
   - **Seed 6 (Energy Injection)**: `base` settles low on the plank ($y = 301$ and $309\text{ px}$), but `fast05` disrupts low rest and injects wild bounces ($y = 148$ and $96\text{ px}$).
   - **Seed 5 & 7 (Tracking Failure)**: Ball swells toward the camera and rolls out of frame (Seed 5) or scatters (Seed 7).
4. **Tracker Survivorship (rog2 Challenge #2628 Verified)**:
   - In heavy doses `j0x025` and `j0x05`, tracker visibility drops to **0/8 (0.0%)** and **2/8 (25.0%)** high-confidence tracks ($vis \ge 0.85$). Identity tracking comparisons across doses are conditioned on a survivor subset.

---

## Statistical Evaluation

### Paired Differences on Fresh Seeds 4–7 ($n=8$ pairs)

| Arm | Description | Mean Base $D$ | Mean Arm $D$ | Paired $\Delta D \pm \text{SE}$ | 95% Bootstrap CI | $t$-statistic | $p$-value | Conclusion |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`fast05`** | $j=0,3 \times 0.5$ | $0.577 \pm 0.118$ | $0.500 \pm 0.094$ | **$-0.077 \pm 0.085$** | $[-0.251, +0.057]$ | $t = -0.908$ | $p = 0.394$ | **Null (Refutes #2239)** |
| **`j0x05`** | $j=0 \times 0.5$ | $0.577 \pm 0.118$ | $0.525 \pm 0.111$ | **$-0.052 \pm 0.100$** | $[-0.253, +0.098]$ | $t = -0.524$ | $p = 0.617$ | **Null** |
| **`j0x025`** | $j=0 \times 0.25$ | $0.577 \pm 0.118$ | $0.589 \pm 0.119$ | **$+0.012 \pm 0.109$** | $[-0.202, +0.192]$ | $t = +0.112$ | $p = 0.914$ | **Null** |

---

## Pooled Trajectory Mechanics (Seeds 1–7)

Across all 14 `base` and 14 `fast05` clips evaluated:
- **Settled Fraction**: 0 / 14 (0.0%) vs 0 / 14 (0.0%).
- **Above Real $e=0.58$ ($y < 230\text{ px}$)**: 8 / 12 (66.7%) in `base` vs 8 / 11 (72.7%) in `fast05`.
- **Anomalous Energy Creation ($y < 110\text{ px}$)**: 3 / 12 (25.0%) in `base` vs 5 / 11 (45.5%) in `fast05`.
- **Held-at-Top Attractor ($y < 220\text{ px}$, $amp < 60\text{ px}$)**: 2 / 12 (16.7%) in `base` vs 2 / 11 (18.2%) in `fast05`.

---

## Tracker Survivorship Audit

| Arm | Total Clips | $vis \ge 0.85$ (High Conf) | $vis \ge 0.50$ (Standard) | Mean Visibility $\pm \text{SD}$ | Primary Failure Mode |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **`base`** | 8 | 4 / 8 (50.0%) | 5 / 8 (62.5%) | $0.615 \pm 0.428$ | Offscreen rollout (s5), scatter (s7) |
| **`fast05`** | 8 | 4 / 8 (50.0%) | 4 / 8 (50.0%) | $0.543 \pm 0.463$ | Offscreen rollout (s5), scatter (s7) |
| **`j0x05`** | 8 | 2 / 8 (25.0%) | 3 / 8 (37.5%) | $0.341 \pm 0.407$ | Visual morphing & scattering |
| **`j0x025`** | 8 | 0 / 8 (0.0%) | 2 / 8 (25.0%) | $0.256 \pm 0.264$ | Severe spatial deformation |

---

## Evidence & Traceability
- **Primary Data**: Mirrored from `swarm@board.tail0c526a.ts.net:~/jobs/poornima-1/task101/` to `work/agy-3/task116_temporal_rope_review/data/`.
- **Overlay Contact Sheets**: 32 overlay sheets in `sheets/*_ov.jpg`.
- **Analysis Code**: `independent_replication_task101.py`, `audit_temporal_rope.py`.
- **Master JSON Results**: `task116_temporal_rope_results.json`.
- **Publication Figure**: `plots/figure_temporal_rope_replication.png`.
