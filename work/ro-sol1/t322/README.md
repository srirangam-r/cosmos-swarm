# Task 322: attributed pendulum audit readout

Open `index.html` locally. This page presents agy-4's completed task 316 audit
(review 6380), using `audit_results.json` pinned to commit `27e60e7`. It preserves
all 20 source rows and four selections, including the flagged half-period result.
The filter changes row visibility only. It does not remeasure clips or refit data.

`source_receipt.json` records frozen source hashes. Copies of the audit JSON,
README and code are included. The source README contains numerical and attribution
inconsistencies; the page calls these out and renders the JSON. OLS standard errors
and bootstrap intervals are labeled separately. Visual review belongs to codex-1;
ro-sol1 supplied presentation and frame indexing. Original 317/320 remain unchanged.

Readout limits: supplied tempo, two scenes and two seeds, calibrated reference,
one reader disagreement, low measured flicker rather than visual certification.
No new physics result, reader calibration or NVIDIA-scoreboard pass is claimed.

From repository root:

```bash
python3 work/ro-sol1/t322/build.py
node work/ro-sol1/t322/render.cjs
```

The build reads pinned Git objects. Existing `work/ro-sol1/t317/` and `t320/` are
needed for local evidence navigation. Browser verification uses the installed
Brave binary (override with `DEMO_BROWSER`) over anonymous CDP pipes, closes the
browser, and requires no listening service. `browser_render.json` records actual
desktop/mobile rendering, filter behavior, exact receipt text and linked frames.

Prior work read past abstracts before creation: note 6387 / task note 6391.
[ProxyUp](https://arxiv.org/abs/2607.03732) §§4.2–5 supplies dynamics through
region-wise latent noising and stochastic flow relaxation (sim motion retention
.52 versus SDEdit .28). [GAUGE](https://arxiv.org/abs/2608.05948) C.2–C.3 uses
timestamped trajectories and physical geometry. [Physics-IQ](https://arxiv.org/abs/2501.09038v2)
Metrics/Results separates spatial, temporal and appearance agreement. This page
reuses those distinctions to present an existing audit; no published experiment
is repeated. No generation, GPU, paid compute, referee request or deployment.
