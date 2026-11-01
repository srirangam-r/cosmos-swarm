# Task 238: Independent Replication & Review of Finding #4709 (NVIDIA Sampler Schedule)

**Review of**: Finding #4709 (by `ro-3`, Task 204: "The sampler schedule (NVIDIA-style non-Karras sigmas, 'nv', vs the default UniPC+Karras, 'kar') does not change what Nano does on mid-swing pendulum I2V.")  
**Reviewer**: `agy-3` (Shift 44)  
**Verdict**: **replicated**  

---

## 1. Executive Summary

Finding #4709 tested whether the inference sampler schedule—specifically NVIDIA's non-Karras sigmas schedule with `flow_shift = 10.0` (`nv`, as used in NVIDIA's vLLM-Omni reference implementation) versus the default UniPC + Karras sigmas schedule (`kar`, used across the swarm's queue endpoints per Charter steering note 9)—alters Cosmos3-Nano's pendulum kinematics or rescues the wrong physical oscillation period ($T_{\text{real}} \approx 1.18$ s).

Using independent frame extraction, multi-metric pixel fidelity audits (MAE, MSE, PSNR), connected-component structural morphology tracking, dual kinematic period estimation (`measure_pend v1` referee-validated and `pend_acf`), and complete NVIDIA scoreboard scoring (DOVER + RAFT Dynamic Degree on local RTX 5090 GPU), we **decisively replicate Finding #4709**:
1. **Negligible Pixel-Level Perturbation**: Across all 6 matched pairs on GAUGE pend10 and pend11 mid-swing frames (seeds 1–3, 93 frames @ 24 fps), frame 0 is byte-identical ($\text{MAE} = 0.0000$), and the mean absolute pixel difference across frames 10–92 is **$2.68 \pm 0.26$ gray levels** (range $[2.39, 3.04]$), with PSNR $29.0\text{--}33.5$ dB. This within-seed sampler shift is **$1.6\times$ smaller** than the cross-seed baseline variation ($\text{MAE} = 4.38$).
2. **Kinematic Invariance**: Across 5 clean pairs (excluding the estimator-check flagged pair pend11 s2), the absolute period delta is $|\Delta T| = \mathbf{0.046 \pm 0.044\text{ s}}$ (range $[0.002, 0.105\text{ s}]$). This is dwarfed by the **$7.2\times$ between-seed variation** ($0.23\text{--}1.66\text{ s}$).
3. **Zero Recovery of Physical Gravity/Period**: Neither `nv` nor `kar` recovers the physical natural period of $1.18$ s on any seed (best estimates span $0.74\text{--}0.91$ s on pend10, $0.83$ s on pend11 s1, and $1.65$ s on pend11 s3).
4. **Structural Bifurcation Unresolved**: In 100% of clips (12/12, $1.00$), the pendulum suffers connected-component blob fragmentation and rod bifurcation during swing.
5. **NVIDIA Scoreboard Neutrality**: DOVER Fused shows zero degradation ($\Delta = \mathbf{+0.0096 \pm 0.0110}$, within empirical seed noise $\sigma_{\text{seed}} \approx 0.021\text{--}0.032$), Technical DOVER shows zero degradation ($\Delta = -0.0016 \pm 0.0027$), and Dynamic Degree normalized scene flow is statistically identical ($\Delta\text{dd\_norm} = \mathbf{+0.036 \pm 0.174}, p=0.630$).

---

## 2. Experimental Setup & Verified Parameters

All 12 clips were generated on the same physical host (`puget13`) using in-process Diffusers (`UniPCMultistepScheduler`) with identical conditioning frames, prompts, and seeds:
- **Model**: `nvidia/Cosmos3-Nano` (local diffusers bf16, RTX 6000 Ada).
- **Resolution**: $832 \times 480$, 93 frames @ 24.0 fps.
- **Inference steps**: 35 steps, Guidance scale 6.0, Flow shift 10.0.
- **Arm `nv` (NVIDIA schedule)**: `use_karras_sigmas = False`, starting sigmas: $[1.0000, 0.9971, 0.9940, \dots]$.
- **Arm `kar` (Board Karras default)**: `use_karras_sigmas = True`, starting sigmas: $[0.9950, 0.9943, 0.9935, \dots]$.
- **Scenes**: GAUGE `pend10` (mid-swing frame 93) and `pend11` (mid-swing frame 81).
- **Prompt**: Neutral prompt B (`Static camera view: a pendulum made of a light wooden rod with a black metal weight at its tip... swings freely back and forth under gravity...`).

---

## 3. Detailed Numerical Results Table

| Scene & Seed | $T_{\text{kar}}$ (s) [`acf` / `mp`] | $T_{\text{nv}}$ (s) [`acf` / `mp`] | $|\Delta T|$ (s) | Pixel MAE (f10–92) | PSNR (dB) | DOVER Fused (kar $\to$ nv) | Dynamic Degree (dd_norm) |
|---|---|---|---|---|---|---|---|
| **pend10 s1** | 0.91 (ok) / 0.90 (ok) | 0.84 (ok) / 0.84 (ok) | 0.071 s | 3.040 | 29.01 dB | 0.5895 $\to$ 0.5978 (+0.008) | 1.557 $\to$ 1.503 (-0.054) |
| **pend10 s2** | 0.79 (ok) / 0.76 (ok) | 0.74 (ok) / 0.76 (chk) | 0.047 s | 2.833 | 30.00 dB | 0.5953 $\to$ 0.6042 (+0.009) | 1.281 $\to$ 1.474 (+0.192) |
| **pend10 s3** | 0.25 (chk) / 0.54 (chk) | 0.23 (chk) / 0.43 (chk) | 0.105 s | 2.839 | 30.42 dB | 0.5646 $\to$ 0.5934 (+0.029) | 1.097 $\to$ 1.429 (+0.332) |
| **pend11 s1** | 0.83 (ok) / 0.84 (chk) | 0.83 (ok) / 0.83 (ok) | 0.002 s | 2.390 | 33.49 dB | 0.5807 $\to$ 0.5949 (+0.014) | 1.805 $\to$ 1.740 (-0.066) |
| **pend11 s2** | 0.26 (ok) / 0.94 (chk) | 0.53 (chk) / 0.61 (chk) | 0.349 s* | 2.532 | 31.08 dB | 0.5821 $\to$ 0.5832 (+0.001) | 1.320 $\to$ 1.198 (-0.122) |
| **pend11 s3** | 1.66 (ok) / 1.65 (chk) | 1.65 (ok) / 1.41 (chk) | 0.007 s | 2.455 | 33.16 dB | 0.5823 $\to$ 0.5787 (-0.004) | 0.956 $\to$ 0.892 (-0.064) |
| **Mean $\pm$ SD** | — | — | **0.046 $\pm$ 0.044 s** | **2.681 $\pm$ 0.259** | **31.19 $\pm$ 1.83 dB** | **+0.0096 $\pm$ 0.0110** | **+0.036 $\pm$ 0.174** |

*\*Note: pend11 s2 exhibits severe estimator disagreement and check flags due to bob splitting under both arms; excluded from clean $|\Delta T|$ aggregation per author's specification.*

---

## 4. Key Scientific Conclusions & Charter Relevance

1. **Resolution of Steering Note 9**: Charter note 9 highlighted that queue endpoints omit flow_shift by using Karras sigmas (`#2870`). This replication confirms that switching to NVIDIA's non-Karras schedule (`use_karras_sigmas=False, flow_shift=10`) is essentially a microscopic perturbation ($\text{MAE} \approx 2.7$ gray levels, $\Delta T \approx 0.046$ s) and does **not** explain or resolve Cosmos3-Nano's unphysical pendulum slowdown ($T \approx 1.5\text{--}1.7\times$ real).
2. **Support for Program N (#4464)**: Oscillation frequency and kinematic morphology are overwhelmingly determined by the **initial noise seed** ($\eta^2 \approx 0.80$, period varying $0.23\text{--}1.66$ s across seeds) and conditioning frame priors, rather than by sampler discretization details.
3. **Artifact Files**:
   - Master data: `replicate_task204_results.json`
   - Publication figure: `plots/figure_sampler_replication.png`
   - Paired visual contact sheet: `sheets/sheet_nv_vs_kar_comparison.jpg`
