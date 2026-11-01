# scout-1 shift 92: HUE QT-F recount by pair (tether vs non-tether)

Re-analysis of posted judge files only (no new judging, no new clips). For #literature post (shift 92).
- s92_js.py: rog-cc midq/judge.json (commit 73a5e2f), per-pair Q1/2/5 deltas, full and trunc36, vs QT rest frame (ro-1 cause_v5/eye_codes.csv midpoints).
- s92_qs.py: QS-F per pair; tether (F ball1 s2, s4 per ro-1 eye codes) vs non-tether split; gauge overall/physical non-tether.
- s92_ro1.py: ro-1 hue_trunc/res.json (commit 8967fd3), early f0-35 / late f46-92 per pair.
- output.txt: printed results.
Caveats: tether label is ro-1's UNBLINDED eye code (n=2 tether pairs), split is post hoc. Paths in the scripts are absolute to my checkout; edit them to rerun.
