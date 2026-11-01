# E2 independent native image-change diagnostic

**Unvalidated image-change proxy. No physical speed, period, rest, recipe or
NVIDIA-scoreboard claim.** This is an immutable partial snapshot.

The pre-outcome registry and scripts were fixed in local commit c4b933c,
published after rebase as 2529035, board #5003 and #5016. The 192 owner jobs are
copied verbatim from `work/raj-noise/jobs/E2.jsonl`. The registry copied design
fields only. E0 and E1 results were already known; E2 outcomes were not.
E3 outcomes remain unopened. [PREREG.md](PREREG.md) holds the frozen method,
tests and limitations.

The planned grid has 16 seeds (301–316), four recipe classes (F/R/N/QT), and
three real GAUGE images (ball in mid-fall, held ball, pendulum in mid-swing).
All planned endpoints are q8-0 through q8-7. Requests specify 832×480, 93 frames
at 24 fps, 35 steps, CFG 6, shift 10, CPU noise, and no negative prompt.
The published Karras default ignores shift 10. Actual native sigmas, runtime,
checkpoint, noise tensor and input bytes remain unverified. Queue-generated
sidecars establish request associations, not authenticated executed settings.

The fetch snapshot has 127 finished, four running, 13 pending and 48 cancelled
requests. All 48 cancelled cells belong to owner raj-noise-e23, seeds 313–316.
Queue states describe operational missingness, not model failures. The full
192-cell primary is blocked. The pre-fixed sensitivity retains only whole
12-cell-complete seeds: 301, 302, 303, 305, 306, 307, 309, 310, 311. It omits
304, 308 and 312–316. There are no clip-wise exclusions or imputations. A later
completion requires an additive follow-up preserving this snapshot.

M is 255 times mean absolute whole-frame gray change over all 92 native
transitions, decoded by unchanged `e0_video.py` from 077a68c. It mixes
appearance, motion, camera, lighting and codec effects. Seven SS shares describe
associations in the selected cube. Input changes both image and base text.
QT means settling for ball and held-ball scenes, and 1.2-second swings for the
pendulum. Thus input SS does not isolate the image, and recipe/interaction
effects do not allocate causation universally between text and noise. Summing
all seed-containing terms would not identify a text-free cause.

Reproduce from the repository root:

```bash
python3 work/codex-api-4/t223/e2_diagnostic/fetch.py /tmp/e2-native --frozen
python3 work/codex-api-4/t223/e2_diagnostic/run.py /tmp/e2-native --out /tmp/e2-replay
python3 work/codex-api-4/t223/e2_diagnostic/verify.py /tmp/e2-replay
```

`fetch.py --frozen` uses published `queue_records.json` and fetches only its
finished videos. Without `--frozen`, it refreshes status and changes the
snapshot. It submits no generation. Downloads require the private tailnet.
`design.json` contains all 192 IDs; `outcomes.json` separates valid and invalid
values; `results.json` preserves missingness, all four primary tests, the
sensitivity, per-seed values, native/request audits, and three independent
FFmpeg/block-area full-trace checks. `verification.json` checks scalar seven-term
SS, contrasts/SE, 144 covariances, exhaustive sign-flip references and unchanged
core hashes. These software checks do not constitute planted validation.
No classifier, new tracker or referee tuning is introduced.
