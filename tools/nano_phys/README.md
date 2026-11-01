# Nano-Phys: Training-Free Physics Start for Cosmos3-Nano

`nano_phys` builds an analytical motion proxy from a supplied first image and parameters, then requests a noised-proxy latent start from a compatible Cosmos3-Nano endpoint. It requires no training or weight changes. The CLI has CPU software checks; a matched physical benchmark of this wrapper and its NVIDIA scoreboard remain pending.

The intended behavior is to transfer the proxy's prescribed motion while regenerating appearance. Historical task252 demonstrates period transfer with a separate implementation; it does not establish this wrapper's accuracy on new images, recovery of physical scale, or preservation of visual quality. The native schedule section below distinguishes sigma from a sampling step or a historical strength label.

---

## Quickstart

Run directly from the root of `cosmos-swarm`:

The commands below are illustrative: supply your image, geometry and a currently announced compatible endpoint. Coordinates refer to the resized output image (832×480 by default); the CLI does not transform them from the original image. Inspect the proxy before requesting model generation. Local in-process generation is disabled; use `--server`, `--proxy-only`, or `--emit-queue-job`.

Period, physical scale and initial velocity are supplied assumptions. With no `--period`, the pendulum builder assumes a 0.35 m length; its harmonic trajectory is not a large-amplitude pendulum solver. The ball builder assumes 539.8 pixels/m and a 0.25 s hold, neither exposed by this CLI. Setting `--g 9.81` alone does not calibrate a new image. A single image does not determine the direction or speed of motion.

### 1. Pendulum Physics
```bash
# Using a remote Cosmos3-Nano server endpoint
python -m tools.nano_phys \
  --image frame0.png \
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
  --image frame0.png \
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
  --image frame0.png \
  --prompt "Preview" \
  --physics pendulum --pivot 322,122 --bob 311,258 \
  --out out/preview.mp4 \
  --proxy-only
```

Both proxy builders preserve the resized input as the first raw frame before
encoding. The MP4 codec is lossy, so its decoded first frame can differ from
the input. This image-boundary guarantee does not certify the proxy mask,
physical calibration, or the endpoint's conditioning behavior.

---

## How It Works (The Mechanism)

1. **Analytical Kinematic Proxy (`nano_phys.proxy`)**:
   Extracts the moving object patch from Frame 0, fills the vacated background via Telea inpainting, and renders a prescribed trajectory:
   - **Pendulum**: Harmonic rotation about the axle; from-rest mode uses $\theta(t)=\theta_0\cos(2\pi t/P)$. Non-rest mode uses the supplied amplitude and direction.
   - **Ball Drop**: Sub-stepped integration with $g_{\text{px}}=g\times539.8$, after a 0.25 s hold, and restitution $v\leftarrow-e v$ at the supplied floor coordinate.
2. **VAE Latent Encoding**:
   The crude proxy video is encoded through Cosmos3-Nano's 3D causal VAE into latent representation $x_{0,\text{ref}} \in \mathbb{R}^{1 \times 48 \times T' \times H' \times W'}$.
3. **SDEdit Latent Noising**:
   Following SDEdit and ProxyUp, the latent is forward-diffused to intermediate step $k$:
   $$x_k = (1 - s_k) x_{0,\text{ref}} + s_k \epsilon, \quad \epsilon \sim \mathcal{N}(0, I)_{\text{CPU}}$$
   where $s_k$ comes from the endpoint's native grid. The archived 35-step grid below has step 19 at 0.89844, step 14 at 0.95868 and step 4 at 0.99140. Noise is drawn on CPU for cross-platform pairing (Charter Rule 11).
4. **Diffusion Denoising**:
   The endpoint is asked to denoise from step $k$. Whether the output preserves the trajectory and removes proxy artifacts must be measured on the resulting clip; this operation alone establishes neither result. This wrapper uses linear noising of a VAE proxy, rather than ProxyUp's full masked inversion and stochastic flow relaxation procedure.

---

## Native Sigma Schedule Reference (35-step UniPC)

`nano_phys` selects `--sigma` from the 35-step grid recorded in the four task281 [native receipts](../../work/raj-demos/sidecars/). This is a reference for that archived deployment, not certification of a current endpoint. All four full grids match; only two `sigmas_used` arrays match their expected executed suffix. The other two contain a 1,000-entry training schedule. [Runtime evidence](../../work/ro-sol1/t303/README.md) preserves this inconsistency without inferring what the model executed.

| Step $k$ | Sigma $s_k$ | Interpretation / Equivalent Arm |
| :---: | :---: | :--- |
| **4** | 0.99140 | Recorded grid entry; step fractions are separate from sigma |
| **14** | 0.95868 | Default start step |
| **19** | 0.89844 | Nearest recorded entry to requested sigma 0.90 |
| **27** | 0.57269 | Nearest recorded entry to requested sigma 0.60 |

Users can supply either `--start-step <int>` or `--sigma <float>` (e.g. `--sigma 0.90`, which overrides `--start-step`). Sigma must be finite in [0, 1] and requires `--steps 35`; other step counts require a valid step selection and do not receive a nominal sigma from this table. The CLI validates the selection before building a proxy. The runner retains returned metadata but does not certify grid, executed suffix or deployment identity; these remain executor acceptance checks. Historical benchmark rows below are not remapped or revalidated by this reference.

---

## Evidence and Benchmark Status

### Historical pendulum period transfer (task252)

ro-3's source experiment used two mid-swing images (pend10/11), seeds 1–2, 93 frames at 24 fps, and a separate `extra_params.proxy` hook with requested `sampler="nv"`. The source labels `t60` and `t90` are retained below; they are not certified step indices or sigmas of this CLI. The proxy period used an assumed 0.35 m length, rather than independently estimating metric scale from the image.

The following is a reconstruction of the reported `mp_T` rows, without remeasuring clips. Each group contains four scene×seed cells, with repeated scenes and seeds. Sample SD across those cells is descriptive spread, not a confidence interval or independent replication.

| Original group | Cells | Mean reported period (s) | Sample SD (s) | Range (s) |
| :--- | :---: | :---: | :---: | :---: |
| `phys_t60` | 4 | 1.186299 | 0.000635 | 1.185709–1.186975 |
| `phys_t90` | 4 | 1.186619 | 0.008573 | 1.179684–1.198707 |
| `x17_t60` | 4 | 2.018573 | 0.001264 | 2.017468–2.020244 |
| `x17_t90` | 4 | 2.002276 | 0.057288 | 1.919543–2.049057 |

The original plain controls report 0.843220 s (pend10) and 0.832609 s (pend11), one seed per image. The published GAUGE 2.36 s baseline is a different setup and is not their matched control. The historical rows support transfer of an externally prescribed period; they do not benchmark the shipped wrapper. One `x17_t90` cell (`sp_pend10_x17_t90_s1`) has `mp_flag="check"` and fit R²=0.186611. These JSON files contain no flicker measurements, so they do not support an all-clean or flicker <0.01 label.

Pinned source: [guided rows](https://github.com/srirangam-r/cosmos-swarm/blob/50409ebbc8b25c1a6ef0b22157c658247e6b2751/work/ro-3/task252/results_sp.json), [plain rows](https://github.com/srirangam-r/cosmos-swarm/blob/50409ebbc8b25c1a6ef0b22157c658247e6b2751/work/ro-3/task252/results_px.json), [job requests](https://github.com/srirangam-r/cosmos-swarm/blob/50409ebbc8b25c1a6ef0b22157c658247e6b2751/work/ro-3/task252/jobs_simproxy.jsonl). [Source and status record](../../work/ro-sol1/t305/README.md) retains task278's provenance audit and task266's owner QC.

### Ball demo (task266): no usable physical measurement

All 18 clips were generated and fetched: plain / requested g=9.81 / requested g=4.905, six seeds per arm, 93 frames, start step 12. The owner marked task266 failed after visual QC: camera pan/zoom, changing apparent ball size and no clean release made 0/18 clips measurable for fitted gravity or release-to-contact timing. This is attributed qualitative QC, not a planted-validated estimate or proof that proxy transfer cannot work. No output-g estimate or improvement is established; the supplied proxy constants must not be presented as measured Nano gravity.

### Current wrapper acceptance

- CPU operational checks cover queue attachments and settings ([297](../../work/ro-sol1/t297/README.md)), raw first-frame identity and later-frame invariance ([302](../../work/ro-sol1/t302/README.md)), and sigma/start guards plus partial archived native metadata ([303](../../work/ro-sol1/t303/README.md)). These are software results.
- Independent [304 pixel/compositing review](../../work/rahul-api-codex/t304/README.md) accepts the raw boundary correction but rejects clean compositing on the tested fixtures: source-bob residue, inpainting smear and strip-carried rig texture remain. The clips are coarse motion scaffolds. Raw first-frame identity does not establish a clean mask or an unchanged stationary hold in later frames.
- Fresh-frame task277 has no generated or measured clips in the published [298 ledger](../../work/rahul-api-codex/t298/current_no_clips_report.json). Its independent period reader's raw referee verdict remains **FAIL / UNVALIDATED**; human coverage review #5939 is unresolved in the [289 record](../../work/ro-sol1/t289/README.md).
- Matched before/after physics measurements, new-scene generalization and the wrapper's DOVER, motion fidelity, plausibility and robot-prediction scoreboard are pending. No complete physics fix or NVIDIA non-regression result is established for this wrapper.

Relevant methods: [ProxyUp](https://arxiv.org/abs/2607.03732) separates prescribed dynamics from coherence using masked inversion and stochastic relaxation; [GAUGE](https://arxiv.org/abs/2608.05948) measures calibrated trajectories under matched inputs; [Physics-IQ](https://arxiv.org/abs/2501.09038) separates spatial motion, timing and visual realism. These papers motivate the evaluation; their results are not measurements of this CLI.

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
| `--period` | float | derived from assumed 0.35 m | Supplied target period (s); not inferred from pixels |
| `--direction`| choice | `inward` | Swing direction (`inward` or `outward`) |
| `--no-release-from-rest` | flag | `False` | Do not enforce release from rest ($\theta'(0)=0$) |
| `--center` | `X,Y` | `None` | Ball center coordinate |
| `--floor-y` | int | `340` | Floor impact pixel level |
| `--g` | float | `9.81` | Gravitational constant ($m/s^2$) |
| `--e` | float | `0.58` | Coefficient of restitution |
| `--start-step`| int | `14` | Intermediate diffusion step (archived 35-step grid: sigma 0.95868) |
| `--sigma` | float | `None` | Finite sigma in [0, 1], requires 35 steps (`0.90` maps to step 19) |
| `--seed` | int | `1` | CPU RNG seed |
| `--proxy-only`| flag | `False` | Only generate and save the proxy video |
| `--emit-queue-job` | flag | `False` | Output JSONL job line for `cosmos_queue.py` |
