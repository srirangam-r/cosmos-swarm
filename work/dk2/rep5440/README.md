# rep5440: independent replication of finding #5440 (dk1, task 255 E2, zero-action drift on Bridge FD)
- Same 24 Bridge dev clips, same OWN/ZERO requests (checked equal to dk1's jobs.jsonl action-for-action), **fresh seeds 11-13**, CPU noise, q8 queue.
- `make_jobs.py` (own code) -> `jobs.jsonl` (144 jobs). `analyze.py` (own code, opencv Farneback + pixel drift; no LPIPS, no dk1 code), frozen before any clip existed. Decision rule in its docstring.
- Pre-data fix (before any rep5440 clip): known-answer tolerance for Farneback on identical frames 1e-6 -> 1e-3 (numerical floor 3e-4 px).
- Smoke test = same-clip cross-check: analyze.py run unchanged on dk1's seed 1-3 clips (E1 OWN from work/rog1/t255/clips, E2 ZERO from work/dk1/t255_e2/clips; seeds relabelled 1-3 -> 11-13). Output: `sameclips_s123_result.json`. rho_PD 0.223 [0.191, 0.267], rho_FM 0.045 [0.033, 0.058], S_zero/S_own 0.25, 24/24 clips each.

## Result (fresh seeds 11-13; analyze.py unchanged since 82798f6) -> `result.json`
- 144/144 clips on q8-0..7 (server rev 04e8e0de81), CPU noise, all sidecars in `clips/`.
- PRIMARY rho_PD = PD(zero)/PD(own): **0.208 [0.177, 0.258]**, 24/24 < 0.5 -> **replicated** (dk1 #5440: 0.222 [0.198, 0.284]).
- Optical-flow family rho_FM: **0.048 [0.041, 0.059]**, 24/24.
- Seed spread (pixel RMSE) S_zero/S_own: **0.213 [0.192, 0.258]**, 24/24 < 1, 23/24 < 0.5 (dk1 LPIPS ratio 0.15).
- OWN drift / real-video drift: 1.04 [0.99, 1.20] (dk1 1.10).
