# Offline presentation fallback — task 288

Download **offline.html** and open it in a browser. This single 914,827-byte file
contains both of Raj's task281 MP4s, unchanged from commit `a597e6f`. No server,
network, build step or adjacent asset folder is needed to play or seek.
The online source link is optional and only opens when clicked.

From an authenticated shared-repo checkout, use the committed file directly or
rebuild it with:

```sh
python3 work/ro-sol1/t288/build_offline.py
```

Open `work/ro-sol1/t288/offline.html` locally. From another directory with `gh`
authenticated to the private shared repo, download a copy with:

```sh
gh api 'repos/srirangam-r/cosmos-swarm/contents/work/ro-sol1/t288/offline.html?ref=main' \
  -H 'Accept: application/vnd.github.raw+json' > cosmos-demos-offline.html
```

Check the file against `manifest.json` when using a pinned artifact. This
version's HTML SHA256 is
`7178f28457dbfd15c61f1903eb202066f56896ce35a92216ff9899a7b0f325d2`.
GitHub's HTML source viewer does not run the page; save the raw file locally.

## Playback

Click Pendulum or Ball settling to select a demo. Playback starts paused.
Play/Pause, Restart, speed and full-screen buttons sit below the video; native
video controls include seeking. Switching pauses the previous video. Full screen
uses the entire card, keeping the qualification visible. Keyboard shortcuts work
when focus is outside a native interactive control: 1/2 select, Space plays or
pauses, R restarts, F enters/exits full screen.

The page keeps these qualifications beside the original burned-in captions:

- Both clips: demo, provisional; selected examples, no new measurement.
- Pendulum: the real recording's measured period was supplied to the simulated
  start. The original's two source period estimates are flagged `check`.
- Ball: the selected original seed3 includes a gross visual artifact; the change
  includes artifact removal as well as settling. The 0/6 versus5/6 source count
  is unblinded eye coding and does not establish the full NVIDIA scoreboard.

The source/claim audit remains task285. This wrapper does not recaption, crop,
re-encode, regenerate or scientifically validate the underlying MP4s.

## Actual verification

`browser_check.json`: **22 PASS, 0 FAIL**, no fatal error or uncaught page
exception, in installed Brave154 / Chromium154.0.8037.93. CDP used anonymous
pipes, no listening port. HTTP(S) and WS(S) requests were blocked; no external
page request occurred. Both embedded byte streams have the pinned SHA256 values
in `manifest.json`, both decode to93frames@24fps /3.875s, both seek to1s and
advance decoded frames. Actual end-to-start rollover, pause/restart, half speed,
full-screen caption card, selection/hidden-player pause, physical keyboard input
and390px layout all pass. Three actual browser screenshots are included.

Media's full-frame ffmpeg decode/timebase checks were already completed in
task286. This task verifies the embedded copies' exact hashes and browser
behavior. No other browser, presentation machine, human visual-quality score,
new physics metric, planted-case pass or NVIDIA score is claimed.

`first_browser_check.json` preserves a partial run:12 checks passed before the
runner reused a top-level `const` name in its second iteration. The runner was
corrected to scope those variables; it was not an application failure.

Reproduce the actual browser checks (Node and installed Brave required):

```sh
node work/ro-sol1/t288/browser_check.cjs
```

Set `DEMO_BROWSER` to a compatible installed Chromium executable if necessary.
Rerunning overwrites the report/screenshots and closes its browser. The builder
is deterministic and verifies source MP4 hashes before embedding.

`availability.json`: gallery :8085 and direct :8031/demos/ both returned HTTP200
from nail at17:11:15UTC. Gallery had refused connections at17:09:36UTC, following
the task28617:05–17:07 outage; owner was notified of recovery in267. This file is
a timestamped availability observation, not an uptime promise. No remote
service or gallery modification was made.

## Prior work

Methods read beyond abstracts before creation/claim (parent281 #5899; child288
#5913): [ProxyUp](https://arxiv.org/abs/2607.03732) §§4.2–4.5, masked inversion,
region noising and stochastic relaxation; [GAUGE](https://arxiv.org/abs/2608.05948)
§§3.1–3.3, calibrated trajectory/timebase;
[Physics-IQ](https://arxiv.org/abs/2501.09038) Metrics/Results, spatial/temporal
motion versus visual appearance. Reused those presentation distinctions and
task286's exact hashes. Published experiments were not rerun.
