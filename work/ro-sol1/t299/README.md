# Live gallery acceptance — task 299

The owner-deployed `003cff7` gallery passes the **same 32 browser checks** that recorded seven failures in task 293. This verifies the deployed presentation controls and links. No gallery source or remote service was changed in this task.

Gallery: http://sha-devel.tail0c526a.ts.net:8085/

| Evidence | Previous live f96be25 (293) | Live 003cff7 (299) |
| --- | --- | --- |
| Actual Brave acceptance | 25 PASS / 7 FAIL | **32 PASS / 0 FAIL** |
| Referenced assets, commit bytes and full decode | 20/20 | **20/20** |
| Missing internal anchor targets | 4 | **0** |
| Uncaught browser exceptions | 0 | **0** |

The seven resolved checks cover missing anchor targets, both featured Restart labels, both GIF control states and both hidden-MP4 restart guards. Existing paired-player pause, restart, speed and source-switch checks also pass. Both featured native MP4s advance and wrap through the end; both displayed GIFs change decoded pixels across 650 ms. These clips remain byte-identical to the owner commit, and the four featured MP4/GIF assets match Raj's original `a597e6f` bytes. Native MP4s are 93 frames at 24 fps, 3.875 seconds.

`delivery_check.json` records HTTP 200 at 2026-11-01 17:31:14 UTC and every media hash/probe/decode result. Served HTML SHA256 is `089df36012d3598d66162c9db301b6bc1050ced36884021bb80c239f98b1fd36`, byte-identical to `003cff7`. A second HTTP fetch after browser execution confirms the page is unchanged. `served_gallery.html` archives those exact bytes. `browser_check.json` and seven PNG screenshots preserve the actual HTTP-page execution. `acceptance.json` compares the previous and current results by the same check names and records GIF pixel differences.

`browser_check.cjs` is byte-identical to task 293's suite, SHA256 `0be30e2f40b9416370ccdc563fe088b8e3c4a97369cee870efae334bf30ac841`. The delivery checker changes only the owner pin and temporary directory prefix. Source checkout when executed: `b0a4f9d91df987ba6f1bc40b7befd0502bbc2aeb`. Browser: installed Brave / Chromium 154, headless with anonymous CDP pipes and default muted autoplay policy; no debugging listener or local web server. Browser and Node exited after the short run.

From the repository root:

```bash
python3 work/ro-sol1/t299/check_delivery.py
node work/ro-sol1/t299/browser_check.cjs
python3 work/ro-sol1/t299/verify_evidence.py
```

Requires Python with Pillow, Node, ffmpeg/ffprobe, git, private gallery access and installed `/opt/brave.com/brave/brave` (override with `DEMO_BROWSER`). The checks make read-only HTTP requests to the announced gallery. Future deployments may legitimately differ from the pinned bytes.

Scientific text and image overlays are preserved as served; this report does not certify their claims or their external evidence. Local anchor targets resolve to the gallery's own registry summaries. Presentation acceptance does not establish physical improvement, NVIDIA-score preservation, continuous uptime, presentation-machine compatibility or frame-accurate synchronization. No queue/referee submission or model generation was made. Task 289's raw referee FAIL / UNVALIDATED state remains unchanged; input/state/native runtime acceptance for 277 remains with its executor.

Prior work was refreshed past abstracts before creating/claiming this task and posted in board message 6057: [ProxyUp](https://arxiv.org/abs/2607.03732) §§4.2–5, [GAUGE](https://arxiv.org/abs/2608.05948) §3 and [Physics-IQ](https://arxiv.org/abs/2501.09038) Metrics. Reused source identity, actual timing and separation of display evidence from physical validation. No published experiment was repeated.
