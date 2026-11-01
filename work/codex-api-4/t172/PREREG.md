# Task 172 independent audit protocol

Registered 2026-11-01 11:35 UTC, before viewing generated clips.
Prior exposure: author result #3810, published numerical tables, source code,
and codex-api-2's prior QC summary are known. I viewed the input frame.png to
set a crop; it depicts a free hanging pendulum near vertical. This is an
independent audit, not a never-seen-outcome replication.

1. Recompute published means/SE and paired differences independently from
   per-clip JSON. Confirm sidecar settings/endpoints and prompt suffixes.
2. Independently compute grayscale consecutive-frame MAE and first-frame
   MAE from all 18 pendulum clips and compare with saved rounded values.
   These are image-change proxies, not kinetic energy or physical damping.
3. Mask arm/seed labels for native-resolution review of all nine pend_rest
   clips, in random order. Inspect f0,8,...,88,92, with native cropped frames
   covering the entire pendulum; inspect all frames if ambiguity persists.
   Code visible bob/rod motion, geometric integrity, and clear rigid swing
   vs unclear; do not equate any small pixel-change threshold with release,
   physical rest, or deadlock. Freeze notes before opening label key.
4. Inspect slope estimator's runoff criterion mathematically; don't equate
   projected displacement with identity-preserving runoff. Native follow-up
   can identify counterexamples but is exploratory and labelled unblinded.
5. Report quantitative proxy findings as unvalidated and fixed-sample
   arithmetic, not a new physical measurement. No new model generations,
   tuning, referee submissions, or editing of source evidence.
