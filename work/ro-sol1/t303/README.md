# Task 303: actual native receipt replay and sigma selection guards

All four archived task 281 receipts contain the same normalized 35-step full grid as the shipped table. Two receipts have a matching executed suffix; two contain a 1,000-entry ascending training schedule in `sigmas_used`. This is a metadata inconsistency, not proof of which values the model executed.

| Existing receipt | Requested/returned start | Full grid | Recorded executed suffix |
| --- | --- | --- | --- |
| sp_k12_s1 | 12 / 0.97056 | exact match | 24 entries, exact match |
| sp_k12_s2 | 12 / 0.97056 | exact match | 1,000 entries, inconsistent |
| sp_k19_s1 | 19 / 0.89844 | exact match | 1,000 entries, inconsistent |
| sp_k19_s2 | 19 / 0.89844 | exact match | 17 entries, exact match |

The inconsistent arrays run from 0.01 to 157.40727. The exact unmodified raw JSON and supplied header bytes are retained in `receipts/`; JSON SHA256s match owner message 6094 / commit 4edc07a. Headers retain supplied CRLF bytes; they were not independently obtained over the network. The files identify different GPU instances 0–3 instances on `brev-bhu5qgfem`, UniPCMultistepScheduler and server.py revision 04e8e0de81. This snapshot does not authenticate a current q8 deployment or its BASE_SCHED configuration.

Actual Python runner replay retains all original grids, returned starts and arrays, including the inconsistencies. Empty summaries retain the native latent; conflicting summary sigmas are recorded without silently replacing it. The runner still returns normally for inconsistent metadata: extraction is not grid/start/suffix/deployment certification. Those acceptance gates remain with the executor.

## Concrete correction

Baseline `runner.py`/`cli.py` are exact 4edc07a bytes. A direct Python `sigma_to_step(float('nan'))` returned 0. Requests for sigma 0.9 at 20 or 1 inference steps reused a prefix of the 35-step grid. The queue CLI could emit invalid default step 14 for a 1-step request after generating a proxy.

The minimal client correction:

- Rejects nonfinite sigma and sigma selection for any step count other than 35, since only that grid is recorded.
- Resolves the start identically for CLI and remote Python calls, rejecting invalid integers/ranges before proxy building or HTTP.
- Preserves the 35-step default 14, sigma 0.9→19, sigma 0→34 and sigma 1→0; sigma overrides an explicit step.
- Allows valid explicit steps at other positive integer step counts, but records `nominal_sigma: null` rather than borrowing a 35-step value.
- Updates the current schedule reference to archived values and distinguishes that reference from historical benchmark claims.

No proxy mask, trajectory, source image, latent hook, sampling grid or historical result was modified. No receipt was corrected or replaced.

## Verification and reproduction

Run from repository root:

```bash
python3 work/ro-sol1/t303/check_runtime.py
python3 work/ro-sol1/t297/check_queue.py \
  --queue-client work/ro-sol1/t297/evidence/cosmos_queue_snapshot.py \
  --out /tmp/ro-sol1-t303-queue
```

Dependencies: Python 3.10+, requests, numpy and OpenCV. The 101 actual Python assertions pass; `acceptance.json` retains before/after selector behavior, actual CLI parser/stdout/stderr, native-file identities and per-receipt observations. CLI parser fixtures replace only proxy generation with a labeled mock; remote receipt tests intercept both HTTP methods and use synthetic response/upload bytes, never model output. Socket connections are blocked.

The separate unchanged task 297 harness exercises the actual CLI in child processes, renders both synthetic analytical proxies (93 frames each), fully decodes them, then invokes the real queue client serializer with local capture. All 36 assertions pass; two local captures, zero requests/submissions. `queue_regression/` preserves those logs, inputs, analytical proxies, serializer snapshot and source hashes. Its `source_commit` 9128ff5 is the checkout base before this uncommitted patch; the exact tested modified product-file hashes are in both reports. No dummy transport response is presented as an MP4 evidence artifact.

`availability.json`: at 17:42:57 UTC gallery :8085 and direct :8031/demos returned 200. Gallery HTML matches 299's accepted hash 089df360…; no browser/media retest or continuous-uptime assertion.

## Limits and next step

This is software/provenance evidence only. No endpoint request, Nano generation, GPU job, paid compute, referee submission or NVIDIA scoreboard evaluation was performed. No parent 277 adoption or validation: reader 289 retains its raw FAIL/UNVALIDATED verdict and human question 5939 remains unresolved. Existing raw data do not certify all executed schedules. The owner needs to explain or correct the inconsistent receipt recording using authorized source/existing logs and verify the actual endpoint identity/grid/start/suffix before dispatching a new frozen benchmark. This report does not infer a model sampling failure from a reporting inconsistency.

Prior work, read past abstracts before task creation, board message 6109: [Cosmos3](https://arxiv.org/abs/2606.02800) §4.2 defines normalized RF interpolation; [ProxyUp](https://arxiv.org/abs/2607.03732) §§4.3–5 aligns intermediate proxy/noise time and separates coherence (simulation motion rationality 0.52 vs SDEdit 0.28); [Physics-IQ v2](https://arxiv.org/abs/2501.09038v2) Metrics separates spatial motion, timing and appearance (best tested score 24.1%). Reused those distinctions, not their experiments. No new physical finding.

Whitespace checks pass for authored files. Exact archived baseline Python and raw CRLF headers retain their original whitespace and are excluded from that formatting check. All artifact bytes are bound in `SHA256SUMS.json`.
