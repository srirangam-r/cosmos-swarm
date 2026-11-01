# Task 314: independent audit of benchmark 276

**Disposition: challenge the strength of finding 6239; accept its published count and median arithmetic.** This is an independent aggregate/provenance audit of reused reader outputs. It is **not independent media measurement, planted validation, or physics replication**.

Reviewed source: [`a33fc5a`, task 276](https://github.com/srirangam-r/cosmos-swarm/tree/a33fc5a/work/dk2/t276). Author artifacts are unchanged. Human instruction 6256 is respected: no edits to the submission's root README or `reports/board/`.

## What the data support

The frozen gate is ACF flag `ok`, flicker < 0.08, and agreement between MP and ACF periods within 10%. The MP flag itself is not part of this gate. Independent code reconstructs all 42 gates and every published count and point median from the scalar fields, without importing the author's analyzer.

| Arm | All slots | Clean | Clean and within 10% of supplied reference | Median ACF/reference among clean | Median flicker, all slots |
|---|---:|---:|---:|---:|---:|
| Plain | 18 | 4 | 1 | 0.680095 | 0.0128 |
| Nano-Phys | 18 | 12 | 12 | 1.011457 | 0.0071 |
| Wrong-period ×1.7 | 6 | 1 | 0 | 1.596482 | 0.0071 |

The 12 Nano-Phys successes are all three seeds of `real_12`, `real_17`, `real_18`, and `real_19`. `real_09` and `real_16` fail the clean gate in all three seeds. The useful reported result is therefore **12/18**, with a conditional period estimate on four successful scenes, rather than 100% success on six scenes.

### Paired scene uncertainty

This audit adds descriptive intervals from resampling the **six scenes**, retaining all paired arms and seeds within each selected scene. It enumerates all 6⁶ = 46,656 ordered draws through 462 weighted multisets; direct ordered enumeration independently checks both rate intervals. These post hoc descriptive estimates were not part of the author's preregistration.

| Nano-Phys minus plain | Estimate | Exact paired scene bootstrap 95% percentile interval | Two-sided scene sign-flip p |
|---|---:|---:|---:|
| Clean fraction | +44.44 percentage points | [0.00, 88.89] pp | 0.1875 |
| Clean **and** within 10%, all slots | +61.11 percentage points | [16.67, 100.00] pp | 0.1250 |

The conditional Nano-Phys clean-period median has a scene-bootstrap interval [0.999247, 1.023147]. Both the plain and Nano-Phys conditional median distributions omit 64/46,656 resamples with no clean observations; this omission is explicit in the JSON. Neither that interval nor the author's IID clean-clip interval includes the failure probability in its estimand. These six dev scenes do not establish broad scene generalization or a causal mechanism.

Within the four successful Nano-Phys scenes, three-seed sample SDs of ACF/reference are 0.03055, 0.00543, 0.01499 and 0.05150. These are conditional seed spreads, not NVIDIA motion-fidelity scores or an evaluation of the two failed scenes.

## What needs narrower wording

1. **The wrong-period control is provisional.** Only 1/6 passes the frozen clean gate, at ratio 1.596482. The reported 1.731752 median is arithmetically correct across four numerical ACF estimates, but includes three `check` rows; two other rows have no ACF estimate. Keep this numerical diagnostic separate from the clean-gated table. All six controls use seed 1, so the charter's three-seed matched-control requirement for building on a claimed cause is unmet. This audit does not refute proxy transfer, but these data do not prove “exact causal steering.”
2. **No `short_clip` flag exists in the inspected ACF source.** It emits `fail`, `check`, or `ok`; `ok` depends on second-minimum consistency when available and finite window spread below 0.10. The three >2 s control estimates are `check`, but the saved aggregate rows omit the window estimates needed to attribute each failure. A duration explanation is plausible, not established by a flag or fixed 2 s rule.
3. **Flicker is low, not zero.** Nano-Phys's median is 0.0071 and range is [0.0057, 0.0085], from reused rounded scalar outputs. No DOVER or other visual-quality score was run by this review.
4. **The supplied period comes from the real video.** `frames.json` explicitly uses MP reference periods divided by 25 Hz, rounded to four decimals. This is a measured real-video reference, not a separately supplied motion-capture table. The builder supplies that reference period to the proxy. It tests rendering of a supplied period on new frames; it does not show inference of the period from frame 0 and the prompt, nor an end-to-end first-frame-only recipe with an unavailable real-future period.
5. **State the sampler as recorded.** Requests say 35 steps, flow_shift 10, latent start index 19. All 24 latent receipts record a 36-entry grid, actual recorded start sigma **0.89844**, and the matching 17-entry suffix including the terminal zero (16 intervals). All 42 receipts identify old `server.py` MD5 prefix `04e8e0de81`. Nine plain receipts have 36 entries matching the latent full grid; nine have 1000 entries. The known old post-lock recording window remains relevant. Metadata consistency is not an executed-step trace, and this review neither attributes historical causes nor authenticates loaded checkpoint bytes.

The snapshot has 126 JSON sidecars and contact strips but no generated MP4s. It includes the six input images and twelve proxy MP4s, whose source bytes are hashed in this review. Labels and request metadata do not independently bind generated media to the published scalar measurements.

No NVIDIA-scoreboard non-regression, new prompt/scene-family generalization, reader validation, or sealed-test improvement follows from this audit. The original MP planted-PASS claim is not revalidated here.

## Reproduce the aggregate audit

From the repository root, with git objects for `a33fc5a` available:

```bash
python3 work/rahul-api-codex/t314/audit.py
```

Python standard library only; no model, media decoding, networking, queue submission, or GPU. Reads frozen git objects rather than mutable working-tree author files. Output:

- `audit_results.json`: rebuilt summaries, per-scene coverage, conditional seed spreads, exact bootstrap distributions' summaries, six individual controls, 42 receipt records, and checks.
- `source_manifest.json`: SHA256 and byte count for 154 inspected source artifacts at the full source commit.
- `audit_stdout.json`: captured run summary.

**250/250 checks pass**, including the 42-slot identity set, individual gate/ratio reconstruction, author summary equality, request constants, one prompt, 42 unique queue IDs, native grid/suffix checks, and weighted-versus-direct bootstrap agreement. These validate this aggregate calculation, not the underlying measuring tools.

## Prior work read before creation and claim

Parent task note 6245 and child note 6248 record the prior-work check.

- [ProxyUp, July 2026](https://arxiv.org/abs/2607.03732), §§4.3–5 and C.3: region-wise intermediate-time inversion plus stochastic flow relaxation; simulation motion rationality 0.52 versus SDEdit 0.28. Reuse its separation of supplied-motion adherence and appearance quality; do not rerun established generic transfer as novelty.
- [GAUGE, August 2026](https://arxiv.org/abs/2608.05948), C.3.1/C.3.6: original timestamps, fixed-pivot angular fits and independent radius/period diagnostics. Reuse the distinction between fit quality, calibrated timing and geometry.
- [Physics-IQ](https://arxiv.org/abs/2501.09038), Metrics: repeated real takes provide a physical-variance reference; spatial and temporal motion agreement are distinct from visual realism. Reuse explicit uncertainty and separate quality/physics evidence.

The open deliverable here was the audit of this specific Nano benchmark's denominators, conditional uncertainty, control gate, and recorded sampler, not a new general transfer method.
