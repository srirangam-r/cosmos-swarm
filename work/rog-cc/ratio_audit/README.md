# ratio_audit: how stable is "QT is 76.2x closer to real than F"?

Claim audited: agy-4 #2802 (task 123), now in D1 l.69, D2 l.388, D3 l.258/418, README.
Metric there: |mean(QT) - real| / |mean(F) - real|, 13 gauge HUE questions, 8 F/QT pairs
(5 ball1 + 3 ball2), real = ONE clip (real_ball1_dd32_93f) averaged over judge offsets 0 and 0.5.

`python3 ratio_audit.py ../../ro-1/hue_qt/res.json <midq/judge.json> --out ratio_audit.json`
(midq/judge.json = my independent task-113 re-run of the same 20 clips; commit 73a5e2f.)

Checks: pair bootstrap (B=20000, seed 0) of each distance and the ratio; real scored at a single
offset; ball1-only pairs; per-pair mean |gen_k - real| (scout-1 #2679 form); same on the re-run.
Output: ratio_audit.json (keys src:category:real_ref:pairs).
