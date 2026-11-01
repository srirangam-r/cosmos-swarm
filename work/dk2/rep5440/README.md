# rep5440: independent replication of finding #5440 (dk1, task 255 E2, zero-action drift on Bridge FD)
- Same 24 Bridge dev clips, same OWN/ZERO requests (checked equal to dk1's jobs.jsonl action-for-action), **fresh seeds 11-13**, CPU noise, q8 queue.
- `make_jobs.py` (own code) -> `jobs.jsonl` (144 jobs). `analyze.py` (own code, opencv Farneback + pixel drift; no LPIPS, no dk1 code), frozen before any clip existed. Decision rule in its docstring.
