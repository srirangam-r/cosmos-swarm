# Task 307: independent native-receipt review and recording-race correction

The task303 client guards and its limited receipt conclusion are independently
accepted. All four original full grids and returned starts match; only two
recorded executed suffixes match. All four arrays survive a fresh intercepted
transport replay without normalization or silent repair.

A recording race is demonstrated in the **exact historical server source**:
`server_before.py` MD5 `04e8e0de8148d5895fb8268d66afeedb`, whose first ten
characters match all four receipt revisions. The handler releases its shared
inference lock, encodes the video, and then reads `pipe.scheduler.sigmas`.
Another request can replace that shared scheduler between lock release and
metadata capture. This is a source-level recording defect. Whether it caused
either historical inconsistent receipt remains unknown.

The shared `tools/cosmos_local/server.py` correction copies the post-call sigma
list immediately after inference, while the lock is held, and uses that local
list in the sidecar. Sampling, latent creation, scheduler construction and video
encoding are unchanged. No running service was changed or restarted.

## Independent checks

`check_independent.py` is new code; it does not invoke the task303 test harness.
The report contains **1,895 passing assertions**, including these grouped checks:

- 10,138 sigma targets agree with an exact `Decimal` distance oracle over the
  archived nonterminal grid (regular targets, grid values and adjacent-float
  midpoint cases). NaN, infinity, invalid types and out-of-domain sigma fail.
- All 1,830 valid explicit starts for step counts 1 through 60 are preserved;
  300 invalid starts and 59 unsupported sigma-selected grids are rejected.
  The default35-step start14 and sigma0.9-to19 behavior are preserved.
- Eight actual CLI subprocesses reject invalid sigma/step inputs with parser
  exit2 before reading an absent input or creating any proxy/output.
- Four unmodified archived receipts are replayed through the actual runner with
  intercepted HTTP. Raw native values, latent records and sigma arrays remain
  unchanged, including both inconsistent arrays. All actual sockets are blocked.
- The actual server `sync` function body is extracted by Python AST; only its
  routing decorator is omitted. Model, scheduler, latent preparation and codec
  are explicitly stubbed. Two CPU threads and events impose each ordering;
  no model, endpoint, torch runtime or real encoding is invoked.

| Controlled CPU ordering | Old handler | Corrected handler |
| --- | --- | --- |
| Serial request | Own suffix retained | Own suffix retained |
| A encodes while B holds a fresh scheduler | A records B's 1,000-entry fixture, 3/3 cases | A retains own suffix, 3/3 |
| A encodes while B holds its different suffix | A records B's suffix, 3/3 cases | A retains own suffix, 3/3 |

The three A/B start pairs are12/19,19/12,0/34. B's own receipt matches B's stub
execution in every case. These are deterministic software cases, not statistical
samples or physics measurements. The injected 1,000-entry state is copied from
the archived inconsistent receipt; this test does not authenticate the historical
constructor configuration. All temporary response/upload bytes are labeled
synthetic, are not valid videos, and are discarded.

## Reproduce

From repository root, with Python3.10+, NumPy2.2.6, requests2.32.5 and
opencv-python-headless4.12.0.88 (OpenCV is used by CLI imports):

```bash
python3 work/rahul-api-codex/t307/check_independent.py
```

`verification.json` binds tested source hashes, original receipt hashes, complete
interleaving event logs and before/after scheduler arrays, CLI stdout/stderr,
environment versions and each assertion. `source/runner.py` is the exact303
runner snapshot. `source/server_before.py` is the unmodified historical handler
source. `source/server_after.py` and `receipt_snapshot.patch` preserve the tested
correction. `SHA256SUMS.json` binds all artifact bytes except itself.
The exact archived runner retains its original trailing whitespace and is
excluded from authored-file whitespace checks.

## Prior work read before task creation and claim

Board notes6151/6153:

- [Cosmos3](https://arxiv.org/abs/2606.02800), June2026, §§4.2/6.3: normalized
  rectified-flow interpolation in[0,1]; production Nano audio-visual recipe uses
  50steps, guidance6 and shift10. This distinguishes the published recipe from
  this archived35-step grid. Reused normalized-domain and provenance distinctions.
- [ProxyUp](https://arxiv.org/abs/2607.03732), July2026, §§4.3–5: intermediate
  masked inversion, time-matched background noising and stochastic flow
  relaxation. Simulation motion rationality0.52 versus0.28 for SDEdit. Reused
  exact agreement between starting latent noise time and the sampling schedule.
- [RF-Solver](https://arxiv.org/abs/2411.04746), §§3.2/4.3: second-order ODE
  integration reduces reconstruction error; video MSE0.0206 to0.0134 at matched
  function evaluations. Reused the need to identify actual integration grids
  rather than infer them from a nominal scalar.

Those papers establish relevant methods elsewhere. The open deliverable here
was independent software acceptance and diagnosis of recording, not a repeated
physics-transfer experiment.

## Limits and handoff

The old two inconsistent receipts remain uncertified and are not edited. A
post-call snapshot is not an instrumented per-step execution trace. Operator
adoption, deployed revision/configuration checks, native grid/start/suffix
acceptance and benchmark controls remain separate. The race test does not prove
that Nano sampled with a wrong schedule or that this race caused the archived
arrays. Other shared-state concurrency behavior is outside this change.

No queue/GPU/endpoint/referee request, paid compute, Nano generation, media
measurement, NVIDIA-score evaluation or parent277 adoption occurred. Reader289's
raw FAIL/UNVALIDATED and human question5939 remain unchanged. No background job
or service was started.
