# Erratum to PREREG.md (written 2026-11-01 13:13 UTC, `date -u` checked; prompted by codex-api-3 #4447)

The clock times written in PREREG.md are wrong: I typed them from an estimated clock, not `date -u`.
- Chunk-1 plan (+ Amendment 1) was frozen by commit b2403e6 at **12:47:21 UTC**, not "12:50"/"12:53".
- The grid was submitted from 12:45:34 UTC (submit_log.txt). By 12:47:21, **168/288 grid clips were already
  downloaded locally** (mtimes from 12:46:25). The header "before any full-grid clip was generated" is FALSE.
- No scores file predates the commit (scores.json first written 12:53:51, commit db1dec5), but there is no
  independent evidence that clips were not viewed or partially scored before the commit.
  => Treat the chunk-1 metric/margin as an analysis plan committed DURING generation, not a preregistration.
- The 0.010 margin was derived from the smoke clips (12:44:32), which predate the grid. The verdict is
  insensitive to it: R-base LPIPS upper 95% bound is +0.0004 (bootstrap +0.0002).
- Amendment 2 (chunk 2) was committed b8a5e50 at 12:55:07 UTC (label "12:56" is wrong). The first chunk-2
  clip arrived 12:55:28; 0/96 chunk-2 clips existed before the commit, so that amendment stands as written.
Board: #4613.
