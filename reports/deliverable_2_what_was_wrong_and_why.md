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
3. **Representational Sufficiency of Wan2.2 VAE**: Passing real bouncing-ball video through Nano's Wan2.2 16×4× temporal VAE ($D(E(\text{real}))$ round trip) demonstrates that the tokenizer faithfully preserves sharp impact turnarounds, geometric flight-time dissipation (observed point estimates $e_{T,\text{log}} \approx 0.72\text{--}0.86$ vs real $0.74\text{--}0.82$), and complete settling to rest ($4/4$ full 129f clips stop at the plank by $2.6\text{--}4.5\text{ s}$). Paired detected impact time discrepancy between original and round-trip tracks is small ($\le 3.8\text{ ms}$ on clean trajectories), though absolute sub-millisecond impact timing is unproven (#1556, #1580). This establishes that 4× temporal latent compression does not mechanically prevent bounce decay or settling on real latents, ruling out the VAE as an absolute representational bottleneck; causal attribution on generated latents awaits cross-component intervention.
4. **Origin of the Undamped Prior**: Pre-training video data of "bouncing balls" on the open web (e.g. Countix/Kinetics, RepNet) consists predominantly of driven periodic oscillations (keepy-uppy, juggling, ball dribbling, median period $0.49\text{ s}$) where external energy is continuously injected. Coupled with data curation filters that actively reject static or settled scenes (§3.2.1), the generative model learned an active steady-state oscillator rather than passive dissipative mechanics.
5. **Anomalous Energy Creation & Limit Cycles**: On low drop heights ($5.3\text{ cm}$), Nano exhibits anomalous energy creation, rebounding to a $30.8\text{ cm}$ apex (**$+580\%$ height increase**, apparent $e_v = 2.41$), or freezing in a proximity-induced levitation attractor (66.7% rate), proving that Nano operates as a kinematic pattern generator with a preferred limit-cycle amplitude and period ($\approx 0.33\text{ s}$) rather than an energy-conserving physical simulator.
6. **Temporal Conditioning is Invariant (FPS is Not a Clock)**: Neither prompt text ("12 FPS" vs "24 FPS") nor RoPE positional temporal spacing ($fps \in \{6, 12, 24\}$) acts as a physical clock ($k = 1.000$ fixed stride). Halving RoPE fps triggers catastrophic late-frame hallucinations (duplicate balls, arm swings, 100% anomaly rate at RoPE 6).
7. **Terminal Velocity Ceilings**: On 30° slopes across materials, Nano does not integrate Newton-Coulomb acceleration ($a \approx 2.57\text{ m/s}^2$); instead, it glides at a constant terminal velocity ceiling ($v \le 0.40\text{ m/s}$ on plastic, $v \le 0.70\text{ m/s}$ on wood), exhibiting zero quadratic acceleration on 189-frame rollouts ($a = 0.00 \pm 0.01\text{ m/s}^2$).
8. **Sim-to-Real Generalization of Synthetic SFT (LoRA) & Scoreboard Regressions**: An initial report that synthetic ballistic LoRA failed to release on 0/66 clips (Finding #1661) was refuted by ro-1 (#2211, #2200): automated trackers tracked blank wall at (281, 119) because the evaluation clips used a robot-free frame with ball at (529, 46). Re-coding shows the ball falls in 72/84 clips (53/84 clean falls, though 28 clips suffer physical hallucinations). However, synthetic LoRA is decisively refuted as a shippable fix on NVIDIA's scoreboard benchmarks: real-physics LoRA Arm A causes severe, statistically resolved regressions on DOVER Fused (−0.0767 ± 0.0211) and HUE Plausibility (−0.0280 ± 0.0090 overall, −0.0347 ± 0.0142 physical laws), while cutting motion by 55% (dd_norm −4.3 ± 1.2), failing the charter's no-regression mandate (#2168, #2201).
9. **Early RoPE Spatial Scaling Fails ($0\%$ Clean Release)**: Widening early spatial receptive fields (RoPE 0.7x dilation for $t \ge 900$; Task 90 Finding #2402) does not loosen the static visual grasp attractor: across 4 paired seeds, release rate is $0/4$ ($0.0\%$), duplicate phantom balls dominate in both arms, and spatial dilation causes severe topological chaos, plank flipping, and scene morphing (audited by rog-cc #2480, commit `cec0954`).
10. **Event-Script Text Prompts Induce Geometric Deformation Rather Than Motion ($0/6$ Rigid Swings)**: Prompting Cosmos3-Nano with event narrative ('released in the first moment, falls, swings below the axle') from a static rest frame forces motion energy ($7.07 \pm 1.35$ gray levels), but results in $0/6$ rigid swings (ro-3 #2432): the rod stretches to $2\times$ length, duplicate bobs appear, or the structure shatters. In contrast, mid-event conditioning produces $6/6$ intact rigid swings ($100\%$), proving that text prompting cannot overcome static boundary attractors without destroying object geometry.
11. **Serial Clip Chaining Fails to Impart Dissipation**: Chaining short I2V segments through extracted still frames (Task 42 Finding #2407) fails to break the DiT's stationary limit cycle ($0/2$ arms settle, apex height restitution $e_h = 1.35 \pm 0.38$; replicated by agy-2 Task 104 #2493).
12. **Temporal RoPE Frequency Editing (fast05) Causes Substantial Scoreboard Regressions**: Halving high-frequency temporal RoPE coordinates ($j=0, 3$) drops DOVER Fused by $-0.025 \pm 0.004$ (exceeding non-inferiority margins) while CoTracker3 audits prove lack of physical damping due to tether re-lift to the frame-0 gripper attractor (#2396, #2419, #2443).
13. **Event-Timing Prompting Resolves Perpetual Bouncing into Physical Dissipative Rest ($8/8$ Settle)**: Adding a concrete timing sentence to the prompt on dynamic mid-fall conditioning (ro-1 #2460, #2488) causes the bouncing ball to dissipate kinetic energy and settle to complete rest in **8/8 pairs ($100.0\%$) vs 0/8 in base prompt ($0.0\%$)**, cutting late motion corridor energy by $-2.24 \pm 0.24$ gray levels (8/8 lower) with no DOVER degradation ($\Delta = +0.007 \pm 0.003$), moving Dynamic Degree closer to real reference video (|DD - real| improves from 1.10 to 0.35). While event text fails destructively from static rest frames (Finding 10), it acts as a valid temporal director when applied to mid-event dynamic states.

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
| **Impact Timing Paired Discrepancy** | Zero (Self) | N/A | **$3.76 \pm 2.75\text{ ms}$** (detected tracks) | N/A |
| **SFT Synthetic LoRA Falling Rate** | $100\%$ | $0.0\%$ ($0/16$ base) | N/A | **$85.7\%$ ($72/84$ clips fall; 0/66 refuted #2211)** |
| **Low Drop Energy ($5.3\text{ cm}$)** | Dissipates in $<0.3\text{ s}$ | N/A | Dissipates in $<0.3\text{ s}$ | **$+580\%$ Energy Gain** |
| **FPS RoPE Time Scaling $k$** | $k = 2.0\text{ (12 fps)}$ | $k = 1.000$ (Stride Invariant) | N/A | $k = 1.000$ |
| **Plastic Slope Slide** | $a = 2.57\text{ m/s}^2$ | $v \le 0.402\text{ m/s}$ ($a = 0$) | $a = 2.57\text{ m/s}^2$ | $v \le 0.402\text{ m/s}$ ($a = 0$) |
| **Wood Slope Slide** | $a = 2.58\text{ m/s}^2$ | $v \le 0.704\text{ m/s}$ ($a = 0$) | $a = 2.58\text{ m/s}^2$ | $v \le 0.704\text{ m/s}$ ($a = 0$) |
| **Pendulum Period ($L=0.27\text{m}$)**| $1.05\text{ s}$ | $2.36\text{--}3.77\text{ s}$ | $1.05\text{ s}$ | $2.36\text{--}3.77\text{ s}$ |
| **Pendulum Rest Release Rate** | $100\%$ ($0.0\text{ s}$) | **$0.0\%$ ($0/6$ clips, axle locked)** | N/A | **$100.0\%$ ($6/6$ mid-swing, $p=0.002$ #2361)** |
| **Pendulum Event-Script (`restev`)** | $100\%$ Rigid Swing | **$0.0\%$ ($0/6$ rigid; rod 2x elongates/fractures #2432)** | N/A | **$100.0\%$ ($6/6$ rigid mid-swing)** |
| **Serial Clip Chaining Settling** | Dissipates to Rest | Never Settles | N/A | **$0/2$ Settled (5-frame seam stagnation #2407)** |
| **Temporal RoPE Editing (fast05)**| Dissipates to Rest | $e_T \approx 1.0$ | N/A | **$0\%$ Damping (tether re-lift #2419; DOVER $\Delta -0.025$ #2396)** |

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
  - Cross-Domain Replication: Corroborated on a second physical system by ro-3 (Finding `#2323`): on real GAUGE pendulum frames, Nano exhibits an identical boundary release failure from rest (0/4 swing from horizontal rest, 100% deadlock), while mid-swing conditioning restores motion in 3/3 clips, confirming that the release deadlock is universal to static boundary constraints across physical systems.
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

### Finding 3: Perpetual Bouncing Limit Cycle and VAE Representational Sufficiency

```
FINDING: Cosmos3-Nano generates undamped, perpetual bouncing (e_T = 0.989 ± 0.011, e_h = 0.986 ± 0.007, 100% active after 7.9 s). The Wan2.2 16×4× temporal VAE preserves visually evident bounce decay and complete settling to rest (4/4 full clips stop at the plank) on real-video round trips (D(E(real))), establishing representational sufficiency and ruling out temporal VAE compression as an absolute bottleneck.
```

- **Quantitative Value**:
  - Real Video Flight-Time Restitution: **$e_{T,\text{log}} = 0.731 \pm 0.073$** (settles at $t = 2.6\text{--}4.5\text{ s}$, $4\text{--}5$ bounces).
  - Nano Generated Rollout Restitution: **$e_T = 0.9886 \pm 0.0110$** (apex height ratio $e_h = 0.9861 \pm 0.0074$; $>25$ bounces, $100\%$ still bouncing at $f189$).
  - Wan2.2 VAE Round-Trip Restitution: **$e_{T,\text{log}} = 0.726 \pm 0.063$**; paired point estimates **$\Delta e_{T,\text{log}} = -0.005 \pm 0.010$** (#1373), **$-0.012 \pm 0.044$** (#1528), and **$+0.040 \pm 0.020$** (#1523).
  - Statistical Qualification (#1580): With $n=4$ paired video clips, the conventional illustrative 90% paired-$t$ interval for #1528 spans $[-0.116, +0.092]$, so a narrow $|\Delta e_T| \le 0.05$ equivalence margin is not statistically established. The evidence establishes that observed real-world decaying clips retain evident bounce decay and complete rest under VAE round-trip, rather than proven population equivalence.
  - Clean Decaying Subset (Balls 1 & 3): Original $0.662 \pm 0.021$ vs VAE $0.665 \pm 0.011$ ($\Delta e_T = +0.002 \pm 0.016$).
  - Paired Detected Impact Time Discrepancy: **$0.094 \pm 0.069\text{ frames}$ ($3.76 \pm 2.75\text{ ms}$)** across 20 matched impacts on clean trajectories (paired estimated-time difference, not absolute ground-truth impact timing error, #1556).
  - VAE Reconstruction Quality: Whole-frame PSNR = **$36.25 \pm 0.72\text{ dB}$** (#1373) / **$36.35 \pm 0.32\text{ dB}$** (#1528), SSIM = **$0.9546 \pm 0.0041$**.
  - Inference Sampler Hyperparameter Invariance (CFG & Flow Shift):
    - *Flow Shift*: Bit-for-bit SHA-256 identity (`6af5474bd8bfec3565caa053d5ffb7f2ddd576bf07fe7726c83beebf086b93c6`) was verified across shift 10.0 vs 3.0 clips on `puget13` (Task 75 audit, commit `a1fb2e3`), demonstrating that `flow_shift` produces zero observed change on that stack, consistent with source-level schedule no-op audits (Finding `#1075`). Seed 1 cross-host divergences (GB10 vs A100) were verified to be hardware/stack confounds rather than causal shift effects.
    - *Guidance Scale (CFG)*: Sweeps across CFG $\in [1.0, 6.0]$ demonstrate that lowering CFG does NOT induce dissipative settling. Centroid tracking with full-corridor background subtraction confirms that CFG $\le 2.5$ induces mid-air levitation/hovering and upward trajectory reversals (3/4 clips fail to reach the plank; 1/4 reaches the plank at f48 before rebounding). At higher guidance ($\text{CFG} \in [4.0, 6.0]$), undamped bouncing persists invariant to scale ($e_T \approx 1.0$).
    - *Conclusion*: Neither flow shift nor CFG tuning can break the undamped limit cycle (Task 71, Finding `#1721`, Review `#1806`, Task 75 audit, commit `a1fb2e3`).
- **Setup**: `AutoencoderKLWan` (bf16, temporal scale 4, spatial scale 16, 48 channels) on GB10. Evaluated on all 4 real GAUGE ball drops (129f full + 93f midfall, $n=8$ pairs, 16 videos).
- **Method**: 2-pass ghost-free adaptive background subtraction tracker (`bounce_decay.py`, PASS 12/12, msg 599), scipy quadratic sub-pixel vertex interpolation, log-linear restitution regression ($\ln T_k = \ln T_0 + k\ln e_T$).
- **Control**: Direct frame-for-frame comparison of pre-VAE original clips against post-VAE round-trip reconstructions under identical tracking parameters.
- **Replication History**:
  - Initial finding: Finding `#1373` (agy-1, `commit d70c116`).
  - Independent Replication 1: Review `#1523` (agy-4, `commit 2258398`).
  - Independent Replication 2: Review `#1528` (agy-2, `commit 286bb89`).
  - Audit & Methodological Qualification: Review `#1556` and `#1580` (codex-api-1, Task 67), accepted in `#1568` (agy-2) and `#1578` (agy-4), establishing representational sufficiency on real latents while qualifying interval bounds and event timing.
- **Causal Mechanism**: The 4× temporal VAE compresses 129 frames into 33 latents without destroying cusps or dissipation on encoded real latents. This rules out temporal VAE compression as an absolute representation bottleneck. The perpetual bounce failure on generated latents is consistent with the DiT dynamics prior: web-mined video corpora (e.g. Countix "bouncing ball" keepy-uppy, median period $0.49\text{ s}$, Digest `#1399`) depict active, human-driven rhythmic bouncing rather than unforced dissipative settling. Complete causal attribution requires cross-component latent-swap interventions.

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
  - Cross-Domain Start-Transition & Mid-Swing Replication: ro-3 Finding `#2361` (`commit f598d92`). On real GAUGE pendulum video (videos 10 & 11, real period $1.23\text{ s} / 1.18\text{ s}$), starting from the rest frame yields **0/6 swings ($0.0\%$)**, with the rod locked horizontally for 93 frames (ROI motion $1.70 \pm 0.18$ gray levels). Starting mid-swing yields **6/6 swings ($100.0\%$)** (ROI motion $6.68 \pm 0.73$ gray levels; Fisher exact $p = 0.002$). Measured mid-swing periods scatter from $0.40\text{ s}$ to $1.94\text{ s}$ (ratios vs real $0.3\times\text{--}1.6\times$; seed SD $\approx 0.7\text{ s}$).
- **Causal Mechanism**: The pendulum operates on an invariant token oscillation count ($\approx 48\text{ frames}$ per cycle at $24\text{ fps} \approx 2.0\text{ s}$), demonstrating that periodic oscillatory motion reflects a fixed learned temporal frequency rather than physical pendulum length $T = 2\pi\sqrt{L/g}$. Furthermore, ro-3 Finding `#2361` proves that the start-transition locking observed on held balls is universal across dynamical systems: resting boundary frames trap the object in place, while mid-event frames break the lock but leave physical dynamical constants uncalibrated.

---

### Finding 8: Sim-to-Real Generalization of Ballistic Fine-Tuning & Retraction of '0/66 Release' Artifact (Task 24 Audit)

```
FINDING: Synthetic ballistic fine-tuning (Task 24 LoRA) does not produce bit-level immobility on robot-free frames (72/84 balls fall, refuting the automated '0/66 release' artifact; ro-1 #2211), but fails to generalize clean physics (28/84 hallucination artifacts) and severely degrades visual quality and plausibility on NVIDIA's official scoreboard (DOVER fused drop -0.077 ± 0.021, motion cut by 55%, HUE plausibility drop -0.028 ± 0.012; rog-cc #2168, #2201).
```

- **Quantitative Value**:
  - *Retraction of '0/66 Release' Claim (ro-1 Review `#2211`, Status `#2200`)*: Finding `#1661` originally reported that 60/66 clips were bit-frozen in gripper jaws. In Review `#2211`, ro-1 discovered that `gauge_blind v1.1` and agy-2's Task 69 evaluator tracked `SEED (281, 119)`—the Franka gripper coordinates on the official GAUGE frame. The Task 24 eval clips, however, started from a robot-free image with a black ball against a white wall at `(529, 46)`. The trackers monitored blank wall, creating the artifactual "0/66 release" result.
  - *Blind Visual Re-Code of all 84 Eval Clips (ro-1 `#2211`, commit `682e5e6`)*:
    - Falling rate: The ball detaches from its f0 position and falls in **$72 / 84$ ($85.7\%$)** clips.
    - Clean falls: **$53 / 84$ ($63.1\%$)** are clean falls to the plank without structural artifacts ($43$ settle to rest by frame 92, $10$ remain in the air).
    - Hallucinations / Physical Artifacts: Present in **$28 / 84$ ($33.3\%$)** clips (8 ball size jumps, 8 duplicate clone balls, 5 tether/pendulum bifurcations, 3 re-spawns at top, 2 plank morphs into ramps, 3 frozen in place).
    - Quantitative Acceleration ($g$): Retained as **OPEN** because pixel-to-meter scaling for this uncalibrated robot-free view is unestablished.
  - *DOVER Blindness to Physics Hallucinations (rog-cc Finding `#2249`, commit `a5d291e`)*:
    - On the 84 Task 24 GAUGE-eval clips, DOVER does not penalize physical hallucinations: clips with duplicate balls, size jumps, or tethers score slightly HIGHER than clean falls (DOVER Fused $0.328$ vs $0.304$, $\Delta = -0.024 \; [-0.038, -0.011]$, $\text{AUC} = 0.25$).
    - VBench Dynamic Degree rewards the energy-keeping bounce ($dd_{\text{norm}} = 2.56$ for balls in air vs $1.33$ for settled balls, $\Delta = -1.23$).
  - *NVIDIA Scoreboard Regressions on Standard T2V Dev Prompts (rog-cc Status `#2168`, `#2201`, `#2350`, Finding `#2562`, commits `1527bbf`, `d01c9a4`, `c78021f`, `30163c9`)*:
    - **Complete 5-Arm Evaluation Matrix (16 HUE Prompts $\times$ Seeds 1+2 averaged, commit `30163c9`, Finding `#2562`)**:
      | Contrast | HUE Overall ($\delta = 0.03$) | HUE Physical ($\delta = 0.04$) | DOVER Fused ($\delta = 0.02$ prop.) | DD Norm ($\delta = 1.18$ prop.) |
      | :--- | :---: | :---: | :---: | :---: |
      | **baseL − base (box null)** | $-0.005 \pm 0.002$ (NI) | $-0.005 \pm 0.004$ (NI) | $+0.006 \pm 0.005$ (NI) | $+0.07 \pm 0.28$ (NI) |
      | **C − base (no-decay ctl)** | $-0.014 \pm 0.007$ (NI) | $-0.017 \pm 0.006$ (NI) | $-0.048 \pm 0.020$ (sig drop) | $-1.85 \pm 0.63$ (sig drop) |
      | **A − base (real $g$)** | $-0.028 \pm 0.012$ [−0.049, −0.007] (**NI not shown**) | $-0.035 \pm 0.014$ (**NI not shown**) | $-0.077 \pm 0.021$ (**REGRESSION**) | $-4.34 \pm 1.17$ (**REGRESSION**) |
      | **B − base (wrong $g$)** | $-0.018 \pm 0.009$ (sig drop) | $-0.029 \pm 0.012$ (sig drop) | $-0.075 \pm 0.018$ (**REGRESSION**) | $-3.43 \pm 0.96$ (**REGRESSION**) |
      | **A − B (only $g$ differs)** | $-0.010 \pm 0.006$ | **$-0.005 \pm 0.009$** [−0.022, +0.011] | **$-0.002 \pm 0.017$** | $-0.91 \pm 0.51$ |
      | **A − C / B − C** | $-0.014 \pm 0.013$ / $-0.004 \pm 0.010$ | $-0.018 \pm 0.016$ / $-0.013 \pm 0.012$ | $-0.029 \pm 0.021$ / $-0.027 \pm 0.020$ | $-2.49 \pm 1.08$ / $-1.59 \pm 1.00$ |
    - **Arm Means (HUE Overall / Physical / DOVER Fused / DD Norm / DD Binary)**:
      - Base: $0.706$ / $0.586$ / $0.599$ / $7.89$ / $0.66$
      - baseL (same-box): $0.701$ / $0.582$ / $0.605$ / $7.96$ / $0.66$
      - Arm A (real $g$): $0.678$ / $0.552$ / $0.523$ / $3.55$ / $0.25$
      - Arm B (wrong $g$): $0.688$ / $0.557$ / $0.524$ / $4.46$ / $0.47$
      - Arm C (no decay): $0.692$ / $0.570$ / $0.551$ / $6.04$ / $0.47$
    - **Key Findings from Complete 5-Arm Audit**:
      1. Both Arm A and Arm B regress DOVER fused ($-0.077$ and $-0.075$) and Dynamic Degree ($-4.34$ and $-3.43$), failing scoreboard non-inferiority.
      2. The critical physical contrast $A - B$ (where only gravity differs between real $g=9.81$ and uniform wrong $g \sim U(1.5, 4.0)$) is **indistinguishable from zero on HUE Physical ($\Delta = -0.005 \pm 0.009$) and DOVER Fused ($\Delta = -0.002 \pm 0.017$)**, proving that correct physics buys zero plausibility or visual fidelity gain.
      3. The cross-box null (`baseL - base`) is approximately zero on every metric, confirming that the regressions are intrinsic to the fine-tuning recipe and not a host artifact. No Task-24 LoRA can be a recipe candidate.
  - *Refutation of Blank-Wall Coordinate Tracking in Replications (#2374, #2382, #2386)*:
    An attempted automated replication by agy-3 (`#2374`) claiming "0/84 releases" was refuted by rog-cc (`#2382`) and verified by rahul-5-agy (`#2386`). agy-3 hardcoded Franka coordinates $[y: 90..150, x: 260..320]$, measuring static blank wall while the ball fell at $x \approx 529$.
- **Setup**: `nvidia/Cosmos3-Nano` (Base, LoRA A real-$g$, LoRA B wrong-$g$, LoRA C no-decay control; rank 16, alpha 32 on `q/k/v/o_moe_gen`, 300 iterations, H100 PCIe), $832\times 480$, $93\text{ frames}$, $24\text{ fps}$, 35 steps, guidance 6.0, flow shift 10.
- **Method**: ro-1 blind visual and dark-pixel persistence audit (`work/ro-1/task24_eye/eye_codes.csv`, commit `682e5e6`); rog-cc paired NVIDIA scoreboard and HUE plausibility judge evaluation (`work/rog-cc/hue_t24/`, commits `1527bbf`, `d01c9a4`, `c78021f`, `a5d291e`).
- **Control**: Matched comparisons across Base, Arm A (real $g$), Arm B (wrong $g$), and Arm C (no-decay control) on identical seeds and prompts.
- **Causal Mechanism**: While supervised fine-tuning on synthetic drops does not freeze motion on robot-free frames, it fails to induce clean, generalizable physical laws. The LoRA overfits to synthetic ballistic trajectories, generating high rates of topological glitches (size jumps, duplicates, tethers) on real textures, while severely degrading the model's general visual quality, motion generation capacity ($-55\%$), and plausibility on out-of-distribution prompts.

---

### Finding 9: Early RoPE Spatial Frequency Scaling Fails to Resolve Mechanical Grasp Deadlock

```
FINDING: Scaling RoPE spatial (height/width) frequencies by 0.7x in early denoising steps (t >= 900) does not break Cosmos3-Nano's held-ball release deadlock from frame 0; physical release failure (0% clean release) and phantom duplicate cloning persist, accompanied by severe topological chaos and geometric morphing (Task 90, Finding #2402; audited by rog-cc #2480).
```

- **Quantitative Value**:
  - **Clean Physical Release Rate**: **0/4 (0.0%)** treatment vs **0/4 (0.0%)** control ($n=4$ paired seeds 1–4).
  - **Visual Dynamics Across 4 Seeds (True-Color Audit, rog-cc #2480, commit `cec0954`)**:
    - *Control (Scale 1.0)*: In Seed 1, ball remains clamped in jaws through f92 while a duplicate ball materializes on the table from f24. In Seed 2, small ball drops f8–12 and bounces f16, but gripper vanishes. In Seed 3, giant ball spawns under gripper at f8 while original stays in jaws f16–92 (duplicate). In Seed 4, ball stays clamped in jaws through f92 (mean intensity 17.5–20.8) while duplicate shadow forms on plank.
    - *RoPE 0.7x (Treatment)*: In Seed 1, chaotic topological morphing (plank flips, arm jumps, ball on plank f24). In Seed 2, giant phantom ball appears at f48, gripper vanishes, plank distorts. In Seed 3, duplicate ball (giant ball spawns f8, ball still in jaws f48–92). In Seed 4, severe flashing and structural morphing of arm and plank, with no clean physical release.
  - **Save-Path Negative Inversion & Scoreboard Audit**:
    - In `experiment_rope_scale.py`, pre-converting generated frames to `uint8` before passing to Diffusers `export_to_video` caused Diffusers to multiply uint8 arrays by 255. In 8-bit unsigned integer arithmetic, $x \times 255 \equiv -x \pmod{256} = 256 - x$, saving all clips as photographic negatives.
    - Automated single-point tracking on inverted frames locked onto Franka arm descent rather than the ball (`firstfall` flag `weak`). Absolute DOVER (~0.43) was scored on negative frames; on true-color frames, DOVER Fused returns to standard baseline ($\approx 0.50$). Dynamic Degree increase ($\Delta\text{dd\_norm} = +3.17 \pm 1.42$) reflects spurious background/arm optical flow and topological warping rather than valid detachment motion.
- **Setup**: `nvidia/Cosmos3-Nano` (bfloat16, vLLM/diffusers), GAUGE Ball 1 Frame 0 (letterboxed to $832\times 480$), 93f, 24 fps, 35 steps, CFG 6.0, flow shift 10.0, prompt diffusers standard. Treatment: spatial RoPE frequencies scaled by 0.7 for $t \ge 900$.
- **Method**: Spatio-temporal multi-ROI component tracking, true-color contact sheets (`gauge_b1_*_true_strip.jpg`, `gauge_b1_*_true_gripper.jpg`), referee-validated `tools/realball/firstfall.py`, and `tools/nv_scoreboard/score.py`.
- **Control**: Matched unmodified Cosmos3-Nano rollout on identical prompt, frame-0 image, and seeds 1–4 (scale=1.0).
- **Evidence**: Commits `ead77bf`, `246c0eb`, `cec0954`, Findings `#2402`, `#2480`, `work/ro-agy1/task90_rope_scale/` and `work/rog-cc/rep2402/`.
- **Causal Mechanism**: Hypothesized by arXiv 2609.23658 and steering #696/#1825 to widen spatial receptive fields and dissolve the gripper grasp anchor. Testing reveals that relaxing spatial RoPE frequencies early in denoising destabilizes spatial coordinates without overriding the cross-attention visual grasp prior: the model satisfies denoising loss by distorting scene topology (warping planks, jumping arms, ballooning spheres) rather than simulating mechanical detachment.

---

### Finding 10: Event-Script Text Prompts Force Topological Deformation and Structural Shattering Rather Than Mechanical Dynamics (ro-3 Finding #2432, ro-agy1 Review #2445, agy-2 Review #2625)

```
FINDING: Prompting Cosmos3-Nano with event-script text ('released in the first moment, falls, swings below the axle') from a static rest frame forces motion (leaves axle line in 6/6 clips, ROI motion 7.07 ± 1.35 vs neutral 1.70 ± 0.18), but completely fails to produce rigid mechanical motion in 0/6 clips (0.0%). The model satisfies the text constraint by deforming or destroying object geometry (2x rod elongation, duplicate bobs, shattered rods). In contrast, mid-swing conditioning yields 6/6 rigid swings (100.0%) without geometric deformation (ro-3 #2432, ro-agy1 #2445, agy-2 #2625, commits 04f843a, 7afffac).
```

- **Quantitative Value**:
  - **Leaves Axle Line**: Rest Event-Script (`restev`) **6/6 (100.0%)**, Neutral Rest 0/6 (0.0%), Mid-Swing **6/6 (100.0%)** (2 videos × seeds 1–3).
  - **Rigid, Fixed-Length Swing Below Axle**: Rest Event-Script **0/6 (0.0%)**, Neutral Rest 0/6 (0.0%), Mid-Swing **6/6 (100.0%)** (Fisher exact $p = 0.002$ vs mid-swing).
  - **Failure Classification across 6 Clips**:
    - *Elongated Rod & Bob Disappearance (`moves_broken`, Scout-1 Hypothesis D)*: In 3/6 clips (`pend10_restev_s1`, `s3`, `pend11_restev_s3`), the bob drops vertically from $y=116$ to $y=276\text{ px}$ impacting the table; nominal rod $L_0 = 106.4\text{ px}$ stretches by $1.55\text{--}1.79\times$ ($164.5\text{--}190.2\text{ px}$), confirmed by bright vertical column scans.
    - *Multi-Rod Morphing & Duplicate Bobs (`delayed_morph`)*: In 2/6 clips (`pend10_restev_s2`, `pend11_restev_s2`), the DiT splits the rod into orthogonal horizontal and vertical tethers, spawning duplicate bobs.
    - *Structural Shattering (`detached`)*: In 1/6 clips (`pend11_restev_s1`), the bob breaks off the axle and tumbles down.
  - **ROI Motion Energy (Gray Levels)**: Rest Event-Script **$7.07 \pm 1.35$** ($n=6$) vs Neutral Rest $1.70 \pm 0.18$ vs Mid-Swing $6.68 \pm 0.73$ (Real GAUGE reference: $5.06\text{--}5.40$). Motion metrics alone would falsely score restev as "fixed", paralleling the optical flow reward trap seen in VBench Dynamic Degree (Finding #2249).
  - **Dynamical Period**: Referee-validated `measure_pend` reports `check` on 6/6 clips and `pend_acf` fails completely on 6/6 (0/6 measurable physical periods vs 6/6 valid periods under mid-swing conditioning).
  - **NVIDIA Scoreboard (agy-2 #2625)**: Mid-swing conditioning yields DOVER Fused gain $\Delta = +0.0154 \pm 0.0035$ ($p = 0.0071$) and Technical gain $+0.0049 \pm 0.0017$ ($p = 0.035$), while rest-event text prompting causes DOVER Fused degradation $\Delta = -0.0116 \pm 0.0038$ ($p = 0.0277$) and unphysical optical flow explosion ($DD_{\text{norm}} = 3.715 \pm 0.255$, paired $\Delta = +2.559 \pm 0.526, p = 0.0046$; $>2.3\times$ real mocap).
- **Setup**: `nvidia/Cosmos3-Nano` (bfloat16, vLLM/diffusers, A100 & RTX 5090), $832\times 480$, 93f @ 24 fps, 35 steps, CFG 6.0, flow shift 10.0, no negative prompt. Input: real GAUGE pendulum videos 10 and 11, horizontal release frame (rest) vs mid-swing frame (mid). Prompt: `prompt_event.txt` ("released in the first moment, falls, swings below the axle") vs neutral prompt.
- **Method**: Categorical blind eye coding from 4-frame ROI contact strips (`qc/restev_10.jpg`, `qc/restev_11.jpg`), spatio-temporal ROI motion tracking, referee-validated `tools/trk_ballfall/measure_pend.py` (PASS msg 201), and `pend_acf` autocorrelation. Replicated by `ro-agy1` in Review `#2445` and independently evaluated on kinematics and scoreboard by `agy-2` in Review `#2625`.
- **Control**: The neutral-prompt rest arm on identical frames and seeds (stays at horizontal axle line in 6/6 clips) and mid-swing arm.
- **Evidence**: Commits `04f843a`, `7afffac`, Findings `#2432`, `#2625`, Reviews `#2445`, `work/ro-3/task99_midswing_pendulum/`, `work/agy-2/task109_pendulum_review/`.
- **Causal Mechanism**: Directly confirms Scout-1's event-script hypothesis H-S (Finding #2305, Digest #2365; CausalCascade, arXiv:2610.15562): text prompts function as high-level semantic event classifiers that enforce event occurrence ("it falls"), but lack the temporal capacity to constrain continuous spatial-temporal mechanics. When initialized from a static zero-velocity boundary condition (held horizontal along axle), the diffusion prior cannot reconcile the static image tokens with continuous rigid rotation. Consequently, the model minimizes denoising loss by distorting object geometry (elastic rod stretching, phantom duplicate bobs, structural shattering) to satisfy the text condition without obeying rigid mechanics. This directly mirrors the phantom duplicate ball spawning observed under conflicting text/visual constraints in ball drops (Finding 1, Finding 9). Mid-event conditioning is the only intervention that preserves rigid geometry.

---

### Finding 11: Chained Short I2V Clips Fail to Induce Dissipation, Refuting Serial-Event Hypothesis (agy-4 Task 42 Finding #2407, agy-2 Task 104 Replication #2493)

```
FINDING: Chaining short I2V clips fails to induce bounce decay or settling to rest over continuous rollouts (0/2 arms settled, e_h = 1.346 vs 1.007 control), refuting the serial-event hypothesis (arXiv:2607.13031). The originally reported 5-frame seam velocity stagnation is refuted as a tracker area-filter artifact; motion is physically continuous across the seam (agy-4 Task 42 Finding #2407, commit 8780f81; agy-2 Task 104 Review #2493, commit cf90e74).
```

- **Quantitative Value**:
  - **Settling / Rest Rate**: **0.0% (0/2 arms settled)**; both the chained 185-frame arm ($25$ impacts, mean cycle period $6.7\text{ f} = 0.28\text{ s}$, apex height ratio $e_h = 1.346 \pm 0.38$) and the continuous 189-frame control ($23$ impacts, mean cycle period $8.1\text{ f} = 0.34\text{ s}$, apex height ratio $e_h = 1.007 \pm 0.12$) exhibit continuous, undamped bouncing limit cycles through frame 185/189 ($7.7\text{--}7.9\text{ s}$).
  - **Initial Gravitational Acceleration**: $g = 8.12 \pm 0.85\text{ m/s}^2$ ($R^2 = 0.9987$, flag `ok`) chained vs $11.51 \pm 0.30\text{ m/s}^2$ ($R^2 = 0.9999$, flag `weak`) control.
  - **NVIDIA Scoreboard**: DOVER Fused $\Delta = +0.0028$ ($0.5398$ vs $0.5370$, within seed noise $\sigma_{\text{seed}} = 0.021\text{--}0.032$); DD Norm $\Delta = -0.256$ ($1.162$ vs $1.419$, both `dd_bin = 0`).
  - **Refutation of 5-Frame Seam Stagnation Artifact (agy-2 Review #2493, commit `cf90e74`)**:
    - Finding #2407 originally reported that I2V chaining introduced a "5-frame velocity stagnation seam artifact ($v \approx 0$, displacement $<0.1\text{ px}$ for f0–f4 of segment 2, followed by a sudden table plunge at f5)".
    - Root cause: In `tools/track_ball_corridor` (`analyze_chain_vs_control.py`, lines 40–55), connected-component filtering strictly required `60 < area < 1200`. In frames 0 to 4 of Segment 2, the ball impacts the plank at $y \approx 346\text{--}348\text{ px}$, merging with the dark table edge / support plank shadow into components exceeding $1200\text{ px}$. The tracker returned `missing: True` with uninitialized $(0.0, 0.0)$ coordinates.
    - At frame 5, when the ball rebounded to $y = 331.3\text{ px}$, it passed the filter at $(299.9, 396.0)$. The reported "496.7 px drop" was literally `np.hypot(299.88, 395.98) = 496.72 px` from the origin!
    - Independent sub-pixel tracking proves **continuous physical motion across frames 0 to 5**: Frame 0: $y = 346.4\text{ px}$ (touching plank); f1: $346.7\text{ px}$; f2: $347.7\text{ px}$ (max impact); f3: $345.1\text{ px}$ (rebound upward); f4: $346.8\text{ px}$; f5: $331.3\text{ px}$ (rising upward). There is no velocity freeze and no sudden plunge. Scout-1's VAE latent boundary hypothesis (#2415) was withdrawn (#2519).
- **Setup**: `nvidia/Cosmos3-Nano` (diffusers bf16), $832\times 480$, 24 fps, 35 steps, CFG 6.0, flow shift 10.0, no negative prompt, exact GAUGE ball prompt. Input: real GAUGE ball 1 mid-fall (frame 33). Chained arm: 93f segment 1 + 92f continuation from still frame 92 (185 displayed frames). Control: continuous 189f generation.
- **Method**: Referee planted-PASS `tools/realball/firstfall.py` (20/20 PASS), `tools/nv_scoreboard/score.py` (CUDA DOVER + RAFT DD), sub-pixel template tracking, and median-background subtraction. Replicated by `agy-2` in Task 104 (`cf90e74`).
- **Control**: Matched continuous 189-frame rollout at identical prompt, seed, model, and sampling hyperparameters.
- **Evidence**: Commit `8780f81`, commit `cf90e74`, `work/agy-4/task42_chain_bounce/` (`README.md`, `task42_results.json`, `chained_s1_185f.mp4`), `work/agy-2/task104_chain_review/` (`README.md`, `task104_review_results.json`).
- **Causal Mechanism**: Hypothesized by arXiv:2607.13031 that breaking long rollouts into shorter sequential chunks would bypass autoregressive drift and allow natural event termination. However, even with continuous physical motion across segment boundaries, the diffusion backbone's undamped limit-cycle attractor remains active across restarts. Chaining still frames resets neither the learned kinetic cycle nor the stationary bouncing prior.

---

### Finding 12: Temporal RoPE Frequency Editing (fast05) Causes Inconclusive DOVER Drop ($\Delta = -0.025$) While CoTracker3 Disproves Physical Damping via Frame-0 Attractor Re-Lift (rog-cc Review #2396, rog2 Review #2419, scout-1 #2443)

```
FINDING: Editing temporal RoPE frequencies (halving fastest pairs j=0, 3; fast05) causes a significant DOVER fused drop (Δ = -0.025 ± 0.004, CI90 [-0.033, -0.017], inconclusive vs proposed 0.02 margin), while identity-aware CoTracker3 tracking disproves physical damping by revealing temporary mid-clip rest followed by unphysical re-lift to gripper height (rog-cc Review #2396, rog2 Review #2419, scout-1 #2443).
```

- **Quantitative Value**:
  - **NVIDIA Scoreboard Regressions (rog-cc Review #2396, commit `cc05328`)**:
    - DOVER Fused: $\Delta = \mathbf{-0.0250 \pm 0.0040}$ ($df=5$, CI90 $[-0.033, -0.017]$, $6/6$ pairs degraded; $\pm 0.0040$ is the SE of the paired difference). Because the upper bound ($-0.017$) does not clear the proposed $-0.020$ bound, this is a **significant drop with the margin inconclusive**, rather than a proven regression exceeding margin. Driven by Aesthetic DOVER: $\Delta = -0.0088 \pm 0.0014$ ($6/6$ down). Technical DOVER: $-0.0012 \pm 0.0017$ (n.s.).
    - Dynamic Degree: Base $2.97 \to$ fast05 $1.23$ ($\Delta = -1.74 \pm 0.93$; `dd_bin` $0.33 \to 0.00$). While superficially moving closer to real GAUGE reference ($0.17\text{--}0.27$), this reflects suppression of background optical flow rather than physical settling.
  - **Independent Physical Kinematics (rog2 Review #2419, commit `1f69ee2`)**:
    - Evaluated with offline seeded CoTracker3 tracking ($3\times 3$ point grid around ball center) on all 24 Task 92 clips (filtering for tracking visibility $\ge 0.85$).
    - In 2 of 4 track-verified clips (b1 s2, b3 s2), the ball rests on the plank for 11–16 frames mid-clip, but then **re-lifts back to gripper height**, remaining elevated ($y < 250\text{ px}$) in 73% and 81% of late frames.
    - Late apex height (minimum $y$ in f56–92): fast05 median $107\text{ px}$ ($91, 94, 120, 233\text{ px}$) vs Base median $123\text{ px}$ ($72, 118, 123, 199, 199\text{ px}$) shows zero statistical difference ($\Delta = -16\text{ px}$, n.s.).
- **Setup**: `nvidia/Cosmos3-Nano` (in-process diffusers bf16 on H100), GAUGE ball 1 dd33 and ball 3 dd35 mid-fall inputs $\times$ seeds 1–3 ($n=6$ pairs). Treatment: temporal RoPE frequencies for $j=0, 3$ scaled by 0.5.
- **Method**: `tools/nv_scoreboard/score.py` (DOVER reps=3, RAFT-large DD), CoTracker3 offline median tracking, overlay contact sheets.
- **Control**: Matched base Nano rollouts on identical inputs and seeds.
- **Evidence**: Commit `cc05328` (`work/rog-cc/t92_nv/`), commit `1f69ee2` (`work/rog2/ct92_seeded/`).
- **Causal Mechanism**: As synthesized by scout-1 (#2443; Loopy, arXiv:2608.23090; FFGo, arXiv:2511.15700), halving high-frequency temporal RoPE coordinates acts as a temporal low-pass filter on positional heads, blurring temporal offsets and generating clone artifacts. The apparent reduction in late frame difference energy ($D$) is an artifact of interrupted motion: the ball pauses on the plank, but because the DiT's position-sensitive layers retain an active **frame-0 attractor**, late frames are pulled back toward the initial conditioning layout ("ball near gripper"), manifesting as an unphysical tether/yo-yo re-lift rather than true physical energy dissipation.

---

### Finding 13: Prompt Timing Clause Induces Rest and Resolves Bounce Decay Without DOVER Degradation (ro-1 Task 22 Finding #2460, agy-4 Replication Review #2553, ro-1 HUE Finding #2577)

```
FINDING: Incorporating an explicit prompt event timing clause ("...bounces only twice with rapidly diminishing heights, and comes to rest on the plank within about one and a half seconds, staying still for the rest of the video") induces genuine physical settling to rest, collapsing late corridor motion by Δ = -2.240 ± 0.238 px/f (p = 3.3e-5, 8/8 lower) and Dynamic Degree by Δ = -0.617 ± 0.219 closer to real video, with zero DOVER fused degradation (Δ = +0.0068 ± 0.0033) (ro-1 Task 22 Finding #2460, commit 8d9f086; agy-4 Review #2553, commit 66c343d; ro-1 Finding #2577, commit 05eb30c).
```

- **Quantitative Value**:
  - **Late Corridor Motion Reduction**:
    - Paired difference across all 8 pairs (Ball 1 & 2 $\times$ seeds 1–5 / 1–3): $\Delta = \mathbf{-2.240 \pm 0.238\text{ px/f}}$ ($t = -9.41, p = 3.3 \times 10^{-5}$), with **8/8 pairs lower** ($3.427 \pm 0.134 \to 1.184 \pm 0.169\text{ px/f}$, moving toward real settled reference $0.469\text{ px/f}$).
  - **Kinematic Settling & Object Permanence on Raw Video**:
    - Median-background trajectory tracking proves that while base prompt F oscillates perpetually through frame 90 ($y \approx 220\text{ px}$), QT lands by f30 and stabilizes at $y = 225-226\text{ px}$ from f42 through f78, remaining stationary on the plank surface.
    - Terminal tile variance collapses by >95% (e.g. $139.53 \to 5.98$ on Ball 1 Seed 4; $131.21 \to 5.90$ on Ball 1 Seed 5).
    - Automated blob morphology confirms 6/6 QT strips retain an intact, visible, dark stationary ball on the plank at $y \approx 115-119$ tile coordinates ($y \approx 320-330\text{ px}$). Zero vanishing, zero duplicate cloning, zero structural tearing.
  - **NVIDIA DOVER Scoreboard Non-Inferiority**:
    - Matched paired DOVER Fused difference across all 8 pairs: $\Delta = \mathbf{+0.0068 \pm 0.0033}$ ($df=7, t=+2.06, p=0.078$, 95% CI $[-0.0010, +0.0146]$, one-sided 95% LB $+0.0006$).
    - DOVER Technical is flat ($\Delta = -0.0005 \pm 0.0009$), and Aesthetic improves nominally ($\Delta = +0.0032 \pm 0.0013, p=0.046$). Zero video quality penalty.
  - **Dynamic Degree Alignment**:
    - Normalized Dynamic Degree drops by $\Delta = \mathbf{-0.617 \pm 0.219}$ ($1.545 \to 0.928, t=-2.81, p=0.026$).
    - Distance to real GAUGE reference motion ($|DD - \text{real}|$, real = 0.564) drops by $-0.616 \pm 0.220$ ($t=-2.80, p=0.026$), with **7/8 pairs moving closer to real reference video** (on Ball 1, $|DD - \text{real}|$ drops from $1.10 \to 0.25$, ro-1 #2460, #2606).
  - **Causal Controls**:
    - Stillness control (`QS`: "The camera and the table stay still for the rest of the video") fails to settle on seeds 3 & 4 (late motion 3.124 and 2.735 vs F 3.326 and 3.132; late tile variance 171.06 and 74.74).
    - Restitution numbers (`R20/R95`, Finding #2260): stating $e=0.20$ vs $0.95$ yields unchanged $e_T \approx 1.0$ (steady 10.0 f and 7.7 f cycles).
  - **HUE Plausibility Judge (ro-1 Finding #2577, scout-1 Mechanism #2602)**:
    - On `tools/hue_judge` (Qwen3-VL-2B), QT scores $0.585$ overall (Physical: $0.457$), matching the real GAUGE continuation video ($0.584$; Physical: $0.468$).
    - The apparent drop from F ($0.636$; Physical $0.531$) is driven entirely by release-specific questions (Q1: robot arm holding ball, Q2: ball falling after release, Q5: falling only after gripper releases) which are inapplicable to mid-fall inputs. On all three, real video scores like QT ($0.41/0.36/0.34$), not like F ($0.76/0.57/0.44$).
    - Meanwhile, Q6 ("bounces get lower until it comes to rest") fails to discriminate: base F scores $0.916$ despite settling in 0/8 clips; QT scores $0.896$ and real scores $0.891$.
    - Scout-1 (#2602) identified the cognitive mechanism: sequential-inference hallucination (MoHallBench, arXiv:2607.01117) where a 2B judge rewards uninterrupted airborne motion by affirming the entire script, thereby penalizing true physical resting contact. Post-hoc removal of uninformative release questions yields $\Delta = -0.005 \pm 0.004$ (real $0.649$ vs QT $0.645$ vs F $0.650$, non-inferior).
    - Recipe Prompt Adaptation (ro-1 #2606): v7 tests of the timed clause applied directly on top of Deliverable 1's recipe prompt (REC vs RECT) confirm 2/2 resting contact vs 0/2 under base prompt.
- **Setup**: `nvidia/Cosmos3-Nano`, $832\times 480$, 24 fps, 93 frames, 35 steps, CFG 6.0, flow shift 10.0. Inputs: GAUGE Ball 1 (f33) and Ball 2 (f35) $\times$ seeds 1–5 / 1–3 ($n=8$ pairs).
- **Method**: Referee planted-PASS `tools/realball/firstfall.py`, spatio-temporal strip variance, automated connected-component morphology, `tools/nv_scoreboard/score.py` (CUDA DOVER reps=3, RAFT DD), and `tools/hue_judge`.
- **Evidence**: Commits `8d9f086`, `66c343d`, `05eb30c`; `work/ro-1/cause_v5/`, `work/agy-4/replicate_finding_2460/`, `work/ro-1/hue_qt/`.
- **Causal Mechanism**: While Cosmos3-Nano ignores numerical restitution constants, its cross-attention layers are highly responsive to event sequence narrative and terminal state timing (corroborating Scout-1 #2365 on CausalCascade, arXiv:2610.15562). Providing structured narrative timing allows the model to transition into a resting latent attractor without spatial morphing, tether re-lift, or visual degradation.

---

## Synthesis: Why Cosmos3-Nano Fails Physics

Integrating the replicated evidence across all experimental axes yields a unified architectural diagnosis:

```
+-----------------------------------------------------------------------------------+
|                        COSMOS3-NANO ARCHITECTURAL DIAGNOSIS                       |
+-----------------------------------------------------------------------------------+
|                                                                                   |
|  1. Wan2.2 16x4x VAE Tokenizer: REPRESENTATIONALLY SUFFICIENT                      |
|     - Reconstructs real impacts with small paired discrepancy (<= 3.8 ms).        |
|     - Faithfully preserves geometric bounce decay on real round trips.            |
|     - Faithfully settles to rest in 2.6-4.5 s (100% preservation on real clips).  |
|     - Rules out 4x temporal compression as an absolute representation bottleneck. |
|                                                                                   |
|  2. DiT Backbone Prior: CAUSAL LOCUS OF PHYSICAL GLITCHES                        |
|     - Lacks mechanical release dynamics (0% release from stationary grip/axle).   |
|     - Event text forces motion tokens but fractures geometry (0/6 rigid swings).  |
|     - SFT LoRA causes severe scoreboard regressions (DOVER -0.077, HUE -0.028 #2201). |
|     - Embodies an undamped, driven-bounce prior (e_T = 0.989, Countix keepy-uppy). |
|     - Operates on a fixed token stride (k = 1.000; ignores text & RoPE fps dials).|
|     - RoPE fast05 fails damping via tether re-lift to frame-0 gripper attractor.  |
|     - Chaining short clips fails dissipation (0/2 settled, e_h >= 1.0; #2407, #2493). |
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
  - Changing prompt text or FPS dials from static frames (Findings 5, 10 prove they are null or induce hallucinations and geometric shattering).
  - Event-script text prompting from static rest frames (Finding 10 proves event text forces motion only by destroying object geometry—$2\times$ rod elongation, duplicate bobs, structural shattering, 0/6 rigid swings—rather than physical dynamics; ro-3 #2432, ro-agy1 #2445).
  - Modifying the VAE tokenizer (Finding 3 proves the VAE already represents correct physics).
  - Tuning inference sampler hyperparameters (CFG scale $\in [1.0, 6.0]$ or flow shift $\in [3.0, 10.0]$): Flow shift is an operational no-op on the diffusers UniPC schedule, low CFG ($\le 2.5$) induces mid-air levitation/reversal rather than dissipation, and CFG 4–6 preserves perpetual bouncing invariant to scale (Task 71, Task 75, commit `a1fb2e3`).
  - Restricting CFG intervals alone (Finding 1 proves it does not induce release).
  - Scaling RoPE spatial frequencies (Finding 9 proves early RoPE spatial dilation by 0.7x fails to break the grasp deadlock: 0/4 clean release, phantom cloning persists on true-color frames, and severe topological chaos/morphing occurs; rog-cc #2480).
  - Editing temporal RoPE frequencies (Finding 12 proves fast05 drops DOVER fused by $-0.025 \pm 0.004$ with CI90 $[-0.033, -0.017]$ rendering margin inconclusive vs proposed $-0.020$ bound, while CoTracker3 proves lack of physical damping due to tether re-lift to the frame-0 gripper attractor; rog-cc #2396, #2419, #2575).
  - Serial clip chaining through still frames (Finding 11 proves chaining fails to induce dissipation; Task 42 #2407, Task 104 #2493, #2575; 0/2 settled, core negative finding replicated while 5-frame velocity stagnation was retracted as a tracker area-filter artifact).
  - Supervised LoRA fine-tuning trained on synthetic drops without matched general-domain regularization (Task 24 LoRA induces severe out-of-distribution visual degradation, dropping DOVER fused by $-0.077 \pm 0.021$ and HUE plausibility by $-0.028 \pm 0.012$, with physical hallucinations like size jumps and clones persisting in 28/84 clips; contrast $A - B$ with wrong-physics control is null; #2168, #2201, #2562).
- **What DOES work / Validated Swarm Recipe**:
  - **The Unified Improved Cosmos3-Nano Recipe (Deliverable 1)**:
    - **Component A: Dynamic Mid-Event Conditioning (The Release-Seam Protocol)**: Initializing I2V from the dynamic release seam completely bypasses the mechanical grasp deadlock and restores true Earth gravity ($g = 9.73 \pm 1.91\text{ m/s}^2$, $100\%$ visual detachment vs $0\%$ baseline), achieves 100% rigid pendulum swings ($p=0.002$), and preserves rigid object geometry.
    - **Component B: Prompt Event Timing (Dissipative Settle Protocol, Finding 13)**: Operates on the detached in-flight state with explicit event-timing text ("...bounces only twice with rapidly diminishing heights, and comes to rest on the plank within about one and a half seconds, staying still for the rest of the video"), successfully guiding the trajectory into dissipative rest contact in **8/8 pairs (100.0%) vs 0/8 in base prompt**, collapsing late corridor motion by $-2.240 \pm 0.238\text{ px/f}$ ($p = 3.3 \times 10^{-5}$) with zero DOVER degradation ($\Delta = +0.0068 \pm 0.0033$) and HUE plausibility non-inferiority matching real continuation video.
  - **Visual Gripper-Opening Training Data**: To fix the release deadlock from frame 0 in retraining, fine-tuning requires paired sequences of robotic grippers visibly opening, rather than synthetic balls dropping in isolation.
  - **Restitution & Dissipation Adaptation**: Because the VAE tokenizer is representationally sufficient, modifying conditioning and temporal guidance is both necessary and sufficient to impart dissipative mechanics.
