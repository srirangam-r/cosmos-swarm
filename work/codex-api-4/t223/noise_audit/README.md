# CPU-noise plumbing audit for Program N

**37 CPU software checks pass. Actual model execution remains unverified.**
This is an outcome-blind audit for task 223, following the arrival of
`tools/cosmos_local/noise.py` at commit
`e5c7b3b8f9996417a59aeb93099d9265a71428fb`. No `raj-noise` clips, scores,
rankings, or experiment manifests were opened. It changes no running service,
shared tool, protocol estimand, or Deliverable 1–3 file.

The source implements plain `noise.device=cpu` by constructing a CPU
`torch.Generator` and passing it into `pipe(**call)`. The mixing context is
intentionally a no-op when `mix` is absent. `noise.mixed=false` therefore
describes a successful plain CPU request in the replay; it does not indicate
that CPU noise failed. The exact route's sidecar records `noise.spec` and
`noise.mixed`, plus a top-level Torch version. It contains no sampled tensor
hash, shape, dtype, or random-draw identifier in `noise`.

`audit.py` compiles `sync` from the pinned, unmodified server source snapshot.
It removes decorators, annotations and defaults, then explicitly supplies every
argument. The function body, lock handling, noise-generator handoff, and
sidecar construction are unchanged. A fake scheduler, fake pipeline, fake
encoder, and response object replace GPU/model/codec/network work. The fake
pipeline uses real Torch CPU random draws. Its random helper is explicitly
**a test double, not the Diffusers helper**. Source hashes and the compiled AST
hash are retained in `verification.json`.

Checks cover the source route's CPU-generator device and seed, independent
direct Torch reference draws, fresh-generator repetition, different-seed and
advanced-stream controls, dtype/shape/byte-packing conditions, the plain and
mixed sidecar flags, all-of-B mixing, unmodified subsequent draws, invalid
device rejection, and cleanup after a manufactured pipeline failure. The
same initial generator state followed by a different preceding random call
gives a different later sample in the replay. Seed and device declarations
alone therefore cannot identify an arbitrary later random draw.

The byte hash preserves bfloat16 storage without conversion to float32.
Its interpretation also requires shape, dtype, packing, and byte order: a
reshape can preserve every byte while changing the tensor's dimensions.

## What this resolves for E0

The published code supports the intended CPU-generator handoff. A request or
`mixed` flag alone cannot establish actual cross-GPU sampled-tensor equality.
That is an evidence limitation, not a reported server malfunction. E0 can
still measure same-seed clip correspondence, retaining its requested-CPU and
unverified-runtime qualifications. A correspondence p-value does not prove
noise identity, pipeline equivalence, physical correctness, or an improvement.

For a live verification, preserve a runtime record tied to each generated
artifact: actual generator device; draw identifier/callsite and sequence;
generator state before that draw; sampled tensor shape/dtype and exact-byte
hash (with packing/byte order); pipeline/helper source revision; and Torch
version. Log the initial video-noise draw and any independently sampled VAE
noise separately. A native record of the values actually used or an existing
published live sentinel can satisfy the protocol's execution check. Do not
relabel a requested setting as an observed runtime value. Keep checkpoint,
sampler/sigma sequence, and host-stack comparisons separate from noise
identity. No live logging patch is installed or proposed as already deployed.

This audit does **not** test the stated explanation involving CUDA SM counts,
the real Diffusers CPU-to-CUDA path, VAE sampling, cross-machine equality,
cross-version CPU RNG stability, or any model output. There is no planted-case
submission, physical estimate, generated Cosmos clip, or NVIDIA-score claim.
The owner-supplied factor grid and native runtime records are still pending.

## Reproduce

The pinned source files make the check independent of later shared-tool edits.
Run with Python 3.10.12, CPU Torch 2.14.1+cpu and NumPy 1.26.4:

```bash
python3 -m venv /tmp/t223-own-noise-env
/tmp/t223-own-noise-env/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch==2.14.1+cpu
/tmp/t223-own-noise-env/bin/pip install numpy==1.26.4
/tmp/t223-own-noise-env/bin/python work/codex-api-4/t223/noise_audit/audit.py --out /tmp/t223-own-noise-replay.json
cmp work/codex-api-4/t223/noise_audit/verification.json /tmp/t223-own-noise-replay.json
```

The recorded report is deterministic in the tested environment. Other Python,
Torch, or NumPy versions change the version fields; exact numerical draw
identity across those versions is not asserted. No model weights, CUDA calls,
network listener, remote machine, or actual experiment output are needed.
