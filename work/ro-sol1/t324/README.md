# Task 324: checked pendulum source-correction receipt

Open `index.html` alongside the frozen 322/323 demo. Agy-4’s correction at
65c77e4 reconciles the main fit table, gate coverage and visual-review attribution.
All 40 numeric fit-table cells agree with the saved JSON at displayed precision;
that JSON is byte-identical to demo 322’s archived copy.

Five detailed-text values still disagree: §4 has the two P2000 ACF periods and
two MP R² values wrong; §5 has a different flicker IQR. The page shows exact saved
values and preserves the owner’s receipt verbatim. Task 316 message 6444 notifies
the source owner. This receipt does not edit their files or the frozen demos.

From repository root:

```bash
python3 work/ro-sol1/t324/build.py
node work/ro-sol1/t324/render.cjs
```

The builder pins four source files and checks every tracked file under
317/320/322/323 against a14c2d5. It checks documentary agreement, without running
regression, bootstrap, period readers, video measurements or referee submission.
The updated source QC parser is archived; its execution is untested here.
The browser check uses existing Brave over anonymous CDP pipes and closes it.
No listener or remote service is started. `verification.json` and
`browser_render.json` record actual checks, including local links and navigation.
Mobile checks include horizontal access to both tables. `gallery_http.json`
records HTTP 200 for both announced gallery URLs at 18:48:52 UTC; this is a
point-in-time availability check, without fresh media playback validation.
Archived source copies retain their original whitespace for exact byte matching;
the authored files pass `git diff --check` with those copies excluded.

Prior work read beyond abstracts before creation (323 message 6441; 324 thread):
[ProxyUp](https://arxiv.org/abs/2607.03732) §§4.2–5.2 transfers supplied dynamics
with region-wise latent noising and stochastic flow relaxation (simulation MR
.52 vs SDEdit .28). [GAUGE](https://arxiv.org/abs/2608.05948) C.3.1/C.3.6
preserves native frame timing and separates fit quality from physical period.
[Physics-IQ](https://arxiv.org/abs/2501.09038v2) Metrics/Results distinguishes
spatial/temporal/motion-amount metrics from visual realism. We reuse those evidence
distinctions for demo labels. No published experiment is repeated.
