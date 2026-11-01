# Gallery demo smoke check — task 279

At **2026-11-01 16:52:33 UTC**, the announced gallery at
`http://sha-devel.tail0c526a.ts.net:8085/` refused connections from the nail
host. The evidence server root and `/e6/report.md` at `board:8031` both
returned HTTP 200. Gallery owner `rahul-5-agy` was notified in task 267
(messages 5768, 5788 and 5790); native pendulum media was requested from
`ro-3` in task 252 (5791). No remote machine was accessed over SSH and no
service was modified.

The committed gallery assets are available and decodable, but the pendulum
row needs native continuous videos before its synchronized comparison can
be presented as motion evidence.

## Pinned evidence

- Repository snapshot: `333821f2cefb9e59ac36bfc2958f5784f79cc8ce`.
- Gallery: `work/rahul-5-agy/gallery/index.html`.
- [Raw HTTP/media report](smoke_333821f.json): hashes, probe output and exit
  codes for every asset; source hash identifies the exact HTML inspected.
- [Contact sheet](gallery_contact_sheet.jpg): one frame at one-third of each
  MP4's decoded frame count, labeled by filename. It is an inspection aid,
  not a physics measurement.

| Check | Actual result |
|---|---|
| Video players / media files including toggles | 10 players / 24 files (12 MP4, 12 WebM) |
| Missing referenced assets | 0 |
| Full decode with `ffmpeg -xerror` | 24/24 pass |
| MP4 video format | H.264, 416×240, yuv420p |
| WebM video format | VP9, 416×240; yuv420p or gbrp |
| Evidence links that target missing HTML IDs | `#5315`, `#5440`, `#2720`, `#5563` |
| Gallery HTTP | connection refused |
| Evidence server root and E6 report | HTTP 200 |

| Video group (both encodings) | Frames | Encoded FPS | Duration |
|---|---:|---:|---:|
| Plain pendulum | 93 | 24 | 3.875 s |
| Pendulum physical proxy | 16 | 4 | 4.000 s |
| Pendulum ×1.7 proxy | 16 | 4 | 4.000 s |
| Donor base / transfer / reconstruction | 93 each | 24 | 3.875 s each |
| Robot own action / zero action | 17 each | 5 | 3.400 s each |
| Bounce base / settle | 93 each | 24 | 3.875 s each |
| Ball g=4.90 / g=9.81 | 189 each | 24 | 7.875 s each |

The two pendulum proxy files display overlaid frame numbers and encode only
16 samples at 4 FPS, although the page labels them 24 FPS. Their original
sampling timebase is not documented in the gallery. The encoded loop
length differs from the baseline by 0.125 s; that is a metadata comparison,
not a browser drift measurement. Re-encoding those 16 frames at 24 FPS
would change playback speed and would not recover native motion.

## Owner handoff

1. Repair the announced listener on sha-devel and verify it from a second
   host. Shared services must bind to its Tailscale IP, port 8085. Keep the
   process/log in the owner's notebook.
2. Replace the sampled pendulum proxy files with native continuous
   generated clips and record source scene, arm, seed, original FPS,
   sidecar and any trim/encoding operation. Preserve original timebase.
3. Replace the four unresolved local evidence anchors with real source
   links. The current anchors do not navigate to board findings.
4. Label the task-266 ball row **proxy illustration; Nano result pending**
   or hide it until actual generation outputs are available. At inspection,
   task 266 explicitly reported no completed run (#5760). The filenames and
   displayed trajectory do not establish generated Nano gravity.
5. Apply the humans' evidence labels before the presentation (provisional,
   replicated, artifact or negative as applicable). The existing source/
   scientific-claim audit is task 278; this report does not duplicate it.

## Reproduce

From the repository root, on the pinned snapshot (or a later snapshot if
checking repairs):

```bash
python3 work/ro-sol1/t279/check_gallery.py \
  --out /tmp/gallery-smoke.json \
  --url http://sha-devel.tail0c526a.ts.net:8085/ \
  --url http://board.tail0c526a.ts.net:8031/
```

Requires Python 3, ffmpeg and ffprobe; the checker otherwise uses the
standard library. It parses media sources and toggle variants, verifies
local files, hashes each one, counts decoded frames, fully decodes the
video stream, checks local anchors and tests explicitly listed HTTP URLs.

This is an operational report. No browser executable was available, so
JavaScript controls, autoplay and browser playback were **not tested**.
No generated clip, physics parameter, planted-case result, NVIDIA score,
model improvement or independent replication is claimed. No GPU job,
background service or paid compute was started.

## Prior work (read methods/results)

- [ProxyUp](https://arxiv.org/abs/2607.03732), §§4–6: proxy dynamics and
  appearance quality require separate assessment; sim MR 0.52 vs 0.31.
- [GAUGE](https://arxiv.org/abs/2608.05948), §§3.3–4: matched conditioning,
  calibrated tracking, and separate equation-form/parameter checks.
- [Physics-IQ](https://arxiv.org/abs/2501.09038), evaluation protocol and
  metrics: matched FPS/conditioning and real continuation comparisons.

These motivate preserving playback time and separating availability from
scientific evidence; they do not establish any result about this gallery.
