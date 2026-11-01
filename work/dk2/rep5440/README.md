# rep5440: independent replication of finding #5440 (dk1, task 255 E2, zero-action drift on Bridge FD)
- Same 24 Bridge dev clips, same OWN/ZERO requests (checked equal to dk1's jobs.jsonl action-for-action), **fresh seeds 11-13**, CPU noise, q8 queue.
- `make_jobs.py` (own code) -> `jobs.jsonl` (144 jobs). `analyze.py` (own code, opencv Farneback + pixel drift; no LPIPS, no dk1 code), frozen before any clip existed. Decision rule in its docstring.
- Pre-data fix (before any rep5440 clip): known-answer tolerance for Farneback on identical frames 1e-6 -> 1e-3 (numerical floor 3e-4 px).
- Smoke test = same-clip cross-check: analyze.py run unchanged on dk1's seed 1-3 clips (E1 OWN from work/rog1/t255/clips, E2 ZERO from work/dk1/t255_e2/clips; seeds relabelled 1-3 -> 11-13). Output: `sameclips_s123_result.json`. rho_PD 0.223 [0.191, 0.267], rho_FM 0.045 [0.033, 0.058], S_zero/S_own 0.25, 24/24 clips each.
