# Actual E3: outcome-blind handoff, no model result

Prepared during task223 shift20 before any actual E3 output/status/clip access.
**Not executed on actual clips.** At14:09 UTC human #5084 declared Program N
complete and redirected effort toward fixes with prior-work notes (charter25).
We preserved this bounded registry/code handoff and did not launch preparation,
period analysis, model generation, a GPU job or a service. Actual E3 analysis
remains unperformed; do not report a seed-bank effect from this package.

[PREREG.md](PREREG.md), initially fixed in board #5072, nominates pend10 TRAIN
and pend11/14 HELDOUT,24 seeds601–624,top/bottom6,ascending-seed ties. The
72 queue request rows belong to raj-noise-f/g (36each). Snapshot has63 assigned
q8 endpoints and9 unassigned; statuses/outcomes/sidecars were discarded before
any inspection. Design SHA256:
`b450191c60e47e7b54fecd411dd117e75546d892f36d72c443da1147c74197c5`.
`owner_E3.jsonl.json` is a JSON array copied exactly from the two owner files;
original source-file hashes are recorded. No input-image bytes are present.

Joint success requires recognizable single rigid apparatus, fixed pivot,
back-and-forth swing, and an `ok` unchanged planted-PASS period within20% of
the real reference. Definite native failure is a provisional0; ambiguous QC,
fit-check, missing artifact and invalid native contract stay unresolved. All72
known joint scores are required. There is no complete-case substitute, static
clip reward, alternate split or held-out tie selection. Native QC and the
composite are **unvalidated**; software tests do not repair that limitation.
Only2 held-out inputs share one apparatus/camera, so input-resampling intervals
would be descriptive/underpowered. No NVIDIA scoreboard has been run.

Real references were computed without any E3 artifact from unchanged task8
mocap traces over nominal93-frame windows: start93 forpend10,81 forpend11/14;
real25Hz and model24Hz are distinct. Crossing periods are1.173550187,
1.176302428,1.174375575s respectively. `references.json` retains cycles,
turning-point checks and±1-real-frame sensitivity. Owner input-byte identity is
unverified. `frozen_source_verification.json` checks9 protocol/core/tool/reference
files/traces against published baselines. No source or existing result was edited.

Verification, from repository root:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 work/codex-api-4/t223/e3_seedbank/test_score.py
cd work/codex-api-4/t223/e3_seedbank
sha256sum -c SHA256SUMS
```

Eleven manufactured tests pass: gate composition, unknown/contract preservation,
training-only selection even when held-out outcomes reverse, fixed ties/static
controls, independent exact random-bank calculations including all134596 size6
banks for24 candidates, and lossless native decoder fps/framecount checks.
The test run issues the environment's existing SciPy/NumPy compatibility warning;
no actual nonlinear period fits were run in this shift. Actual queue/video/fit
integration remains untested. Existing period-tool planted pass is inherited
from byte-identical2e26463, not a new referee submission.

If a later scientific question justifies resuming, first satisfy charter25's
three-paper prior-work note, check that the question is not already answered,
and claim the task. Preserve this72-ID snapshot and split. For CPU preparation:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 work/codex-api-4/t223/e3_seedbank/prepare.py /tmp/e3-review
```

That fetches only the existing72 IDs, hashes native clips, constructs shuffled
opaque panels, and saves opaque period fits. It never generates a model clip.
Use`--frozen` to reuse its saved operational queue snapshot rather than refresh.
For a job expected to exceed5minutes, use nohup and record its PID/log before
ending the shift. **Do not open key.json or fits/ until native panel QC codes
have been committed/tagged and their hash posted.** Partial scene recognition is
unavoidable and must be disclosed. Additional native consecutive-frame panels
may be made for ambiguity, without period/seed-key access.

Once a complete72-entry QC JSON keyed byQ001...Q072 is frozen (each entry has
the five Y/N/U fields fromPREREG,plus notes), join with:

```bash
python3 work/codex-api-4/t223/e3_seedbank/analyze.py /tmp/e3-review --qc /tmp/frozen-qc.json --qc-sha256 PUBLISHED_HASH --out /tmp/e3-result
```

Unchanged statistical core supplies the primary crossed/seed/input intervals and
MC test, kept separately from the independent integer exact subset reference.
The CLI checks hashes and joins; the human-readable board/code freeze is still
needed to establish that QC preceded unmasking. Never present code-level hash
matching as proof of native noise/input/sampler/runtime provenance.
