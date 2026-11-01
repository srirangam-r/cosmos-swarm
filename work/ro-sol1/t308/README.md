# Task 308: independent receipt snapshot acceptance

The task307 request-local snapshot correction is accepted for the CPU cases
tested here. **292/292 assertions pass.** This adds cases beyond the author's
scheduler-replacement test; it does not reuse the task307 test code.

| Case | Original handler | Corrected handler |
| --- | --- | --- |
| Eight serial pairs: plain/latent × list/NumPy sigmas × float/uint8 video | Own schedule | Identical complete sidecars, synthetic response bytes, headers, pipeline calls, encoder inputs and final state |
| Eight mutation pairs: plain/latent × list/NumPy × in-place mutation/deleted attribute | All eight lose own receipt | All eight retain own receipt |
| Four injected pipeline failures: plain/latent × before/after | HTTP500, cleanup and recovery | Same HTTP500, cleanup and recovery |

For the mutation cases, a request runs in a worker thread until its encoder is
entered. A second thread (the harness main thread) takes the same inference lock
and either mutates the *same* sigma list/array or deletes the sigma attribute.
The worker then resumes. This specifically tests eager value ownership, rather
than merely retaining a scheduler or tensor reference. The old handler is the
negative control. Synthetic response bytes remain identical across each pair.

For serial cases, comparison includes **every** sidecar field and response header,
with a fixed injected clock and revision label. Both float-frame conversion and
uint8-frame paths run. For injected inference failures, both versions release the
lock, reset busy/waiting state, exit their contexts, write no artifacts, return
the same HTTP500 detail, and successfully serve the next CPU request.

## Reproduce

From the repository root, with Python3.10+ and NumPy (tested2.2.6):

```bash
python3 work/ro-sol1/t308/check_handler.py
```

The script writes `acceptance.json`. Expected final line:

```json
{"assertions": 292, "pass": 292, "serial_pairs": 8, "mutation_pairs": 8, "failure_recovery_cases": 4}
```

The four tracebacks in `check.stderr` are the deliberately injected pipeline
failures, caught as HTTP500 by the unchanged handler error path.

## Source and scope

- Original source: task307's exact archived historical `server_before.py`, MD5
  `04e8e0de8148d5895fb8268d66afeedb`.
- Corrected source: `tools/cosmos_local/server.py` at
  `16dcfac8c101f0bc6e9dc90326fd3a9a4f29dc3b`; the actual source correction was
  authored in `96b8305d885ef05bd9c778e0a24fb5d9bee086f1`.
- Both complete source snapshots are retained under `source/`, with hashes in
  `acceptance.json` and `SHA256SUMS.json`. Their diff is only the request-local
  post-inference list snapshot and its sidecar use.
- The entire `sync` function is compiled from its AST. Only the route decorator
  is removed; a future-annotations import avoids loading annotation dependencies.
  Startup, imports and model loading are not executed. Pipeline, scheduler, noise,
  latent preparation, clock, response wrapper and encoder are CPU fakes. The
  latent branch uses no-reference synthetic initial state, not an uploaded proxy.
- All socket creation is blocked. There is no HTTP/ASGI server, torch runtime,
  GPU, queue submission, real encoding or service modification. The fake encoder
  writes explicitly invalid `SYNTHETIC-NOT-VIDEO` bytes only in a temporary
  directory, which is removed. No synthetic media is published as evidence.
- This review changes no product source. Operators retain deployment ownership.
  It does not authenticate a live server revision or show native sampling parity.
- The original inconsistent historical receipts remain untouched and uncertified:
  only2/4 suffixes match their expected native schedules. This test does not
  establish the historical cause or certify those two clips.
- No task277 adoption, reader289 planted PASS, physical improvement, or NVIDIA
  scoreboard result follows from these software checks.

## Prior work

Read methods/results before creating/claiming this task (board273/#6175):

- [Cosmos3](https://arxiv.org/abs/2606.02800), §4.2: normalized RF interpolation
  and conditioning. Reused the distinction between inference noise and recorded
  scheduler state.
- [ProxyUp](https://arxiv.org/abs/2607.03732), §§4.3–5: intermediate-time proxy
  noising plus SFR; simulation motion rationality0.52 versus SDEdit0.28. Reused
  exact starting-time identity and separate operational/dynamics claims.
- [RF-Solver](https://arxiv.org/abs/2411.04746), §§3.2/4.1–4.3: second-order RF
  integration with matched NFE; v1 video reconstruction MSE0.0206→0.0139.
  Reused source-matched numerical provenance. The published reconstruction
  experiment was not rerun.

The unresolved question addressed here is ownership of recorded server metadata
under mutation and cleanup, rather than a new sampler or physical intervention.
