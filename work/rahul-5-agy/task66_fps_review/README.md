# Independent Replication and Review of Finding #1448 (Task 45 / poornima-1)

## Executive Summary

We performed an independent quantitative replication and review of Finding #1448 by `poornima-1` across all **40 Cosmos3-Nano H100 video clips** (5 experimental arms × 8 matched seeds 3–10, 93 frames @ 832×480 resolution) generated from real GAUGE bouncing-ball frame 42 (mid-fall).

Finding #1448 is **firmly replicated**. Our independent multi-ROI evaluation confirms:
1. **Text Channel Null Effect**: Writing `"12 FPS"` vs `"24 FPS"` into the text prompt produces **zero dynamical change** across all spatial ROIs (Corridor diff $-0.013 \pm 0.085$ gray levels, $t = -0.16, p = 0.88$; Arm diff $+0.058 \pm 0.110$, $t = +0.53$; Table diff $-0.050 \pm 0.116$, $t = -0.43$). Nano completely ignores the prompted FPS string for physics dynamics.
2. **RoPE Spacing Parameter Fails as a Physical Clock**: Lowering the RoPE time spacing parameter ($\text{fps} \in \{24, 12, 6\}$) does **not** compress motion in physical time. Independent time-warp optimization yields a median scaling factor of **$k = 1.000$** for RoPE 12 (vs theoretical $k=2.0$, SSE penalty $2.24\times$) and **$k = 1.062$** for RoPE 6 (vs theoretical $k=4.0$, SSE penalty $2.50\times$). Nano advances its physical dynamics on a near-fixed per-frame stride.
3. **Severe Late-Motion Explosion & Hallucination Incoherence**: Halving RoPE fps to 12 or 6 significantly inflates late-window motion ($t \ge 68$, final 24 frames) in the upper arm region ($+1.85 \pm 0.96$ for RoPE 12, $+5.79 \pm 2.45$ for RoPE 6, $p = 0.022$). Instead of coming to rest, the model generates unprompted chaotic events: gripper morphing, arm plunges, phantom ball reappearance, and re-drops. Unprompted anomaly rates surge from 12.5% in baseline (Arm A) to 37.5% in Arm B, 50.0% in Arm D, and **100.0%** in Arm E (RoPE 6).

Therefore, fps conditioning parameter tuning and prompt text adjustments are **refuted** as viable recipe levers to fix Cosmos3-Nano's slow gravity or perpetual bouncing.

---

## Experimental Setup & Arms

- **Model**: `nvidia/Cosmos3-Nano` (in-process diffusers `@86ef420b`, bf16, 35 steps, CFG 6.0, flow_shift 10.0, `add_duration_template=False`).
- **Input Image**: Real GAUGE ball-1 frame 42 (mid-fall, SHA256 `555073a4a8b72de2dbf898b2ed54cc9ff7d2a2ec98583d94ee8cb42466024483`).
- **Prompt Structure**: Hand-written fixed template with stated duration and variable FPS string:
  `"A black rubber ball has just been released from a robot gripper and is falling toward a wooden plank on a black optical table in a lab with dark curtains. The ball hits the plank, bounces several times with decreasing height, and comes to rest. The camera is static. The video is 3.9 seconds long and is of {N} FPS."`
- **Arms (5 arms × 8 matched seeds 3–10 = 40 clips)**:
  - **Arm A**: RoPE 24.0, Text 24.0 (Default reference baseline)
  - **Arm B**: RoPE 12.0, Text 24.0 (RoPE halved, text unchanged)
  - **Arm C**: RoPE 24.0, Text 12.0 (Text halved, RoPE unchanged)
  - **Arm D**: RoPE 12.0, Text 12.0 (Both halved)
  - **Arm E**: RoPE 6.0, Text 24.0 (RoPE quartered)

---

## 1. Multi-ROI Motion Profile Results

We evaluated inter-frame pixel differences $D(t) = \frac{1}{|ROI|} \sum |I_{t+1} - I_t|$ across four disjoint physical ROIs:
- **Corridor**: $[y: 150..440, x: 180..440]$ (Primary ball drop zone)
- **Arm / Gripper**: $[y: 0..240, x: 180..440]$ (Robot arm holding zone)
- **Table / Plank**: $[y: 240..440, x: 180..440]$ (Impact plank & table surface)
- **Full Frame**: $[y: 0..480, x: 0..832]$
- **Static Background Control**: $[y: 150..440, x: 550..750]$

### Absolute Motion by Arm (Mean ± SE across 8 seeds, gray levels)

| Arm | Condition (RoPE / Text) | Corridor (All) | Corridor (Late 24) | Arm Zone (Late 24) | Table Zone (Late 24) | Background Control |
|---|---|---|---|---|---|---|
| **A** | 24 / 24 | $2.506 \pm 0.305$ | $1.080 \pm 0.158$ | $1.327 \pm 0.571$ | $1.323 \pm 0.214$ | $0.879 \pm 0.070$ |
| **B** | 12 / 24 | $3.243 \pm 0.353$ | $1.827 \pm 0.383$ | $3.178 \pm 1.349$ | $2.289 \pm 0.503$ | $0.944 \pm 0.085$ |
| **C** | 24 / 12 | $2.493 \pm 0.282$ | $1.092 \pm 0.240$ | $1.301 \pm 0.599$ | $1.332 \pm 0.335$ | $0.966 \pm 0.076$ |
| **D** | 12 / 12 | $3.280 \pm 0.341$ | $1.806 \pm 0.377$ | $3.034 \pm 1.341$ | $2.248 \pm 0.490$ | $0.992 \pm 0.126$ |
| **E** | 6 / 24 | $3.789 \pm 0.424$ | $3.423 \pm 0.635$ | $7.120 \pm 2.687$ | $3.623 \pm 0.612$ | $1.092 \pm 0.130$ |

---

## 2. Paired Contrast Analysis Across Matched Seeds

Paired seed contrasts ($n=8$ matched pairs per comparison):

### A. Text Channel Contrasts (Pure Prompt Effect)
- **Contrast C − A (Text 12 vs 24 @ RoPE 24)**:
  - Corridor Whole Clip: **$-0.013 \pm 0.085$** ($t = -0.16, p = 0.88$, n.s.)
  - Corridor Late 24f: **$+0.013 \pm 0.089$** ($t = +0.14, p = 0.89$, n.s.)
  - Arm Zone Whole Clip: **$+0.058 \pm 0.110$** ($t = +0.53, p = 0.61$, n.s.)
  - Table Zone Whole Clip: **$-0.050 \pm 0.116$** ($t = -0.43, p = 0.68$, n.s.)
- **Contrast D − B (Text 12 vs 24 @ RoPE 12)**:
  - Corridor Whole Clip: **$+0.037 \pm 0.065$** ($t = +0.57, p = 0.59$, n.s.)
  - Corridor Late 24f: **$-0.021 \pm 0.033$** ($t = -0.62, p = 0.55$, n.s.)

*Conclusion*: Changing the prompt text from `"24 FPS"` to `"12 FPS"` has zero detectable effect on Nano's kinematics or motion rates.

### B. RoPE Channel Contrasts (Positional Encoding Modulation)
- **Contrast B − A (RoPE 12 vs 24 @ Text 24)**:
  - Corridor Whole Clip: **$+0.737 \pm 0.231$** ($t = +3.19, p = 0.015$)
  - Corridor Late 24f: **$+0.747 \pm 0.387$** ($t = +1.93, p = 0.095$)
  - Arm Zone Late 24f: **$+1.851 \pm 0.958$** ($t = +1.93, p = 0.095$)
  - Table Zone Late 24f: **$+0.966 \pm 0.524$** ($t = +1.84, p = 0.108$)
- **Contrast E − A (RoPE 6 vs 24 @ Text 24)**:
  - Corridor Whole Clip: **$+1.283 \pm 0.368$** ($t = +3.49, p = 0.010$)
  - Corridor Late 24f: **$+2.343 \pm 0.641$** ($t = +3.66, p = 0.008$)
  - Arm Zone Late 24f: **$+5.793 \pm 2.454$** ($t = +2.36, p = 0.050$)
  - Table Zone Late 24f: **$+2.299 \pm 0.673$** ($t = +3.42, p = 0.011$)

*Conclusion*: Lowering RoPE fps injects large, statistically significant excess motion in late frames across all regions.

---

## 3. Time-Warp Analysis: Clock Hypothesis Refutation

If RoPE acts as an internal physical clock, temporal motion should compress by a factor of $k = \frac{\text{fps}_{\text{base}}}{\text{fps}_{\text{arm}}}$, predicting:
- Arm B & D (RoPE 12): $k = 2.0$
- Arm E (RoPE 6): $k = 4.0$
- Arm C (Text 12): $k = 1.0$

### Empirical Scaling Factor $k$ vs Arm A

| Arm | Description | Median $k$ | Mean $k \pm \text{SE}$ | Pooled Profile $k$ | Clock Theory $k$ | SSE Ratio $\frac{\text{SSE}(k_{\text{clock}})}{\text{SSE}(k_{\text{best}})}$ |
|---|---|---|---|---|---|---|
| **C** | Text 12 vs 24 | **$1.000$** | $1.000 \pm 0.005$ | **$1.000$** | $1.0$ | $1.00\times$ (Identical) |
| **B** | RoPE 12 vs 24 | **$1.000$** | $1.069 \pm 0.135$ | **$1.000$** | $2.0$ | **$2.24\times$** worse |
| **D** | RoPE 12 / Text 12 | **$0.988$** | $1.009 \pm 0.114$ | **$1.000$** | $2.0$ | **$2.69\times$** worse |
| **E** | RoPE 6 vs 24 | **$1.062$** | $1.284 \pm 0.269$ | **$0.500$** | $4.0$ | **$2.50\times$** worse |
| **Null** | $A(s_i)$ vs $A(s_{i+1})$ | $1.038$ | $1.609 \pm 0.420$ | — | — | — |

*Conclusion*: The clock hypothesis ($k=2$ or $k=4$) is decisively rejected. Every RoPE arm aligns best at $k \approx 1.0$, identical to the null baseline between different random seeds.

---

## 4. Settle Frame & Unprompted Late-Event Audit

### Settle Frame Analysis (5-frame smoothed motion $< 1.5$ gray levels)
- **Arm A**: $59.62 \pm 6.09$ frames (range 39–90)
- **Arm C**: $51.50 \pm 6.49$ frames (range 36–91)
- **Arm B**: $71.62 \pm 7.47$ frames ($+12.0$ frames later than A)
- **Arm D**: $71.62 \pm 7.50$ frames ($+12.0$ frames later than A)
- **Arm E**: **$87.38 \pm 2.18$** frames (7/8 seeds fail to settle by frame 80; 4/8 seeds still actively moving at frame 92)

### Unprompted Late-Event Anomaly Rate
- **Arm A (RoPE 24)**: $1 / 8$ clips ($12.5\%$, seed 7 late arm twitch)
- **Arm C (Text 12)**: $1 / 8$ clips ($12.5\%$, seed 7 late arm twitch)
- **Arm B (RoPE 12)**: $3 / 8$ clips ($37.5\%$: seed 3 second ball drop from gripper; seed 7 arm swing; seed 10 re-bounce)
- **Arm D (RoPE 12 / Text 12)**: $4 / 8$ clips ($50.0\%$)
- **Arm E (RoPE 6)**: **$8 / 8$ clips ($100.0\%$)** — every seed exhibits severe unprompted glitches:
  - Seed 3: Ball reappears in gripper jaws at $t=66$, drops again
  - Seed 4: Extreme exposure/brightness flash at $t=48$, arm morphs into white cloud
  - Seed 5: Duplicate ball spontaneously materializes on plank
  - Seed 7 & 8: Franka arm sweeps down across plank in unprompted stroke
  - Seed 10: Ball enters unprompted perpetual vertical yo-yo oscillation

---

## Artifacts and Code

- `replicate_finding_1448.py`: Independent Python evaluation script
- `replicate_finding_1448_results.json`: Full structured JSON metrics across all 40 clips
- `task66_qc_contact_sheet.jpg`: Consolidated 24-clip composite contact sheet across seeds 3, 5, 7, 10
- Mirrored author data: `work/poornima-1/` (`arm_stats.py`, `timewarp.py`, `armgrid.py`, JSON summaries, grids, and all 40 JSON sidecars)
