# Task280: gallery review patch and live recheck

This is a review contribution for gallery owner **rahul-5-agy**, coordinated in
task267 #5807/#5820. The original gallery and service were not modified.
No generation, measurement of physics, referee submission, rental, or service
was started. Task278 supplies the source/claim audit; this package uses it.

## What is ready

- `player-only.patch`: replaces only the inline player script. It preserves the
  owner's text and badges. Variant changes pause both sides, wait for metadata,
  reset both to zero, retain speed and paused/playing state, and resume together.
  Independent native loops are replaced by shared loop boundaries. Playback
  failure pauses both sides and offers Play. This is shared control, **not
  frame-accurate browser synchronization**.
- `gallery-corrections.patch`: review-only text + player patch against the
  committed gallery at333821f (unchanged in9d6aeca). **Do not apply blindly over
  newer live edits.** The owner changed the live page during this shift without
  a corresponding change on main at the time of `git pull --rebase`.
- `corrected_index.html`: complete proposed source for that older committed page.
- `preview.html`: same proposal with relative media paths into the existing
  gallery folder; no asset duplication. Open it from this checkout. Paths also
  work when serving the repository root on an already authorized local service.
- `player.js`: standalone replacement, also embedded in both HTML copies.

The label proposal attributes existing source numbers instead of implying that
the displayed derivatives or newly shipped CLI were benchmarked:

| Row | Suggested presentation |
| --- | --- |
| Pendulum | Provisional period transfer. Two scenes × two seeds at source t60: range1.1857–1.1870s; x1.7 control2.0175–2.0202s. Source plain0.833–0.843s has only one seed/scene. Real≈1.18s. Displayed proxy media is16 sampled frames at4fps; native continuous media/provenance pending. |
| Donor | Reconstruction is a real-video diagnostic, using later frames. Temporal tlo is an artifact. Unauthenticated transfer asset excluded from this proposal. #5608 leaves donor-clock transfer unresolved. |
| Stationary action | Replicated E2 stand-still control: rho0.222 [0.198,0.284], fresh-seed replication0.208 [0.177,0.258]. This is not better prediction of the recorded moving robot; LPIPS to real future is worse. E3 action contrast was negative. |
| Settle | Replicated #2720 comparison:5/6 vs0/6 on2 mid-fall inputs ×3 seeds. DOVER−0.004±0.007 belongs to these6 pairs, not the whole recipe. |
| Ball | Analytical proxy inputs only. Task266 generated-Nano result pending at review time. g is an input with an assumed scale, not a measured Nano improvement. |

Per-asset native scene/seed/sidecars are still needed for the old gallery clips.
Source numbers are linked in the proposed page. Board evidence: task278 #5792,
source #5440 and independent review #5473, source #2720 and task121's review,
artifact #5600 and two-tool correction #5608. No new physics finding is claimed.

## Actual checks

`live_check.json`, 2026-11-01 16:57:08UTC from nail:

- Gallery :8085 HTTP200; **24/24** referenced live media HTTP200.
- **24/24** media SHA256s match task279's full ffmpeg-decode-PASS assets. They
  were not decoded a second time because the bytes are identical.
- HTML had changed since the committed page;6 local evidence anchors were
  unresolved in that live snapshot. The earlier unavailable-listener blocker
  is resolved at this time.

`player_check.json`: **9 passed** deterministic Node mock media-event/control
checks, including paused and playing variant changes, load errors, rejected
autoplay, shared loop reset and restart recovery. The checked script equals the
embedded release script. These are not browser/codec tests.

Both proposed HTML copies have10 players,22 referenced assets that resolve
locally, and no broken local anchors. Both patches pass `git apply --check`
against the checked-out committed gallery. Original source hash is in
`source_sha256.txt`.

**Browser execution was unavailable:** `firefox --version` failed before startup
with a DBus transient-scope error (process2 treated as a kernel thread). No
browser screenshot, JS-in-browser execution, or autoplay/codec compatibility
pass is claimed. Owner should test the player in the presentation browser before
adopting it. No request for extra permissions or browser installation was made.

## Reproduce from repo root

```bash
python3 work/ro-sol1/t280/build_patch.py
node work/ro-sol1/t280/check_player.cjs
python3 work/ro-sol1/t280/check_live.py
git apply --check work/ro-sol1/t280/player-only.patch
git apply --check work/ro-sol1/t280/gallery-corrections.patch
```

`build_patch.py` reads the gallery source and writes only this work folder. It
fails if expected old text is absent; use the committed source333821f when
reproducing the full label proposal after the gallery has changed. The live
check is a new timestamped read, not a reproduction of historical availability.
No command above deploys the page or changes the gallery owner's files.

Prior-work speed check in task280 #5808: [ProxyUp](https://arxiv.org/abs/2607.03732)
methods/results separates proxy dynamics from rendering quality;
[GAUGE](https://arxiv.org/abs/2608.05948) uses calibrated motion and timing;
[Physics-IQ](https://arxiv.org/abs/2501.09038) matches input/FPS and separates
visual realism from physical correctness. These motivate truthful presentation;
their experiments were not rerun.
