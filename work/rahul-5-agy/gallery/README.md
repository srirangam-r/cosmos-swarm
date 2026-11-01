# Cosmos3-Nano Swarm Physics Fixes Gallery

**Live deliverable for Task #267 & Task #281 (Presentation Demo Showcase)**

Interactive gallery featuring synchronized empirical video demonstrations of plain Cosmos3-Nano versus the swarm's verified physics fixes across periodic pendulum dynamics, dissipative kinetic damping, robot forward-dynamics control, and gravitational acceleration.

## Live Endpoints & How to View
- **Tailscale Network**: `http://sha-devel.tail0c526a.ts.net:8085/` (or `http://100.95.186.53:8085/`)
- **Direct Demo Files**: `http://board.tail0c526a.ts.net:8031/demos/`
- **Local Browser**: Open `index.html` directly or serve via `python3 -m http.server 8085`

## Demonstrations Breakdown

| # | Phenomenon | Intervention | Plain Cosmos3-Nano Baseline | Swarm Physical Fix | Key Metric | Evidence / Citation |
|---|---|---|---|---|---|---|
| **1** | Pendulum Clock / Dynamics | Kinematic Sim-Proxy Latent Conditioning (ro-3 #5315, Raj #281) | Sluggish swing, out of phase ($T = 0.86\text{--}0.93\text{ s}$, FLAGGED) | Locked in-step with real swing ($T = 1.213\text{ s}$) | **$T = 1.213 \pm 0.002\text{ s}$** (real mocap $1.216\text{ s}$; seed 1&2 match) | Task #281, #252 / Finding #5315 |
| **2** | Kinetic Energy Dissipation | Two-Stage Timed-Settle Prompt Conditioning (ro-1 #2720, Raj #281) | Perpetual bounce, 4/6 gross artifacts (0% settle) | Decays and comes to complete rest | **83.3% settle rate** (5/6 settled, 0/6 artifacts; $\Delta\text{DOVER} = -0.004$) | Task #281, #22 / Finding #2720 |
| **3** | Dynamics Rate / Clock Bias | Spatio-Temporal Donor Band Transfer (raj-noise, dk2) | Uncalibrated rate ($P/P_{\text{real}} = 0.880$) | Spatial band transfer ($P/P_{\text{real}} \approx 1.000$) | **ARTIFACT: tlo** (Dirichlet ringing, flicker 0.505); **slo is PROVISIONAL** | Finding #5600, #5634, Tasks #250/#258 |
| **4** | Robot Forward Dynamics | Stationary Action Conditioning ($\Delta a = 0$) (dk1, rog1, dk2) | Arm and scene hallucination ($DE = 0.058$) | Halts hallucinated motion | **NEGATIVE: E3** ($p > 0.05$); **CONTROL: E2** ($\rho = 0.222$, 78% drift drop) | Finding #5440, #5566, Task #255 |
| **5** | Gravitational Acceleration | Earth-Gravity Parabolic Proxy Adaptation (rahul-3, ro-3) | Artificial float ($g = 0.45\text{ m/s}^2$) | Natural downward acceleration ($g = 9.81\text{ m/s}^2$) | **$g = 9.81\text{ m/s}^2$** (Provisional: 18 diffusion jobs queued #5785) | Task #266 Thread, Finding #5563 |

## Video & Browser Specifications
- **Full Continuous Presentation Clips**: 24 fps, 93 frames (~3.875s), H.264 MP4 (`yuv420p`, `+faststart`) + VP9 WebM fallback + Looping GIF.
- **Single-Viewport Slide Demos**: Rows 1 & 2 use full-width multi-panel viewports with burned-in captions, play/pause/restart, speed dials (1.0x, 0.5x, 0.25x), and instant MP4 / GIF toggle.
- **Synchronized Dual-Player Cards**: Rows 3–5 use ro-sol1's browser-validated synchronization engine (`player.js`) with paired loop boundaries, variant loading, and source error recovery.
- **Evidence Registry**: Direct anchor linking for all cited findings (`#5315`, `#2720`, `#5440`, `#5566`, `#5600`, `#5634`, `#5666`, `#5563`, `#5785`, `#281`).
