# Published demo delivery check — task 286

Raj's four task281 files are intact, decode fully, and play in installed Brave.
Download the MP4s before presenting if seeking is needed. The identical local
copies seek correctly; the HTTP copies reset to frame0 when seeking to1s.
Gallery :8085 refused connections again from nail; owner notified in267 #5882.
Direct [:8031/demos/](http://board.tail0c526a.ts.net:8031/demos/) remained available.

Scope: delivery, media timebase, and actual browser behavior. Source/claim review
is rahul-4-codex-sha-devel's task285. No model generation, physics measurement,
planted submission, NVIDIA-score verification, service edit, or gallery edit.

## Evidence

- `delivery_check.json`: 4/4 HTTP200; SHA256 equal pinned shared-repo commit
  `a597e6f`; 4/4 full ffmpeg `-xerror` decode passes. Both MP4s are H.264 yuv420p,
  93frames at24fps, duration3.875s, first/last samples0/3.833333s. Both GIFs have
  47 distinct frames, infinite-loop metadata, 80/90ms frame durations approximating
  12fps, duration3.910s (35ms longer than MP4). Maximum cumulative deviation
  from a12fps grid is3.333ms. GIF is a sampled presentation derivative.
- `browser_check.json`: 12PASS /2FAIL, no uncaught exception/fatal error.
  Brave154 / Chromium154.0.8037.93, headless, anonymous CDP pipe, no listener,
  no autoplay-policy override. Both direct HTTP MP4s decode, advance decoded
  frames and loop through a real end-to-start rollover. Both GIFs decode and
  visibly animate. The two failures are direct HTTP MP4 seek-to1s: `currentTime`
  resets0 and `seekable=[0,0]`, even with the full3.875s buffered. The same local
  files (SHA256 recorded in browser report) seek-to1s correctly.
- Server responds200/full file to Range requests, with Python SimpleHTTP/0.6,
  Content-Length and moov before mdat. Together with the local comparison, this
  points to HTTP delivery as the seek limitation; no remote change attempted.
- `*_http_mp4.png`: browser screenshots after playing through1s then pausing;
  `*_local_mp4.png`: same file sought to1s locally. Native browser controls
  partially overlay the demo footer in these MP4 screenshots.
- `*_gif_a.png` / `*_gif_b.png`: direct GIF screenshots700ms apart.
  `gif_pixel_changes.json` binds their hashes and checks changed decoded pixels.
  `demo_index.png` and `gallery_recheck.png` preserve actual HTTP-page state.
- `served_demos.html`: server's directory listing with all four links.
  `first_delivery_check.json` preserves the first observation (header casing
  corrected in the final checker). The final report is the current evidence.

Gallery connection refusal was observed by Python, curl and Brave at17:05–17:07UTC,
after task283's17:03UTC gallery pass. It is an availability regression; this
report does not establish the service's state at any later time.

## Reproduce

From a cosmos-swarm checkout containing `work/raj-demos`:

```sh
python3 work/ro-sol1/t286/check_delivery.py
node work/ro-sol1/t286/browser_check.cjs
python3 work/ro-sol1/t286/check_screenshots.py
```

Requires Python/Pillow, ffmpeg/ffprobe, Node and installed Brave at
`/opt/brave.com/brave/brave` (or set `DEMO_BROWSER`). The browser checker exits1
while either HTTP seek failure remains. It runs for about20s and closes its
browser. Reports are observations of live services; reruns overwrite them.
Use an exact checkout of a597e6f for the local comparison if demo sources change.

Presentation download commands (run in your chosen demo directory):

```sh
curl --fail --output pendulum_physics_start.mp4 http://board.tail0c526a.ts.net:8031/demos/pendulum_physics_start.mp4
curl --fail --output ball_settle.mp4 http://board.tail0c526a.ts.net:8031/demos/ball_settle.mp4
```

Expected SHA256:

```text
fd724670aab40fd348fe5dfcd11e7996a62a13cb96b0fb9ec1a302d12cb84e99  pendulum_physics_start.mp4
6ba3af0a67bf3d3ee5497e22bdbfac6a58eaac2d88ad95aadce3e31df962ea86  ball_settle.mp4
```

The full four-file hashes are in delivery_check.json. For captions, preserve
Raj's demo/provisional qualification and285's source review. In particular,
do not present the ball's visible baseline artifact as only a timing error or
claim that the pendulum's supplied proxy period was independently predicted.

## Prior work

Refreshed methods/results before claiming: [ProxyUp](https://arxiv.org/abs/2607.03732)
§§4–5, [GAUGE](https://arxiv.org/abs/2608.05948) §§3.1–3.3, and
[Physics-IQ](https://arxiv.org/abs/2501.09038) Metrics/Results. Task286 note5878
records the reuse: explicit temporal fidelity and separation of display quality
from physical correctness. No published experiment was rerun.
