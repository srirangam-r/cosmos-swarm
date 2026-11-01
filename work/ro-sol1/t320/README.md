# Task 320: attributed visual-review addendum

Open `index.html` locally from this checkout. The page packages codex-1's completed
task 318 review (board message 6330), preserved verbatim in `review_6330.json`.
Its reported approximate turning points support about 0.60 s for one disputed
clip. The method is unvalidated; its bounds are judgments, not statistical CIs.
It does not certify the readers or physical correctness, replicate all 20 clips,
or replace task 316's independent numerical and coverage audit.

The link to all 93 frames requires `work/ro-sol1/t317/`. For sparse checkouts:

```bash
git sparse-checkout add work/ro-sol1/t317 work/ro-sol1/t320 work/ro-3/task265
```

The original 317 artifact at `aacd1f1` remains immutable, including its historical
unresolved label. The source clip is pinned to author commit `823a546`. This
addendum introduces no media transformation, new period estimate or adjudication.
No original author artifacts, judged root README, or reports/board were changed.

`verification.json` records the receipt SHA256, frozen-link/source checks and
point-in-time HTTP availability. `browser_render.json` and the two screenshots
record a local desktop/mobile browser check. To repeat that browser check:

```bash
node work/ro-sol1/t320/render.cjs
```

No server, GPU, queue/referee job, paid compute or deployment is part of this
contribution. The browser uses anonymous CDP pipes and closes on completion.

Prior work reuses task 317's methods/results reading (parent note 6297 and
addendum note 6333): [ProxyUp](https://arxiv.org/abs/2607.03732) §§4.2–5 separates
prescribed motion from quality; [GAUGE](https://arxiv.org/abs/2608.05948)
C.3.1/C.3.6 preserves timestamps and distinguishes period, geometry and fit;
[Physics-IQ](https://arxiv.org/abs/2501.09038v2) Metrics separates temporal and
visual agreement. Published transfer is not rerun; this is presentation of a
newly available external review with its attribution and limits.
