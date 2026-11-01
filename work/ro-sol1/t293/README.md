# Deployed gallery integration check — task 293

The deployed `f96be25` page is reachable and its 20 referenced media files are intact. Actual Brave checks found seven integration failures. The owner-review patch passes the same 32 checks in a local preview. **The live gallery and service were not changed.**

## Evidence

- `delivery_check.json`: HTTP 200 at 2026-11-01 17:20:59 UTC; served HTML SHA256 `b639e275eb3373b517ab69b8607fbd1b9531633aa473d9a518f03b4a4d6eec76`, identical to `f96be25`. All 20 referenced MP4/WebM/GIF assets returned 200, matched the commit and fully decoded with `ffmpeg -xerror`.
- Both featured MP4s are 93 frames at 24 fps, 3.875 seconds. Their MP4/GIF files are byte-identical to Raj's `a597e6f` originals. GIFs remain sampled presentation alternatives; no conversion was performed here.
- `browser_check.json`: **25 PASS / 7 FAIL**, actual deployed HTTP page in installed Brave 154 / Chromium 154 using private CDP pipes. Both featured MP4s decode, advance and wrap through the end. All three diagnostic pairs play/pause/restart correctly, and the donor variant preserves paused/playing state and speed. No uncaught exception.
- Failures: four missing anchor targets (`#5634`, `#5666`, `#5718`, `#5785`) counted as one check; two Restart buttons retain `Play` while playing; both GIF modes leave MP4 controls enabled; pressing Play in either GIF mode starts the hidden MP4.
- `gif_animation.json` and paired screenshots show each visible GIF changes pixels across 650 ms. These are presentation animation checks, not physics measurements.
- `patched/browser_check.json`: **32 PASS / 0 FAIL**, same browser/control scenarios on `preview.html` with the same local media bytes. This is a local preview result, not evidence of owner deployment. Featured and diagnostic screenshots are included for both runs.

`served_gallery.html` preserves the original page, including its claims. `corrected_index.html` changes only featured controls and anchor aliases. Scientific labels/claims are unchanged and are **not certified by this report**; source audits 278/285 retain their qualifications. Resolving a link to a local registry summary does not independently validate its text or establish a working external evidence link. No model output, referee result, NVIDIA score, continuous uptime, presentation-machine compatibility or frame-accurate synchronization is claimed. The task 289 reader remains UNVALIDATED with raw referee FAIL; no submission was made here.

## Patch and reproduction

From the shared repository root:

```bash
python3 work/ro-sol1/t293/check_delivery.py
node work/ro-sol1/t293/browser_check.cjs
```

The deployed browser command exits 1 when the recorded integration failures remain. It needs Node and the installed browser at `/opt/brave.com/brave/brave` (override `DEMO_BROWSER`). Delivery checking needs Python, ffmpeg/ffprobe and access to the announced private gallery URL. It downloads only gallery assets, uses temporary local files and makes no board/referee/queue mutation.

To reconstruct and inspect the review patch:

```bash
python3 work/ro-sol1/t293/build_patch.py
git apply --check work/ro-sol1/t293/integration.patch
```

Open `work/ro-sol1/t293/preview.html` in a browser. For automated verification, set `DEMO_URL` to its absolute `file:///.../preview.html` URL and `DEMO_OUTPUT=work/ro-sol1/t293/patched`, then run the same browser script. The preview uses gallery media from the checkout. The builder pins `f96be25`; review context before applying to any newer owner page. It writes only this task's folder.

The small patch synchronizes featured labels with actual media events, catches rejected play promises, disables video controls during GIF display and guards against hidden MP4 restart. It adds aliases for the four existing registry summaries. It preserves media, paired-player code and scientific text. Owner adoption remains pending. The already delivered offline task 288 page is an independent fallback.

Prior-work methods/results refreshed before task creation/claim: [ProxyUp](https://arxiv.org/abs/2607.03732) §§4–5 (masked inversion/region noising/SFR; dynamics and quality separately), [GAUGE](https://arxiv.org/abs/2608.05948) §§3.1–3.3 (calibrated motion/time and matched initial conditions), [Physics-IQ](https://arxiv.org/abs/2501.09038) Metrics/Results (spatiotemporal motion vs visual appearance). Reused timing/provenance and presentation-vs-physics distinctions; no published experiment rerun.
