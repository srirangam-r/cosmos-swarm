# Task 145 blind visual QC

After all 60 F/S2/Z2/S4/Z4 clips are fetched, run:

```sh
python3 work/codex-api-2/t145/blind_qc.py \
  --clips work/codex-api-2/t145/out --out work/codex-api-2/t145/blind
```

Each sheet is one paired scene/seed with randomized row labels and eight
sampled frames. The original-resolution clips have the same opaque IDs and
row letters under `blind/native`. The key is `blind/UNBLIND_key.json`; do not
open it until coding is recorded. The program refuses incomplete sets and
existing output directories. It makes hard links, so the input and output
must share a filesystem. Sheets alone cannot establish rest: inspect native
successive late frames for anything uncertain, and code only what is visible.

For each sheet and row record: whether the named object appears and moves at
all, whether it is visibly stationary over the late window, whether the
camera is stable, whether identity/position becomes ambiguous or leaves the
frame, and whether there are gross artifacts. Use `unclear` instead of
guessing; record the observed frames and notes. This qualitative check is not
a planted-validated rest metric and does not establish physical correctness.
Only after coding, open the key and compare each steered arm with its paired
equal-norm random control. Preserve raw codes, key and analysis with results.
