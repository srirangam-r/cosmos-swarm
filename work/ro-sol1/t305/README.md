# Task305: source-matched Nano-Phys demo documentation

Documentation correction only. The product change is limited to
`tools/nano_phys/README.md`; no renderer, runner, CLI, sampler, gallery, service
or historical result was changed. No model request or physical measurement
was performed.

The old README called the wrapper a replicated fix, assigned archived252
strength groups to new CLI step indices, claimed all-clean/flicker evidence,
and described ball improvement while the owner had already marked266 failed.
The corrected document retains the genuine historical prescribed-period
transfer and separates it from the wrapper's pending physical benchmark.

`source_summary.json` recomputes means, sample SDs and ranges from all16
reported `mp_T` rows in the unmodified archived `results_sp.json`. It retains
the `x17_t90` check-flagged row and reports the two one-seed plain controls
from `results_px.json`. The four source files here are byte-exact git blobs
at50409ebbc8b25c1a6ef0b22157c658247e6b2751; source paths, blob IDs and SHA256
are in that summary. This is arithmetic over reported results, not an
independent clip measurement or replication. Four scene×seed cells share
scenes and seeds; their sample SD is not a CI.

Task278 audit5792 and task266 owner messages5858/5880/5887 are archived in
`task278_source.json` and `task266_source.json`, with original author, IDs and
timestamps. Task266's0/18 measurable is attributed eye QC, not a validated
physics estimate or proof of failed transfer. The ball experiment generated
and fetched18 clips, but camera pan/zoom and release ambiguity prevented the
intended physical measurement. No new job or remeasurement was attempted.

Current native receipt limits are kept from303: full archived grids match4/4,
executed suffix metadata matches2/4. Reader289's raw FAIL/UNVALIDATED is kept;
human coverage question5939 remains unresolved at this documentation update.
The current278/266/277 statuses were read from the live board. Peer304 owns
independent rendered-pixel/compositing review and was not duplicated.
After the first documentation push, inbox6133 reported304 complete inb8f3a09:
raw boundary correction accepted, clean compositing rejected on the tested
fixtures. A linked disposition was added to the product README, without a
renderer change or duplicate experiment. This updates the evidence status;
it does not adopt the coarse proxy into277.

Documentation verification: recomputed every displayed table number from
the raw blobs with Python's `statistics.mean/stdev`, checked retained flags,
compared request settings, checked repository link destinations, and reviewed
the diff. No test suite was added for this documentation-only change.
`verification.json` records the actual checks and point-in-time HTTP status.

To independently reconstruct the displayed historical numbers from these
archived source rows (no network or model request):

```bash
python3 - <<'PY'
import json, statistics
from pathlib import Path
root = Path('work/ro-sol1/t305')
rows = json.loads((root / 'results_sp.json').read_text())
for group in ['phys_t60', 'phys_t90', 'x17_t60', 'x17_t90']:
    values = [r['mp_T'] for k, r in rows.items() if '_' + group + '_' in k]
    print(group, len(values), statistics.mean(values), statistics.stdev(values),
          min(values), max(values))
print('Flagged:', {k: r['mp_flag'] for k, r in rows.items() if r['mp_flag'] != 'ok'})
PY
```

Prior work read beyond abstracts before create/claim, parent273 #6129 and
child305 #6131: [ProxyUp](https://arxiv.org/abs/2607.03732) §§4.3–5 separates
masked dynamics transfer from coherence with stochastic relaxation;
[GAUGE](https://arxiv.org/abs/2608.05948) §§3.3/5.2 uses matched inputs and
calibrated trajectory measurements;
[Physics-IQ](https://arxiv.org/abs/2501.09038v2) Evaluation/Metrics separates
spatial motion, timing and visual realism. Reused their evidence distinctions,
not their experiments. The documentation gap is specific to this wrapper.
