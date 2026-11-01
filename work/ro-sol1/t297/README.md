# Shipped Nano-Phys queue serialization: runtime evidence

**36 checks PASS, 0 FAIL. No live queue submission or GPU run.**

Owner commit `ac8d086396d6d6f4d352130981d2a59ad8788782` adopted completed review291's patch5975. This report validates the shipped CLI at `003cff7d53df272e56ab6192129aa5db103ca156`; no product source changed here.

The actual Python CLI generated two synthetic-fixture proxies, one pendulum and one ball, each 93 frames at 832×480 and 24 fps. Every frame decoded with OpenCV. These fixtures exercise CLI generation and serialization; they are not task277 inputs or evidence of physical accuracy.

The same runs against pre-fix `0596dc1` reproduce all three reported defects for both physics paths: mixed stdout, absent `files`, and absolute `latent.ref`. Shipped code emits one JSONL record with status on stderr, attaches the generated proxy and references its basename.

The real `cosmos_queue.py.submit()` then consumed each emitted line, with its HTTP call replaced by a local capture and socket connections forbidden. The captures preserve exact image and proxy bytes, upload basename, multiline/Unicode captions, negative prompt, all eight sampling fields, CPU noise, explicit start index, owner and endpoint restriction. There were two local captures and zero network requests. Paths contain spaces as an additional integration check.

`--start-step 7` is an arbitrary serialization fixture. It does **not** select or certify sigma 0.9. This report does not validate the native sigma schedule (child295), remote execution, task277 state adoption, proxy masks/geometry, model outputs, planted readouts or NVIDIA scores. Reader289 retains its raw referee FAIL / UNVALIDATED status, pending human5939.

## Reproduce

From the shared repository root, with Python, NumPy, OpenCV and requests installed:

```bash
python3 work/ro-sol1/t297/check_queue.py \
  --queue-client work/ro-sol1/t297/evidence/cosmos_queue_snapshot.py \
  --out /tmp/ro-sol1-t297-replay
```

The baseline requires commit `0596dc1` in local git history. The included queue snapshot is the unchanged client read from the swarm checkout, SHA256 recorded in `evidence/result.json`. Nothing is submitted; never replace the test's local capture with a live call merely to reproduce this report.

`evidence/result.json` contains all 36 assertions, source hashes and media hashes. Each fixture folder contains raw before/after stdout and stderr, a payload summary with large base64 fields replaced by hashes, its synthetic input image and current proxy MP4. Raw stdout preserves the original execution paths; rerunning creates fresh paths.

Prior work was read before creation/claim (board6029/6031): [ProxyUp, methods and results](https://arxiv.org/abs/2607.03732) motivates exact proxy transfer; [GAUGE, §3.3](https://arxiv.org/abs/2608.05948) matches initial inputs; [Physics-IQ, metrics](https://arxiv.org/abs/2501.09038) separates temporal fidelity from appearance. This is operational validation, not a new physics finding.
