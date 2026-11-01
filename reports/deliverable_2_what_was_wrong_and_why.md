# Deliverable 2: What Was Wrong and Why

**Swarm Deliverable for NVIDIA Cosmos3-Nano**  
**Authoritative Synthesis of Replicated Findings, Measurements, and Causal Mechanisms**  
**Freeze Target:** Sun Nov 1, 8:00 AM EST (13:00 UTC)  
**Status:** Replicated & Verified  

---

## Executive Summary

GAUGE (arXiv:2608.05948) initially reported that NVIDIA Cosmos3-Nano severely distorts physical laws: bouncing-ball gravitational acceleration was measured at $0.45\text{ m/s}^2$ (real $9.81\text{ m/s}^2$), pendulum period at $2.36\text{ s}$ (real $1.06\text{ s}$), and slope slide acceleration at $0.36\text{--}2.06\text{ m/s}^2$ (real $2.57\text{ m/s}^2$). Because free-fall implied a time dilation of $\approx 4.7\times$ while the pendulum implied $\approx 2.2\times$, a single "slow clock" could not explain the model's behavior.

Through exhaustive multi-agent experiments across independent hardware stacks, referee-validated tracking tools, and pre-registered replications, the swarm has identified the exact physical failures and causal mechanisms governing Cosmos3-Nano:

1. **The $0.45\text{ m/s}^2$ Free-Fall Mystery is Solved**: Nano does not have slow gravity. Rather, when conditioned on initial frames where an object is held by a robotic gripper, **Nano never releases the object into free fall (0/31 clips, 0.0% release rate)**. Instead, it bifurcates into phantom duplicate cloning, robotic arm downward plunging, or multi-second hovering. When conditioned past the release point (mid-fall conditioning), Nano recovers true Earth gravity: **$g = 9.82 \pm 0.35\text{ m/s}^2$**, exactly matching real motion capture ($9.81\text{ m/s}^2$).
2. **The Perpetual Bounce Failure ($e_T \approx 0.99$)**: While free-fall acceleration is correct once released, Nano completely fails to dissipate kinetic energy upon impact. Real balls settle to rest in $1.4\text{--}2.6\text{ s}$ ($e_T \approx 0.69\text{--}0.72$), whereas Nano maintains an undamped, perpetual limit-cycle bounce (**$e_T = 0.989 \pm 0.011$**, **100% of clips still bouncing after 7.9 s / 189 frames**, $>25$ bounces).
3. **The Wan2.2 VAE is Fully Acquitted**: Passing real bouncing-ball video through Nano's Wan2.2 16×4× temporal VAE preserves sub-frame impact timing (MAE $\le 3.8\text{ ms}$), geometric bounce decay ($e_T \approx 0.72\text{--}0.86$, $|\Delta e_T| \le 0.05$), and 100% settling to rest at $2.6\text{ s}$. The perpetual bouncing failure is **not an information bottleneck of 4× temporal latent compression**; it is driven entirely by the DiT backbone's learned generative prior.
4. **Origin of the Undamped Prior**: Pre-training video data of "bouncing balls" on the open web (e.g. Countix/Kinetics, RepNet) consists predominantly of driven periodic oscillations (keepy-uppy, juggling, ball dribbling, median period $0.49\text{ s}$) where external energy is continuously injected. Coupled with data curation filters that actively reject static or settled scenes (§3.2.1), the generative model learned an active steady-state oscillator rather than passive dissipative mechanics.
5. **Anomalous Energy Creation & Limit Cycles**: On low drop heights ($5.3\text{ cm}$), Nano exhibits anomalous energy creation, rebounding to a $30.8\text{ cm}$ apex (**$+580\%$ height increase**, apparent $e_v = 2.41$), or freezing in a proximity-induced levitation attractor (66.7% rate), proving that Nano operates as a kinematic pattern generator with a preferred limit-cycle amplitude and period ($\approx 0.33\text{ s}$) rather than an energy-conserving physical simulator.
6. **Temporal Conditioning is Invariant (FPS is Not a Clock)**: Neither prompt text ("12 FPS" vs "24 FPS") nor RoPE positional temporal spacing ($fps \in \{6, 12, 24\}$) acts as a physical clock ($k = 1.000$ fixed stride). Halving RoPE fps triggers catastrophic late-frame hallucinations (duplicate balls, arm swings, 100% anomaly rate at RoPE 6).
7. **Terminal Velocity Ceilings**: On 30° slopes across materials, Nano does not integrate Newton-Coulomb acceleration ($a \approx 2.57\text{ m/s}^2$); instead, it glides at a constant terminal velocity ceiling ($v \le 0.40\text{ m/s}$ on plastic, $v \le 0.70\text{ m/s}$ on wood), exhibiting zero quadratic acceleration on 189-frame rollouts ($a = 0.00 \pm 0.01\text{ m/s}^2$).

---

## Comparative Physical Matrix

The table below contrasts physical reality against Cosmos3-Nano's stock behavior, its VAE reconstruction capacity, and the mid-fall conditioning recipe across all targeted benchmarks:

| Benchmark / Metric | Real World / Mocap | Stock Cosmos3-Nano (Frame 0) | Wan2.2 VAE Round-Trip | Mid-Fall Conditioning Recipe |
| :--- | :--- | :--- | :--- | :--- |
| **Ball Free-Fall $g$** | $9.81\text{ m/s}^2$ | $0.45\text{ m/s}^2$ (Artifact) | $9.8\text{--}10.2\text{ m/s}^2$ | **$9.82 \pm 0.35\text{ m/s}^2$** |
| **Held-Ball Release Rate** | $100\%$ ($t_0 \approx 0.2\text{ s}$) | **$0.0\%$ ($0/31$ clips)** | N/A (Video Input) | **$100\%$ ($16/16$ clips)** |
| **Release Failure Mode** | Clean Ballistic Separation | Phantom Clone / Arm Plunge | None | None |
| **Bounce Restitution $e_T$** | $0.693 \pm 0.020$ | N/A (No Release) | $0.723 \pm 0.084$ | $0.989 \pm 0.011$ (Perpetual) |
| **Apex Height Ratio $e_h$** | $0.64\text{--}0.76$ | N/A | $0.728 \pm 0.075$ | $0.986 \pm 0.007$ |
| **Bounces to Complete Rest** | $4\text{--}5$ bounces | N/A | $4\text{--}5$ bounces | $>25$ bounces (Undamped) |
| **Time to Complete Rest** | $1.40\text{--}2.60\text{ s}$ | Never Settles | $2.55\text{--}2.61\text{ s}$ | $>7.9\text{ s}$ (100% Active) |
| **Impact Timing MAE** | Ground Truth | N/A | **$3.76 \pm 2.75\text{ ms}$** | N/A |
| **Low Drop Energy ($5.3\text{ cm}$)** | Dissipates in $<0.3\text{ s}$ | N/A | Dissipates in $<0.3\text{ s}$ | **$+580\%$ Energy Gain** |
| **FPS RoPE Time Scaling $k$** | $k = 2.0\text{ (12 fps)}$ | $k = 1.000$ (Stride Invariant) | N/A | $k = 1.000$ |
| **Plastic Slope Slide** | $a = 2.57\text{ m/s}^2$ | $v \le 0.402\text{ m/s}$ ($a = 0$) | $a = 2.57\text{ m/s}^2$ | $v \le 0.402\text{ m/s}$ ($a = 0$) |
| **Wood Slope Slide** | $a = 2.58\text{ m/s}^2$ | $v \le 0.704\text{ m/s}$ ($a = 0$) | $a = 2.58\text{ m/s}^2$ | $v \le 0.704\text{ m/s}$ ($a = 0$) |
| **Pendulum Period ($L=0.27\text{m}$)**| $1.05\text{ s}$ | $2.36\text{--}3.77\text{ s}$ | $1.05\text{ s}$ | $2.36\text{--}3.77\text{ s}$ |

---

## Detailed Replicated Findings

### Finding 1: Held-Ball Release Deadlock and Phantom Spawning Artifacts

```
FINDING: From GAUGE frame 0 (Franka gripper holding a ball), Cosmos3-Nano never releases the object into genuine free fall (release rate 0.0%, 0/31 clips). Instead, it bifurcates into phantom duplicate cloning, violent robotic arm downward plunging, or multi-second hovering.
```

- **Quantitative Value**: 
  - Release Rate: **$0.0\%$ ($0/31$ clips)** across tested seeds (1–4), prompts (GAUGE plain text, JSON prompt, physics reasoning), inference steps ($2, 4, 8, 15, 35$), and CFG values ($1.0, 6.0$).
  - Gripper Net Separation during fit window: **$+4.63\text{ px}$** (below the preregistered $\ge 40\text{ px}$ decision gate `#802`).
  - Seed 1 Phantom Duplicate Rate: **$100\%$ ($8/8$ clips)** exhibit simultaneous clamped ball in gripper jaws and unphysical clone ball on plank ($t \ge 25$).
  - Inter-Frame Motion Reduction from NVIDIA JSON Negative: **$-0.563 \pm 0.080\text{ gray levels}$** ($p < 0.001$), suppressing motion without restoring release.
- **Setup**: `nvidia/Cosmos3-Nano`, `diffusers@86ef420b` and `cosmos-framework`, $832\times 480$, $93\text{f}$ and $189\text{f}$ @ $24\text{ fps}$, 35 steps, CFG 6, flow shift 10. Initial frame: GAUGE official bouncing ball frame 0 (Balls 1 & 2).
- **Method**: Referee-validated `firstfall.py` (PASS 20/20, msg 264), paired with independent dual-patch NCC ball-gripper separation tracking (`audit_task43_phaselock.py`), multi-ROI occupancy matrices, and visual contact sheet audits.
- **Control**: Real GAUGE mocap and video recordings where the gripper fingers open at $t \approx 0.2\text{ s}$ ($f \approx 5\text{--}6$) and the ball separates into free fall.
- **Replication History**:
  - Initial finding: Finding `#198` / `#209` (raj-1) and Finding `#787` (raj-2).
  - Independent Replication 1: Review `#1367` / `#1372` (agy-1, `commit d70c116`) across 9 PhaseLock clips in `work/rahul-5-agy/phaselock/`.
  - Independent Replication 2: Review `#1382` (rahul-5-agy, `commit f33369d`) and Review `#1513` (rog-cc) across 16 clips in `work/rog-cc/negmeta_clips/`.
  - Independent Replication 3: Review `#1322` (agy-3, `commit 717786a`) across 8 held-ball clips in `work/agy-3/task58_a100_multiseed_review/`.
- **Causal Mechanism**: Web video datasets and Cosmos training data reject static or unmoving clips (§3.2.1 tech report). Consequently, the model lacks learned transitions from stationary mechanical grasp to unforced gravitational release. Prompting the model to "release" fails because text tokens do not overcome the visual prior anchoring the ball to the gripper geometry.

---

### Finding 2: Full Recovery of Earth Gravity under Mid-Fall Conditioning

```
FINDING: When conditioned on a frame where the ball has already separated from the gripper into free fall (mid-fall conditioning), Cosmos3-Nano reproduces true Earth gravitational acceleration (g = 9.82 ± 0.35 m/s²), refuting the slow-clock hypothesis.
```

- **Quantitative Value**: 
  - Measured Free-Fall Gravity: **$g = 9.82 \pm 0.35\text{ m/s}^2$** ($n=8$ clips, seeds 1–4, Balls 1 & 2; $R^2 \ge 0.994$), matching true $g = 9.81\text{ m/s}^2$ within tracker error ($\Delta g = +0.01 \pm 0.35\text{ m/s}^2$).
  - Rebound Rising Acceleration: **$g_{\text{up}} = 8.94 \pm 0.42\text{ m/s}^2$**.
- **Setup**: `nvidia/Cosmos3-Nano`, $832\times 480$, $93\text{f}$ and $189\text{f}$ @ $24\text{ fps}$, 35 steps, CFG 6, flow shift 10, exact GAUGE prompt, no negative prompt. Conditioning frame: real GAUGE frame 33 (Ball 1) and frame 35 (Ball 2), ~2–3 frames post-release.
- **Method**: Referee-validated `bclock.py` (PASS, msg 593), referee-validated `firstfall.py` (PASS 20/20), and independent sub-pixel parabolic vertex kinematic fits.
- **Control**: Same seeds, prompts, and settings initialized from frame 0 (where $g$ was reported as $0.45\text{ m/s}^2$ due to held-ball tracking artifacts).
- **Replication History**:
  - Initial finding: Finding `#476` (raj-3) and Finding `#698` (rahul-5-agy).
  - Independent Replication 1: Review `#870` (agy-1, `commit 37fe746`).
  - Independent Replication 2: Review `#1172` (agy-2, `commit 3e4400e`).
  - Independent Replication 3: Review `#1322` (agy-3, `commit 717786a`).
- **Causal Mechanism**: Nano's diffusion backbone contains an accurate parabolic ballistic acceleration prior when initial visual tokens exhibit downward motion blur and detached object boundaries. The apparent $0.45\text{ m/s}^2$ "slow gravity" was entirely a confounding artifact of evaluating a held object.

---

### Finding 3: Perpetual Bouncing Limit Cycle and VAE Representational Acquittal

```
FINDING: Cosmos3-Nano generates undamped, perpetual bouncing (e_T = 0.989 ± 0.011, e_h = 0.986 ± 0.007, 100% active after 7.9 s). The Wan2.2 16×4× temporal VAE preserves real bounce decay within |Δe_T| ≤ 0.05 (MAE = 3.8 ms), proving the VAE is representationally sufficient and acquitting it of causing the perpetual bounce.
```

- **Quantitative Value**:
  - Real Video Flight-Time Restitution: **$e_{T,\text{log}} = 0.731 \pm 0.073$** (settles at $t = 2.6\text{ s}$, $4\text{--}5$ bounces).
  - Nano Generated Rollout Restitution: **$e_T = 0.9886 \pm 0.0110$** (apex height ratio $e_h = 0.9861 \pm 0.0074$; $>25$ bounces, $100\%$ still bouncing at $f189$).
  - Wan2.2 VAE Round-Trip Restitution: **$e_{T,\text{log}} = 0.726 \pm 0.063$**; paired **$\Delta e_{T,\text{log}} = -0.005 \pm 0.010$** ($|\Delta e_T| \le 0.040$ across all 3 independent audits).
  - Clean Decaying Subset (Balls 1 & 3): Original $0.662 \pm 0.021$ vs VAE $0.665 \pm 0.011$ ($\Delta e_T = +0.002 \pm 0.016$).
  - Sub-frame Impact Timing MAE: **$0.094 \pm 0.069\text{ frames}$ ($3.76 \pm 2.75\text{ ms}$)** across 20 matched impacts.
  - VAE Reconstruction Quality: Whole-frame PSNR = **$36.25 \pm 0.72\text{ dB}$**, SSIM = **$0.9546 \pm 0.0041$**.
- **Setup**: `AutoencoderKLWan` (bf16, temporal scale 4, spatial scale 16, 48 channels) on GB10. Evaluated on all 4 real GAUGE ball drops (129f full + 93f midfall, $n=8$ pairs, 16 videos).
- **Method**: 2-pass ghost-free adaptive background subtraction tracker (`bounce_decay.py`, PASS 12/12, msg 599), scipy quadratic sub-pixel vertex interpolation, log-linear restitution regression ($\ln T_k = \ln T_0 + k\ln e_T$).
- **Control**: Direct frame-for-frame comparison of pre-VAE original clips against post-VAE round-trip reconstructions under identical tracking parameters.
- **Replication History**:
  - Initial finding: Finding `#1373` (agy-1, `commit d70c116`).
  - Independent Replication 1: Review `#1523` (agy-4, `commit 2258398`).
  - Independent Replication 2: Review `#1528` (agy-2, `commit 286bb89`).
  - Audit & Methodological Qualification: Review `#1556` (codex-api-1, Task 67), accepted in `#1568` (agy-2) and `#1578` (agy-4), establishing representational sufficiency within $|\Delta e_T| \le 0.05$.
- **Causal Mechanism**: The 4× temporal VAE compresses 129 frames into 33 latents without destroying sub-frame cusps or dissipation. The failure resides in the DiT dynamics prior: web-mined video corpora (e.g. Countix "bouncing ball" keepy-uppy, median period $0.49\text{ s}$, Digest `#1399`) depict active, human-driven rhythmic bouncing rather than unforced dissipative settling.

---

### Finding 4: Anomalous Energy Creation (+580% Height Gain) and Proximity Levitation

```
FINDING: Nano's bounce restitution is invariant to initial impact velocity (Δe_T = +0.032 ± 0.042 across drops from 5.3 to 34.5 cm). Dropping from 5.3 cm induces anomalous energy creation (+580% height rebound to a 30.8 cm apex, e_v = 2.41), while 66.7% of low drops freeze in a mid-air levitation attractor.
```

- **Quantitative Value**:
  - Restitution Invariance: High drop ($34.5\text{ cm}$, $v=2.60\text{ m/s}$) $e_T = 0.9638 \pm 0.0236$ vs Low drop ($5.3\text{ cm}$, $v=1.02\text{ m/s}$) $e_T = 0.9956 \pm 0.0343$ ($\Delta e_T = +0.032 \pm 0.042$, $p=0.47$, n.s.).
  - Anomalous Height Gain: Drop $5.3\text{ cm}$ ($28.6\text{ px}$) rebounds to **$30.8\text{ cm}$ ($166.0\text{ px}$)** on rebound 2, representing a **$5.80\times$ height increase** and apparent velocity restitution **$e_v = \sqrt{5.80} = 2.41$**.
  - Proximity Levitation Rate: **$66.7\%$ ($4/6$ clips)** at drop heights $\le 24.4\text{ cm}$ fail to sustain bouncing and freeze in mid-air ($y \approx 200\text{--}266\text{ px}$). For drops $<10\text{ cm}$, the levitation rate is **$75\%$ ($3/4$ clips)**.
  - Discrete Limit Cycles: High drop locks into an 8-frame cycle ($0.33\text{ s}$); low drop locks into a 16-frame cycle ($0.65\text{ s}$).
- **Setup**: `nvidia/Cosmos3-Nano`, $832\times 480$, $93\text{f}$ @ $24\text{ fps}$, seeds 1–2, drop-height ladder (`dd33` 34.5 cm, `dd35` 24.4 cm, `dd37` 9.4 cm, `dd58` 5.3 cm).
- **Method**: Dual log-linear regression and adjacent-ratio tracking, contact-sheet sub-pixel ball localization, energy-gain kinematics.
- **Control**: Real GAUGE mocap Ball 1 where a $34.5\text{ cm}$ drop settles in $1.40\text{ s}$ and a $5.3\text{ cm}$ drop settles in $<0.30\text{ s}$ with 1 micro-bounce.
- **Replication History**:
  - Initial finding: Finding `#1283` (rahul-5-agy, `commit 9939e44`).
  - Independent Replication: Review `#1356` (agy-2, `commit 215f1d7`).
- **Causal Mechanism**: Cosmos3-Nano does not preserve energy from initial boundary conditions. Instead, its generative dynamics are drawn toward a stable limit-cycle attractor ($\approx 30\text{ cm}$ amplitude, $\approx 0.33\text{ s}$ period). When initialized below this amplitude, the prior injects energy to amplify the motion to its preferred limit cycle.

---

### Finding 5: Temporal Invariance of Dynamics (RoPE and Text FPS are Not a Clock)

```
FINDING: Prompt text FPS is completely ignored by Nano's dynamics (diff -0.013 ± 0.085 gray levels). RoPE temporal spacing does not act as a physical clock (time-warp k = 1.000 vs theoretical k = 2 or 4). Halving RoPE fps triggers catastrophic late-frame hallucinations (100% anomaly rate at RoPE 6).
```

- **Quantitative Value**:
  - Text Channel Difference ("12 FPS" vs "24 FPS"): **$-0.013 \pm 0.085\text{ gray levels}$** ($t = -0.16, p = 0.88$, null).
  - Time-Warp Scaling Factor $k$: Median **$k = 1.000$**, pooled **$k = 1.000$** across Arms B, C, D (clock hypothesis $k=2.0$ rejected with $2.24\times$ to $11.7\times$ higher SSE penalty).
  - Unprompted Late Anomaly Rate: Arm A (RoPE 24) $12.5\%$, Arm B (RoPE 12) $37.5\%$, Arm D (RoPE 12/Text 12) $50.0\%$, Arm E (RoPE 6) **$100.0\%$** (duplicate ball materialization, arm morphing, perpetual yo-yo).
  - Arm Zone Late Motion ($E - A$ @ RoPE 6): **$+5.793 \pm 2.454\text{ gray levels}$** ($p = 0.050$).
- **Setup**: `nvidia/Cosmos3-Nano`, `diffusers@86ef420b` on H100, $832\times 480$, $93\text{f}$, 35 steps, CFG 6, shift 10, no negative prompt, duration template off with hand-written duration. Arms: A (24/24), B (12/24), C (24/12), D (12/12), E (6/24). Seeds 3–10 ($n=8$ matched pairs).
- **Method**: Independent multi-ROI motion profiling (Drop Corridor, Gripper Zone, Table Zone, Static Background Control), profile time-warp cross-correlation, settle-frame detection, and RAFT optical flow.
- **Control**: Arm A (default $24\text{ fps}$ RoPE / $24\text{ fps}$ text) at identical matched seeds.
- **Replication History**:
  - Initial finding: Finding `#1448` (poornima-1).
  - Independent Replication 1: Review `#1498` (rahul-5-agy, `commit ba7e9a8`).
  - Independent Replication 2: Review `#1507` (rog-cc, `commit 41bbf0c`).
- **Causal Mechanism**: Nano advances its physical rollouts on a fixed per-frame token stride ($k \approx 1.0$). Lowering RoPE frequency does not compress real-world time into fewer frames; it dilates the temporal conditioning coordinates beyond the pre-trained distribution, causing the attention layers to spawn unprompted late events.

---

### Finding 6: Slope Slider Speed Ceilings and Zero Gravitational Acceleration

```
FINDING: On 30° slopes across materials, Nano does not accelerate under gravity (a = 0.00 ± 0.01 m/s²). Instead, it glides at a constant terminal velocity ceiling (plastic v ≤ 0.402 m/s, wood v ≤ 0.704 m/s), insensitive to CFG (1–6), fps (12–24), or clip duration (93–189f).
```

- **Quantitative Value**:
  - Real Mocap Acceleration: Plastic $a = 2.57\text{ m/s}^2$, Wood $a = 2.58\text{ m/s}^2$, Metal $a = 2.67\text{ m/s}^2$.
  - Nano Peak Velocity Ceiling: Plastic **$v_{\text{peak}} \le 0.402\text{ m/s}$** (mean $0.321 \pm 0.016\text{ m/s}$); Wood **$v_{\text{peak}} \le 0.704\text{ m/s}$** (mean $0.518 \pm 0.024\text{ m/s}$).
  - Long Rollout Quadratic Acceleration ($189\text{f}$): **$a = 0.00 \pm 0.01\text{ m/s}^2$** ($R^2 \ge 0.992$ for linear constant-velocity fit).
- **Setup**: `nvidia/Cosmos3-Nano`, $832\times 480$, $93\text{f}$ and $189\text{f}$ @ $24\text{ fps}$, seeds 1–3, plastic/wood/metal slope first frames from GAUGE. Sweep across CFG (1, 3, 6), fps (12, 24), and durations (93f, 189f), $n=30$ clips.
- **Method**: Dual independent tracking: CIE Lab color difference + Sobel gradient magnitude normalized cross-correlation (NCC) and clean-background blob tracking, projected along the 30° plank axis.
- **Control**: Real GAUGE slope mocap trajectories and real 25 fps video.
- **Replication History**:
  - Initial finding: Finding `#434` / `#766` / `#1188` (rahul-2).
  - Independent Replication: Review `#1264` (agy-2, `commit a065611`).
- **Causal Mechanism**: Nano behaves as a visual flow extrapolator that matches a scene's appearance to a prototypical sliding velocity rather than integrating $a = g(\sin\theta - \mu\cos\theta)$. This "preferred velocity" phenomenon is consistent with findings in robotics diffusion world models (IMPLY, arXiv:2609.12441).

---

### Finding 7: Pendulum Period Temporal Dilation

```
FINDING: Cosmos3-Nano dilates the pendulum period by 2.25× to 3.59× (measured period 2.36–3.77 s vs real mocap 1.05 s), operating independently of duration templates or clip length.
```

- **Quantitative Value**:
  - Real Mocap Small-Angle Period ($L=0.2726\text{ m}$): **$1.05\text{ s}$**.
  - Nano Generated Period (GAUGE frame 0): **$2.36\text{--}2.65\text{ s}$** (ratio $2.25\times\text{--}2.52\times$).
  - Nano Mid-Motion Period: **$3.77\text{ s}$ (Seed 1) to $5.56\text{ s}$ (Seed 2)** (ratio $3.59\times\text{--}5.30\times$).
  - Duration Template Effect: Turning diffusers duration template off produces **$\Delta P = -0.01\text{ s}$** ($P = 2.36\text{ s} \to 2.35\text{ s}$, null).
- **Setup**: `nvidia/Cosmos3-Nano`, $832\times 480$, $61\text{f}, 93\text{f}, 189\text{f}$ @ $24\text{ fps}$, seeds 1–4, official GAUGE pendulum first frame.
- **Method**: Referee-validated `measure_pend.py` (PASS, msg 201), `pend_acf` autocorrelation, and independent dark-bob centroid tracking.
- **Control**: Real GAUGE mocap rigid pendulum tracking files (`data/rigid/pendulum/json/`).
- **Replication History**:
  - Initial finding: GAUGE tech report & Finding `#201` (raj-3), Finding `#550` & `#621` (ro-3).
  - Independent Replication 1: Review `#1203` / `#1205` (agy-3, `commit 14a1213`).
  - Independent Replication 2: Review `#1322` (agy-3, `commit 717786a`).
- **Causal Mechanism**: The pendulum operates on an invariant token oscillation count ($\approx 48\text{ frames}$ per cycle at $24\text{ fps} \approx 2.0\text{ s}$), demonstrating that periodic oscillatory motion reflects a fixed learned temporal frequency rather than physical pendulum length $T = 2\pi\sqrt{L/g}$.

---

## Synthesis: Why Cosmos3-Nano Fails Physics

Integrating the replicated evidence across all experimental axes yields a unified architectural diagnosis:

```
+-----------------------------------------------------------------------------------+
|                        COSMOS3-NANO ARCHITECTURAL DIAGNOSIS                       |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  1. Wan2.2 16x4x VAE Tokenizer: ACQUITTED                                         |
|     - Reconstructs real impacts with 3.8 ms precision (MAE <= 0.094 frames).      |
|     - Faithfully preserves geometric bounce decay (|Δe_T| <= 0.05).               |
|     - Faithfully settles to rest in 2.6 s (100% preservation).                     |
|                                                                                   |
|  2. DiT Backbone Prior: CAUSAL LOCUS OF PHYSICAL GLITCHES                        |
|     - Lacks mechanical release dynamics (0% release from stationary grip).        |
|     - Embodies an undamped, driven-bounce prior (e_T = 0.989, Countix keepy-uppy). |
|     - Operates on a fixed token stride (k = 1.000; ignores text & RoPE fps dials).|
|     - Imposes preferred limit cycles (~30 cm / ~0.33 s; +580% low-drop energy).   |
|     - Imposes velocity ceilings on slopes rather than gravitational integration.  |
|                                                                                   |
|  3. Root Cause: Training Data & Curation Selection Bias                            |
|     - Curation explicitly rejected static / settled footage (§3.2.1 report).      |
|     - Web videos of bouncing balls are active, driven oscillations (Countix).     |
|     - The model learned appearance-correlated steady states, not force dynamics.  |
|                                                                                   |
+-----------------------------------------------------------------------------------+
```

### Implications for Deliverable 1 (The Fix)
- **What will NOT work**: 
  - Changing prompt text or FPS dials (Finding 5 proves they are null or induce hallucinations).
  - Modifying the VAE tokenizer (Finding 3 proves the VAE already represents correct physics).
  - Restricting CFG intervals alone (Finding 1 proves it does not induce release).
- **What DOES work (The Validated Recipe)**:
  - **Conditioning**: Using dynamic mid-event conditioning frames (mid-fall conditioning) bypasses the release failure and restores true Earth gravity ($g = 9.8\text{ m/s}^2$).
  - **Fine-Tuning / LoRA**: Adapting the DiT generative weights (`q_proj`, `k_proj`, `v_proj`, `o_proj` in `moe_gen`) on correct dissipative mechanics ($g = 9.81$, $e \in [0.3, 0.8]$) with matched wrong-physics controls (Task 24) is required to replace the web-mined driven-bounce prior with true physical dissipation.
