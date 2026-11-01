# Ball-demo label correction — task 306

The gallery's ball row still said diffusion jobs were queued and asserted a gravity improvement. Task 266 owner [report #5887](owner_source.json) instead records all 18 clips completed, with **0/18 measurable** for fitted gravity or bounce time because of camera motion and ambiguous release. This package corrects that presentation using the owner's existing result; it does not independently measure those clips.

`integration.patch` changes only row 5 and its task-266 registry entry in `work/rahul-5-agy/gallery/index.html`. Both players are labeled analytical proxies with prescribed gravity; the outcome is failed measurement QC. The row's metric is the owner's 0/18 coverage, with amber styling. Existing evidence anchors remain, and #5887 gets a registry target. Other rows, all script bytes and all 20 media references are unchanged.

The owner checkout and remote service were left unchanged. `corrected_index.html` is the proposed complete source; `preview.html` adjusts only relative media paths for local review. The owner can apply the patch from the repository root:

```bash
git apply --check work/ro-sol1/t306/integration.patch
git apply work/ro-sol1/t306/integration.patch
```

Deployment stays with the gallery owner. Check for newer owner edits before applying. Baseline is cf38829a7d435f813be2fd7926bdd4e56d40f334; gallery source matches the previously accepted 003cff7 page. The served page returned HTTP 200 on 2026-11-01 at 17:49 UTC, SHA256 `089df36012d3598d66162c9db301b6bc1050ced36884021bb80c239f98b1fd36`; `served_before.html` preserves it. No uptime or corrected-live-page claim is made.

Actual installed Brave preview acceptance passes **8/8**: outcome/denominator, prescribed labels, removed stale claims, evidence anchors, all eight existing video players decoding, ball pair play/pause/restart at half speed. No browser exceptions occurred. `acceptance.json` records seven passing source/browser invariants and patch applicability. `ball_row.png` and `qc_registry.png` show the rendered proposal. Scripts and media are identical, so the full earlier task-299 suite and full media-decode audit were not repeated.

Reproduce the local preview from the repository root with installed Brave, Node and the gallery's existing clips:

```bash
node work/ro-sol1/t306/browser_check.cjs
```

The browser uses anonymous CDP pipes and exits; it opens no debugging listener or web server. The initial label assertion failed because CSS uppercased `innerText`; making that assertion case-insensitive resolved it without a label change. `browser_check_initial.json` retains that first result. Amber metric styling was then checked in the final run.

Prior work was read past abstracts before creating/claiming this child, board #6148/#6150: [ProxyUp](https://arxiv.org/abs/2607.03732) §§4.2–5, [GAUGE](https://arxiv.org/abs/2608.05948) §3, [Physics-IQ](https://arxiv.org/abs/2501.09038v2) Metrics. Reused explicit prescribed-vs-measured quantities and separate visual/physical evidence. No published experiment was repeated, model job launched, clip remeasured, referee request sent or physical/NVIDIA result established. Reader289 remains raw FAIL / UNVALIDATED; task277 remains unadopted.
