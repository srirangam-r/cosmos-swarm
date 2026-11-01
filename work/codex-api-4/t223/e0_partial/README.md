# Actual E0: available-q8 audit, incomplete cross-GPU handoff

Task 223, shift 16. This is a partial artifact audit and an exploratory control,
**not a replication of the cross-GPU claim #4786 or a physics finding**.

The E0 temporal-change distance, bootstrap and permutation code were frozen in
077a68c before any actual Program N results. Aggregate human report #4786 was
read this shift. Pair/device mapping and the six-member primary family were
fixed in board #4818 before opening per-clip records. That mapping therefore
was not blind to the aggregate report. No metric or frozen core was changed.

Only q8 jobs appear in the shared queue under owner `raj-noise`: CPU seeds
101–108 and CUDA seeds 101–104. These twelve original videos were downloaded
without new generation. The design-only queue snapshot excludes sidecar and
outcome fields; SHA256 is
`053e6db3fcb2e081558f74992dad76601b99750c53188189738daf6f02cc838c`.
No E1–E4 clips, scores, labels or rankings were inspected.

All twelve request/queue joins and native 832×480, 93-frame, 24-fps contracts
pass. Video and queue-record hashes, server clip IDs and actual endpoint labels
are in results.json. Two independent FFmpeg RGB decodes plus direct 4×4 block
area averaging reproduce the first two changes within 4.45e-16 of the frozen
OpenCV implementation. Those are software checks, not planted validation.

The three planned GPU pairs are q8→l40s, q8→a6k, l40s→a6k, for both devices.
All six tests remain **untested** because the l40s/a6k artifacts have not been
provided. Their displayed p-values are null; internal p=1 placeholders preserve
the full Holm family and do not accept any null hypothesis. No smaller complete
grid is substituted. Same-host repeat generations are also unavailable: a file
compared to itself gives zero but is explicitly not that repeat control.

The available exploratory control compares q8 CPU-noise vs CUDA-noise clips at
the same four seed integers. Matched distance is 1.35317 gray levels, versus
1.34698 for different integers (ratio 1.00459). Correspondence advantage is
−0.00619 gray levels, seed-bootstrap 95% [−0.17138, +0.16370]; exact one-sided
permutation p=.875 (24 permutations, n=4). 37/2000 bootstrap samples contain only
one distinct original seed and are undefined. These are descriptive intervals
for four seeds, not equivalence, proof of independent draws, or evidence about
cross-GPU portability. CPU-only different-seed q8 mean distance is 1.46029 gray
levels (56 ordered off-diagonal comparisons, **eight seed clusters**).

Queue sidecars retain requested `extra_params.noise`, not native execution
records. The audited queue source constructs them from request parameters and
selected HTTP response headers; it does not copy the server-native noise record.
Thus these sidecars alone cannot verify the executed generator or tensor hashes.
Original input bytes/hash, native sidecars, actual sampler/sigmas, checkpoint and
runtime revisions are still missing. Karras is the charter/source default; a
request's flow_shift=10 is not evidence that shift 10 was executed.

To fetch exactly these twelve completed artifacts through the announced shared
queue (no generation), run this from this directory:

```bash
python3 - <<'PY'
import json, urllib.request
from pathlib import Path
root = Path('clips'); root.mkdir(exist_ok=True)
design = json.loads(Path('q8_design_only.json').read_text())
for row in design['runs']:
    url = 'http://100.111.167.68:8030/jobs/' + row['id']
    for suffix, local in [('', '.queue.json'), ('/mp4', '.mp4')]:
        with urllib.request.urlopen(url + suffix, timeout=120) as response:
            (root / (row['name'] + local)).write_bytes(response.read())
PY
python3 audit_q8.py clips --out replay
```

Queue metadata formatting may differ on refetch; native video hashes identify
the data. For byte-identical published replay, retain the exact queue_records
objects and write each as `json.dumps(obj, indent=2) + '\n'` to its named
`.queue.json` file. Otherwise only queue-record file hashes may change. The
statistic depends on video bytes, not metadata formatting. Requires NumPy,
OpenCV and FFmpeg. Full distance matrices permit statistical replay without
redownloading videos; hashes and queue IDs support independent native decoding.

Next: obtain the owner's l40s/a6k design and native artifact handoff, authenticate
matching inputs/settings/runtime, and run the six registered comparisons using
the unchanged metric. No CPU seed-pairing permission across arbitrary endpoints
or NVIDIA scoreboard conclusion follows from this partial audit.
