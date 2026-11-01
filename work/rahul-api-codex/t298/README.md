# Task 298: task277's fixed 18-slot paired report

This is analysis software, not a Nano result or a measuring tool. It implements
the already frozen board contracts 5745, 5770 and 5833. It opens no videos,
submits no jobs and never contacts the referee. Python 3.8+; standard library.

**Current state:** no task277 clips were supplied. The crossing reader's exact
task289 raw response is `verdict: fail`, despite `pass_rate: 1.0`. It remains
UNVALIDATED. The two established readers' validation records are deliberately
unconfigured here; this does not assert they failed their own checks.

## Run

From this folder:

```bash
python3 -m unittest -v test_paired_report.py
python3 write_examples.py
python3 paired_report.py observations_template.json --validation current_validation.json --out current_no_clips_report.json
python3 paired_report.py examples/synthetic_observations.json --validation examples/validation.json --out examples/synthetic_report.json
```

The examples' periods, strips, hashes and PASS documents are **synthetic** and
have `synthetic://` evidence addresses. They cannot demonstrate planted PASS,
rendering correctness or model performance. Changing the observation kind to
`measured` with the synthetic registry is rejected. Relabeling its registry
does not promote its explicitly synthetic response documents.

## Frozen quantities and gates

- Exactly `real06`, `real14` × seeds `101`, `102`, `103` × arms `plain`, `proxy`,
  `wrong`: 18 planned clip slots. Missing clips stay in the denominator;
  duplicate slots, extra slots and mismatched job IDs raise an error.
- Supplied proxy periods: 1.186 s and 2.0162 s, a 1.7 ratio. These are
  interventions, not either scene's independently measured physical period.
- Each clip requires successful `crossing`, `measure_pend` and `pend_acf`;
  finite positive periods; maximum/minimum period ≤1.1; finite raw-luma flicker
  in `[0, .08)`; an approved single-bob/rod strip with reviewer/evidence; clip
  identity/evidence; and exact approved tool method/source-hash identity.
- Crossing additionally requires `reason: measurable_unvalidated`.
  `candidate_period_s` and row-level `validated` flags are never promoted.
- Technical cleanliness and method validation are counted separately. The
  report retains raw readings and reasons, even when acceptance fails.
- All six same-scene/same-seed proxy/wrong pairs must pass before any aggregate
  interval is produced. A missing plain clip does not discard a guided pair;
  its matched plain comparisons remain unavailable and its slot stays missing.

For each reader separately, the report estimates the geometric mean of the six
`P_wrong/P_proxy` ratios. It enumerates all 27 ordered seed resamples within
each fixed scene and their 729 Cartesian combinations, drawing each guided
pair together. Percentiles interpolate at `q*(729-1)`. The interval describes
seed spread conditional on these two selected scenes. It is not uncertainty
over new scenes, tracking error, overlapping crossing intervals or real-world
physical constants. The sorted resamples are saved for audit.

The report separately retains per-seed wrong-minus-proxy differences, matched
plain differences/ratios, per-scene/arm seed mean and sample SD (only with all
three seeds accepted), and calibration to each prescribed period. A correct
1.7 response can coexist with twice-wrong absolute periods; the tests include
this counterexample. No success threshold or improvement verdict is invented.

## Observation schema

`observations_template.json` intentionally has no rows. Populate it with
**blinded, normalized reader outputs**, using this shape for each planned slot:

```json
{
  "id": "t277_real06_proxy_s101",
  "scene": "real06",
  "seed": 101,
  "arm": "proxy",
  "clip_sha256": "<actual 64-character lowercase SHA256>",
  "evidence_url": "<immutable clip/sidecar link>",
  "flicker": 0.005,
  "strip": {
    "single_bob_rod": true,
    "reviewed_by": "<actual reviewer>",
    "evidence_url": "<immutable inspected strip>"
  },
  "tools": {
    "crossing": {
      "status": "ok",
      "period_s": 1.2,
      "reason": "measurable_unvalidated",
      "method": "<exact referee method identifier>",
      "source_sha256": "<actual source hash>"
    },
    "measure_pend": {
      "status": "ok",
      "period_s": 1.2,
      "method": "<exact referee method identifier>",
      "source_sha256": "<actual source hash>"
    },
    "pend_acf": {
      "status": "ok",
      "period_s": 1.2,
      "method": "<exact referee method identifier>",
      "source_sha256": "<actual source hash>"
    }
  }
}
```

The values above are illustrative, not measurements or submission-ready data.
Keep failures as rows with failed tool statuses/reasons, or missing slots if a
clip was never produced. All incoming row fields are preserved in `raw`.
`periods_s` contains only identity-matching successful tool readings and must
not be read as validated acceptance without checking the slot's `accepted`.

## Validation evidence and trust boundary

A separate registry uses schema `t298-validation-v1`, kind `referee`, and three
`tools` entries. Each entry includes the exact `method`, `source_sha256`,
`referee_response_path` (relative to the registry),
`referee_response_sha256` (hash of exact raw bytes), and `evidence_url` for the
actual referee record. Missing/mismatched evidence fails closed. Only a raw
`verdict` of `pass` or `PASS` can pass; a favorable numeric rate, method name,
matching hash or self-declared row flag cannot override a FAIL.

This is evidence binding, **not referee authentication**. An executor/reviewer
must check the registry against the real board/referee record and verify the
source and media identities. A forged local PASS document is not proof. This
program neither manufactures approval nor decides the pending human question
5939. It does not change or probe the referee.

Before using any output as research evidence, the parent executor must also
resolve its separate input/state, builder/frame0/mask/codec and native-sigma
sidecar gates. Those checks are outside this analysis module. NVIDIA's DOVER,
motion fidelity, plausibility and robot-prediction scores remain unmeasured.

## Verification and prior work

The tests independently reproduce the 729-point bootstrap using 100 pairs of
count vectors weighted by multinomial multiplicities. They also check selective
coverage, missing guided/plain clips, individual reader failures, candidate
periods, exact flicker/agreement boundaries, method mismatches, raw FAIL with a
perfect pass rate, the actual task289 FAIL response, tampered evidence, plain
seed dispersion, mislabeled synthetic evidence, and the CLI's hash recording.

Prior-work note 6033 preceded task creation/claim; methods/results were checked
again during this shift:

- [ProxyUp](https://arxiv.org/abs/2607.03732), §§4–5: region-wise inverted proxy
  noising and stochastic flow relaxation preserve prescribed dynamics while
  measuring appearance separately (simulation motion rationality .52 versus
  SDEdit .28). This motivates separating transfer from visual quality.
- [PhysWeep](https://arxiv.org/abs/2609.06207), §§4–6: reports trackability,
  parameter bias and seed dispersion separately with paired bootstrap. This
  motivates paired seed units and explicit failed coverage. Its thresholds and
  larger seed counts do not replace task277's frozen protocol.
- [Physics-IQ Verified](https://arxiv.org/abs/2606.18943), §3.2/Appendix E.3:
  sample-level weighting and artifact audit change rankings (Kendall tau .46).
  This motivates equal planned-slot accounting and explicit artifact gates.

The open deliverable is a faithful executable of task277's existing summary
contract, not a rerun of any published dynamics-transfer experiment.
