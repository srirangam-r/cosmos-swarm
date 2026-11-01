# E7 donor-transfer gallery labels — task 313

Raj's [human report #6167](human_report.json) supersedes the gallery's awaited-E7b claim and universal flicker-free spatial-transfer language. This owner-review patch reports E7's partial donor-clock transfer with full planned denominators: spatial slo 8/16 clean and 6/16 within 10% of real; plain 4/16 clean and 0/16 within 10%. It preserves the 3-target, underpowered paired estimate f=0.93, CI [-2.2, 1.15], and the corrected temporal-donor result of 8/16 clean but 0/16 within 10%.

The displayed E6 videos remain historical illustrations, explicitly distinct from E7's benchmark grid. This package quotes the human report; it does not independently remeasure clips or establish a NVIDIA-scoreboard pass. Historical E6 ringing evidence remains linked. Other gallery rows, scripts, and media paths are preserved.

Only files under this task folder are published. The owner's gallery checkout and running service are unchanged. From the repository root, the owner can review/apply:

```bash
git apply --check work/ro-sol1/t313/integration.patch
git apply work/ro-sol1/t313/integration.patch
```

Check for newer owner edits before applying. The patch uses gallery source at ceb5a4e (SHA256 089df36012d3598d66162c9db301b6bc1050ced36884021bb80c239f98b1fd36). `corrected_index.html` is the proposed page; `preview.html` changes relative clip paths only. Task306's separate ball-QC label patch is still needed and is checked for compatibility in both orders.

Reproduce this source build and focused browser review from the repository root:

```bash
python3 work/ro-sol1/t313/build.py
node work/ro-sol1/t313/browser_check.cjs
```

The browser uses installed Brave through anonymous CDP pipes; no web server or debugging listener is started. Screenshots and raw browser observations are retained. This is local preview evidence, not deployed-page acceptance. The unchanged media and full earlier gallery suite are not re-audited.

Verification: seven source invariants pass; all ten actual Brave checks pass, including the historical-media labels, E7 counts and uncertainty, resolved anchors, donor-pair playback, diagnostic variant switching, and 390px layout. Both orders of the306/313 patches apply and produce identical combined HTML. Initial browser output retained in `browser_check_initial.json` has one assertion failure caused by CSS-uppercased label text; a case-insensitive assertion fixes that check without changing the page.

Prior work was read past abstracts before creating/claiming this child, board6206/6210: [FreeInit](https://arxiv.org/abs/2312.07537) §§4–5, [Phi-Noise](https://arxiv.org/abs/2605.24509) §§3–5, [ProxyUp](https://arxiv.org/abs/2607.03732) §§4.3–5. Reused separate motion-transfer, calibration, and visual-quality evidence. No model job, paid compute, queue/referee request, deployment, or physical result is part of this work. Reader289 remains raw FAIL / UNVALIDATED, and task277 remains unadopted.
