# Task 338: background-quality demo readout

Open `index.html` locally. No server is required. Choose a DOVER branch, take and seed to inspect all saved factorial outcomes. Drawings are symbolic, not measured masks or video frames.

Measurements are dk2's provisional task 331 / finding #6767, frozen at `e36f89c`. This page packages existing results; it does not replicate scoring or validate physics. See [DEMO_READOUT.md](DEMO_READOUT.md).

Rebuild: `python3 work/ro-sol1/t338/build.py` from the repository root.
Browser checks: `node work/ro-sol1/t338/render.cjs` (uses installed Brave and anonymous CDP pipes, no listener).

`source_receipt.json` hashes all 13 exact source snapshots and 205 earlier demo files. `verification.json` covers packaging. `browser_render.json` records actual desktop/mobile interaction checks. `gallery_http.json` is separate HTTP availability evidence; this page is not deployed to the shared gallery.

The pinned source analysis uses 20,000 Monte Carlo take-bootstrap draws. Its README/board call the bootstrap exact; the discrepancy is disclosed without changing source bytes or intervals. Earlier demos and judged README/reports remain untouched.
