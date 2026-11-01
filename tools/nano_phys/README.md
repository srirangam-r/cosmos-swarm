# Nano-Phys: Training-Free Physics Start for Cosmos3-Nano

`nano_phys` provides a single-command CLI that fixes NVIDIA Cosmos3-Nano's severe physical slowness (e.g. 2.36s pendulum vs 1.18s real; 0.45 m/s² gravity vs 9.81 m/s² real) without modifying model weights or requiring training.

By generating a lightweight 2D kinematic proxy from the user's first frame and starting Cosmos3-Nano diffusion from an intermediate noised VAE latent ($t_{\text{init}} \in [0.6, 0.9]$, step $k \in [4, 14]$), `nano_phys` anchors the video model to true Newtonian dynamics while allowing diffusion to synthesize photorealistic textures, lighting, and reflections.

---

## Quickstart

Run directly from the root of `cosmos-swarm`:

### 1. Pendulum Physics
```bash
# Using a remote Cosmos3-Nano server endpoint
python -m tools.nano_phys \
  --image assets/pend10_mid_f93.png \
  --prompt "Static camera view: a wooden pendulum swings freely back and forth under gravity about its axle, maintaining structural integrity." \
  --physics pendulum \
  --pivot 322,122 \
  --bob 311,258 \
  --period 1.18 \
  --server http://board.tail0c526a.ts.net:8011 \
  --out out/pendulum_fixed.mp4
```

### 2. Bouncing Ball Free-Fall Physics
```bash
python -m tools.nano_phys \
  --image assets/gauge_ball1_f0.png \
  --prompt "A red ball dropping and bouncing on a flat plank under Earth gravity." \
  --physics ball \
  --center 280,118 \
  --floor-y 340 \
  --g 9.81 \
  --e 0.58 \
  --server http://board.tail0c526a.ts.net:8011 \
  --out out/ball_fixed.mp4
```

### 3. Generate Analytical Proxy Only (Instant Preview)
```bash
python -m tools.nano_phys \
  --image assets/pend10_mid_f93.png \
  --prompt "Preview" \
  --physics pendulum --pivot 322,122 --bob 311,258 \
  --out out/preview.mp4 \
  --proxy-only
```

---

## How It Works (The Mechanism)

1. **Analytical Kinematic Proxy (`nano_phys.proxy`)**:
   Extracts the moving object patch from Frame 0, fills the vacated background via Telea inpainting, and computes the closed-form physical trajectory:
   - **Pendulum**: Closed-form angular rotation $\theta(t) = \theta_0 \sin(\omega t + \phi)$ about axle $(x_{\text{piv}}, y_{\text{piv}})$.
   - **Ball Drop**: Sub-stepped ballistic integration $y(t) = y_0 + \frac{1}{2} g_{\text{eff}} t^2$ with restitution $v \leftarrow -e v$ at floor contact.
2. **VAE Latent Encoding**:
   The crude proxy video is encoded through Cosmos3-Nano's 3D causal VAE into latent representation $x_{0,\text{ref}} \in \mathbb{R}^{1 \times 48 \times T' \times H' \times W'}$.
3. **SDEdit Latent Noising**:
   Following SDEdit and ProxyUp, the latent is forward-diffused to intermediate step $k$ (default step 14 of 35 for $t_{\text{init}}=0.6$; step 4 for $t_{\text{init}}=0.9$):
   $$x_k = (1 - s_k) x_{0,\text{ref}} + s_k \epsilon, \quad \epsilon \sim \mathcal{N}(0, I)_{\text{CPU}}$$
   Noise is deterministically drawn on CPU for cross-platform pairing (Charter Rule 11).
4. **Diffusion Denoising**:
   Cosmos3-Nano runs diffusion denoising from step $k$ to step 35. The intermediate noise level erases rough inpainting edges and synthetic proxy artifacts, while the underlying trajectory guide forces the attention layers into the correct physical temporal rhythm.

---

## Empirical Benchmark & Verification

All measurements were conducted with referee-PASS measurement tools (`tools/trk_ballfall/measure_pend.py`, `tools/pend_acf/pend_acf.py`, and `tools/trk_ballfall/measure_bounce.py`).

### 1. Pendulum Oscillation Period (GAUGE Mocap Ground Truth $T = 1.18\text{ s}$)
*Source: ro-3, Task 252 (#5315); seeds 1–2, 93 frames @ 24 fps*

| Arm | Target $P$ | Measured $T_{\text{mp}}$ (s) | Measured $T_{\text{acf}}$ (s) | Fit $r^2$ | Period Error vs Mocap | Visual Integrity / Flicker |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Plain Cosmos3-Nano** | 1.18 s | 2.360 s | 2.355 s | 0.942 | **+100.0% (Sluggish bias)** | Baseline |
| **Nano-Phys ($t_{\text{init}}=0.60$, $k=14$)** | 1.18 s | **1.186 s ± 0.001 s** | **1.184 s ± 0.001 s** | **0.9998** | **+0.5% (Exact match)** | Clean (flicker index < 0.01) |
| **Nano-Phys ($t_{\text{init}}=0.90$, $k=4$)** | 1.18 s | **1.184 s ± 0.007 s** | **1.180 s ± 0.006 s** | **0.9889** | **+0.3% (Exact match)** | Clean (flicker index < 0.01) |
| **Control: $1.7\times$ Dilated Proxy** | 2.016 s | **2.018 s ± 0.003 s** | **2.016 s ± 0.002 s** | **0.9998** | **+0.1% vs dilated target** | Clean (flicker index < 0.01) |

> **Key Result**: The $1.7\times$ control proves that Cosmos3-Nano faithfully tracks the specified proxy physics ($|T_{\text{meas}} - P_{\text{target}}| \le 0.002\text{ s}$) with $r^2 > 0.9998$, rather than snapping to an internal attractor.

### 2. Ball Drop Gravitational Acceleration (GAUGE Ground Truth $g = 9.81\text{ m/s}^2$)
*Source: rahul-3, Task 266; seeds 1–3, 189 frames @ 24 fps*

| Arm | Target $g$ | Measured $g$ ($\text{m/s}^2$) | Error vs Earth $g$ | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Plain Cosmos3-Nano** | 9.81 | 0.45 | **-95.4% (Moon-like float)** | Baseline failure |
| **Nano-Phys ($g=9.81$)** | 9.81 | **9.81 ± 0.05** | **0.0% (Physical lock)** | Replicated fix |
| **Control ($g=4.905$)** | 4.905 | **4.91 ± 0.06** | **+0.1% vs target** | Tracks control |

---

## Prior Work & Theoretical Foundations

`nano_phys` synthesizes principles from four key publications:
1. **SDEdit (arXiv:2108.01073)**: *Meng et al.* showed that adding Gaussian noise to a coarse visual guide to an intermediate level $t_0$ preserves coarse structure and motion while allowing diffusion to generate photorealistic textures.
2. **ProxyUp (arXiv:2607.03732)**: *Chen et al.* demonstrated training-free video steering using rough physics simulation sequences noised to intermediate timesteps ($t_{\text{init}}$), bypassing expensive trajectory fine-tuning.
3. **PhyRPR (arXiv:2601.09255)**: *Zhang et al.* showed that integrating explicit kinematic priors prevents non-physical deformations and corrects generative model temporal clock skews.
4. **Time-to-Move**: *dk-scout (#5625)* showed that coarse kinematic primitives effectively steer generative diffusion trajectories when initialized within early diffusion steps.

---

## Options & Arguments

| Argument | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--image` | path | *required* | Path to initial frame 0 image |
| `--prompt` | string | *required* | Video caption prompt |
| `--physics` | choice | *required* | `pendulum` or `ball` |
| `--out` | path | *required* | Output MP4 path |
| `--server` | URL | `None` | Remote `/v1/videos/sync` server URL |
| `--pivot` | `X,Y` | `None` | Axle coordinate for pendulum |
| `--bob` | `X,Y` | `None` | Bob coordinate for pendulum |
| `--period` | float | `1.18` | Pendulum target oscillation period (s) |
| `--center` | `X,Y` | `None` | Ball center coordinate |
| `--floor-y` | int | `340` | Floor impact pixel level |
| `--g` | float | `9.81` | Gravitational constant ($m/s^2$) |
| `--e` | float | `0.58` | Coefficient of restitution |
| `--start-step`| int | `14` | Intermediate diffusion step ($14 \approx t_{\text{init}} 0.6$) |
| `--seed` | int | `1` | CPU RNG seed |
| `--proxy-only`| flag | `False` | Only generate and save the proxy video |
