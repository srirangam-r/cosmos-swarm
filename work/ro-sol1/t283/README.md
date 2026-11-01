# Task283: actual browser playback and source-error recovery

**14/14 browser checks passed**, 2026-11-01 17:03 UTC, using installed Brave
154.1.96.60 (CDP reports Chrome154.0.8037.93), headless on nail. No autoplay
policy override was used. An isolated temporary profile and anonymous CDP
pipes avoid a debugging listener or a new web service. This closes280's
browser-execution gap; it does not validate model physics or NVIDIA scores.

## Review contribution

Use **this `player-only.patch` instead of280's version**. It preserves the
gallery owner's d466e17 labels and adds280's shared controls plus the fix below.
`source-error-delta.patch` is the smaller delta if280's player was already adopted.
The live gallery and its service were not modified.

The initial real-browser run of280 exposed a failure that its9 mocked checks
missed: when both variant `<source>` URLs fail, source errors do not bubble to
the video listener. `pair.loading` stayed true with `networkState=3`, blocking
both controls and subsequent variant changes. `before_browser_check.json`
preserves that actual failure (9 pass,1 fail).

The revised player captures source-node errors and waits for **both formats**
to fail before clearing loading and pausing the pair. It also bounds a stalled
load at15 seconds. The actual browser verifies successful recovery to a valid
variant and verifies that a missing MP4 still falls back to a valid WebM.
The15-second stalled-network branch was not directly exercised.

## Evidence

- `browser_check.json`:14 passing checks, no uncaught page exceptions. The10
  preview players decode and advance actual browser video frames. Real pause,
  paused/playing variant changes,0.5× speed, restart and a genuine `ended`
  event pass. These are shared controls, not a frame-accurate synchronization
  guarantee.
- All24 original gallery MP4/WebM sources reach `loadeddata` with decoded
  dimensions, including the gbrp pendulum WebM. Their SHA256s are recorded.
  This is initial-frame browser decode;279 already fully decoded the same
  files with ffmpeg. No Safari/Firefox or presentation-machine pass is claimed.
- Live :8085:10/10 players decode; all five pairs autoplay when scrolled into
  view. Chromium pauses native muted autoplay outside the viewport on the
  HTTP page. The earlier overly strict all-offscreen-autoplay observation is
  retained in `pre_scroll_browser_check.json`; it is not a presentation blocker.
- `pendulum_preview.png` is the revised local review preview;
  `live_pendulum.png` is the unchanged live gallery at the check time. Remaining
  source-label/4fps sampled-media issues are described in280; Raj's281 native
  replacement media is separate and was not regenerated or fetched here.

## Reproduce from the repository root

```bash
python3 work/ro-sol1/t283/build_patch.py
git apply --check work/ro-sol1/t283/player-only.patch
node work/ro-sol1/t283/browser_check.cjs
```

Requires Node22+, the existing gallery assets, and Brave at
`/opt/brave.com/brave/brave`; `DEMO_BROWSER` can select another Chromium binary.
The runner opens local files, then reads the live gallery. It exits the browser
afterward. It does not deploy anything. The process runs with `--no-sandbox`
inside the Codex filesystem sandbox. Browser stderr is preserved separately;
its readonly-profile/DBus warnings did not prevent playback.

`build_patch.py` pins owner source d466e17 and inherits280's archived label
proposal for the local preview. Recheck patch applicability after owner edits.
Prior-work refresh: parent280 #5842 and this task's description/#5843:
[ProxyUp](https://arxiv.org/abs/2607.03732),
[GAUGE](https://arxiv.org/abs/2608.05948),
[Physics-IQ](https://arxiv.org/abs/2501.09038), methods/results read this shift.
