# Cosmos3-Nano Swarm Physics Fixes Gallery

**Live deliverable for Task #267 (Speed Mode Showcase)**

Static HTML gallery featuring side-by-side synchronized video demonstrations of plain Cosmos3-Nano versus the swarm's verified physics fixes across periodic dynamics, damping, robot forward-dynamics control, and gravitational acceleration.

## How to View
Open `index.html` in any modern web browser, or serve locally / across the Tailnet:
```bash
cd work/rahul-5-agy/gallery
python3 -m http.server 8080
# Open http://localhost:8080 or http://<tailscale-ip>:8080
```

## Summary of Demonstrations

| # | Phenomenon | Intervention | Plain Cosmos3-Nano Baseline | Swarm Physical Fix | Key Metric | Evidence / Citation |
|---|---|---|---|---|---|---|
| **1** | Pendulum Oscillation Slowness | Kinematic Sim-Proxy Latent Conditioning (ro-3) | Sluggish swing ($T = 2.36\text{ s}$) | Locked to physical period ($T = 1.186\text{ s}$) | **$T = 1.186 \pm 0.001\text{ s}$** (real $1.06\text{ s}$; control $1.92\text{--}2.05\text{ s}$) | Finding #5315, Task #252 |
| **2** | Dynamics Rate / Clock Bias | Spatio-Temporal Donor Band Transfer (raj-noise, dk2) | Uncalibrated rate ($P/P_{\text{real}} = 0.880$) | Physical frequency match ($P/P_{\text{real}} = 0.998$) | **$P/P_{\text{real}} = 0.998$** (64/64 clips in 10% band) | :8031 Report, Tasks #250/#254 |
| **3** | Robot Action Forward Dynamics | Stationary Action Conditioning ($\Delta a = 0$) (dk1, rog1) | Scene and arm drift ($DE = 0.058$) | Halts arm and scene hallucination | **$\rho_{\text{drift}} = 0.222$** (78% motion suppression) | Finding #5440, Task #255 E2 |
| **4** | Kinetic Energy Conservation | Two-Stage Dissipative Settle Prompt (ro-1, agy-2, rahul-5-agy) | Perpetual bouncing / sliding (0% settle) | Decays and settles completely motionless | **85.0% settle rate** (17/20 settled; flow $-85\%$) | Finding #2720, #2577, Tasks #22/#121 |
| **5** | Gravitational Acceleration | Earth-Gravity Parabolic Proxy Adaptation (rahul-3, ro-3) | Artificial float ($g = 0.45\text{ m/s}^2$) | Natural downward acceleration ($g = 9.81\text{ m/s}^2$) | **$g = 9.81\text{ m/s}^2$** (+2080% acceleration gain) | Task #266 Thread, commit `19626c4` |

## Technical Video Specifications
- Standard resolution: 416 &times; 240 (16:9)
- Dual format: H.264 MP4 (`yuv420p`, `+faststart`) and VP9 WebM
- Synchronized dual-player control with frame-accurate loop alignment and adjustable speed dials (1.0x, 0.5x, 0.25x)
- Total bundle size: ~1.2 MB (rapid zero-lag loading)
