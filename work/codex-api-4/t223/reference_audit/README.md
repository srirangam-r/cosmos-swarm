# Historical task-141 integration and missing-label sensitivity

This is a **retrospective same-label statistical audit**, within Program N task
223. It is not Raj's E0-E3 data or a new physical finding. The source aggregate
claims were known (#4664/#4407). Board #4720 fixed the full 90-cell grid and
exhaustive binary-completion analysis before this audit was coded. No source
labels, author findings, classifier, server, recipe or Deliverables 1-3 changed.

The frozen task-141 CSV contains 89 binary rest codes and one UNCLEAR code:
`t141q8_b1dd33_F_s1`. The unchanged E1/E2 adapter correctly reports 89 valid,
1 unknown, and blocks primary decomposition and all four registered tests.
The historical author's `analyze_grid.py` uses an additive seed + condition-cell
fit for this missing value; its reported prompt share 0.520169 and seed share
0.183302 therefore depend on that imputation convention.

The two possible **hypothetical** binary completions give:

| Quantity | Unknown=0 | Unknown=1 |
|---|---:|---:|
| Prompt SS / total SS | 0.532531 | 0.498922 |
| Seed SS / total SS | 0.158010 | 0.202586 |
| Seed × prompt SS / total SS | 0.145435 | 0.136853 |
| QT − F mean code difference | +0.766667 | +0.733333 |
| Conditional seed-bootstrap 95% interval, QT − F | [0.566667, 0.933333] | [0.533333, 0.900000] |
| QT − F exact two-sided seed sign-flip p | 0.00390625 | 0.00390625 |
| QT − F Holm p, four-test retrospective family | 0.01171875 | 0.01171875 |
| QT − N mean code difference | +0.700000 | +0.700000 |
| QT − N exact seed sign-flip p | 0.0078125 | 0.0078125 |
| Omnibus whole-seed prompt permutation p | 0.0003 | 0.0003 |

Thus one unknown label does not reverse the chosen grid's descriptive
prompt-versus-seed ordering or QT−F contrast. These are identification ranges
over **labels**, not confidence intervals. Bootstrap intervals are conditional
on each hypothetical completion, not a calibrated joint interval for sampling
and label uncertainty. Omnibus p uses 9,999 draws and plus-one correction; exact
sign flips enumerate all 1,024 whole-seed flips. The retrospective family is
omnibus, QT−F, QT−N and N−F; it was not the original author's test family.

`summary.json` reports all seven components and conditional intervals. No
imputed or hypothetical value is inserted into the original file. The original
blocked result remains `blocked_original.json`, alongside the two explicitly
marked hypothetical results. `historical_design.json` uses the adapter's E2
schema routing only; its scope explicitly says it is **not actual E2**.
Each artifact hash identifies the canonical source CSV **label record**, not
an MP4, initial-noise tensor, or verified execution. No native clips were read.

Reproduce from the shared repository root:

```bash
python3 work/codex-api-4/t223/reference_audit/run.py
cd work/codex-api-4/t223/reference_audit
sha256sum -c SHA256SUMS
```

Fifteen checks verify the 90-cell join, unknown-versus-missing handling, blocked
inference and retained four-test family, all seven components against independent
exact-rational scalar inclusion-exclusion, and all three paired contrasts against
independent exact scalar sign enumeration. No live outcomes or classifier
accuracy are validated by these checks. Source copies match immutable shared
commit `028723bdbe6060d161be6849b849e965b4fa5dae` under
`work/ro-agy1/t202_seedshare_audit/data/`.

The q8 historical grid uses seeds 1–10, prompts F/QT/N, and three inputs
`b1dd33`, `b2dd35`, `b2dd37` from one GAUGE camera setup. It is the published
189-frame, 24-fps, 832×480, 35-step, CFG-6, no-negative-prompt experiment;
the board stack uses Karras sigmas and ignores requested `flow_shift=10`.
Those settings are historical declarations, not independently audited here.
The source CSV contains unvalidated eye codes. This is not evidence of general
causality, planted-pass rest measurement, physical dissipation, an improved
recipe, or a NVIDIA-scoreboard pass. Actual raj-noise E0-E3 outcomes remain
unopened; the owner design manifest and execution evidence are still pending.
