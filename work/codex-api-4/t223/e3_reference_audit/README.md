# Historical rest-ranking: held-out labels must never resolve training ties

This **retrospective task-141 methods diagnostic** belongs to task 223, separate
from actual `raj-noise` E0–E3. Board #4781 fixed the calculations before this
script ran. Historical aggregate findings and the source labels were already
known, so these excluded-input scores are not a new blinded generalization test.
No new clips, classifiers, source labels, recipe or Deliverables 1–3 changed.

For each F/QT/N prompt, train on two of the three task-141 inputs and exclude
the third. Rank ten seeds by training mean rest code only; select three using
the frozen ascending numeric ID tie break. Compare with the mean over all ten
seeds on the excluded input. Enumerate all 120 random three-seed subsets for an
exact one-sided reference. Also enumerate every top bank compatible with the
training scores, without selecting a preferred bank from the excluded labels.

The original 89 binary codes plus one unknown still block primary inference.
The table shows unknown=0, a **hypothetical completion**, not an assigned label.
For unknown=1, only F/b1dd33's fixed-bank lift changes, to +0.2333 (p=0.30);
F/b2dd37's admissible-bank count changes from 120 to 36. All 18 results, including
both completions, are in `results.json`.

| Prompt | Excluded input | Fixed-bank lift | Exact p | Equally ranked banks | Lift range across those banks |
|---|---|---:|---:|---:|---:|
| F | b1dd33 | 0.0000 | 1.0000 | 8 | [0, 0] |
| F | b2dd35 | 0.0000 | 1.0000 | 8 | [0, 0] |
| F | b2dd37 | +0.1333 | 0.5333 | 120 | [−0.2000, +0.4667] |
| QT | b1dd33 | +0.1000 | 0.7000 | 35 | [+0.1000, +0.1000] |
| QT | b2dd35 | −0.1333 | 0.9333 | 56 | [−0.1333, +0.2000] |
| QT | b2dd37 | +0.2000 | 0.4667 | 56 | [−0.1333, +0.2000] |
| N | b1dd33 | +0.2333 | 0.3000 | 8 | [+0.2333, +0.2333] |
| N | b2dd35 | +0.2333 | 0.3000 | 8 | [+0.2333, +0.2333] |
| N | b2dd37 | +0.1333 | 0.5333 | 36 | [+0.1333, +0.4667] |

Lifts are code-probability differences. Tie ranges are **identification ranges**
over equally ranked banks, not confidence intervals. The fixed banks' exact
p-values are all ≥0.30; this is not evidence of equivalence or a refutation of
seed banks. There are 18 retrospective, unadjusted tests and no confirmatory
claim. Two completions of a shared unknown label are not independent tests.

The leakage hazard is concrete: for N/b2dd37 a favourable resolution of training
ties gives lift +0.4667 and exact p=8/120, while the frozen rule gives +0.1333
and p=64/120. Choosing that bank using excluded labels would invalidate its
nominal p-value and inflate the apparent evidence eightfold. Neither is below
0.05. QT/b2dd35 and QT/b2dd37 can even change lift sign under different
equally ranked banks. This illustrates why actual E3 must freeze ties before
opening its test labels; it does not change the frozen default in PROTOCOL.md.

The unchanged core also reports 2,000-draw seed and crossed seed/input bootstrap
intervals, Spearman correlation and 9,999-draw seed-map permutation results.
All intervals here are **descriptive and underpowered**: every fold has one
excluded input, and all three inputs share one GAUGE camera setup. Resampling
one input cannot estimate input-population uncertainty. An all-zero excluded
outcome yields a degenerate [0,0] empirical interval, not proof of zero effect.
The exact subset p-value equals a full seed-map permutation p-value because
each size-three subset has 3!7! mappings. Core Monte Carlo values are retained
separately rather than silently replaced.

This is a **rest-only** diagnostic with unvalidated eye codes. Release,
identity preservation, event success, DOVER, dynamic degree, plausibility and
robot prediction are not measured. It cannot justify a physics improvement,
new scene transfer or a deployable seed bank. Actual Program N design metadata,
validated outcomes and native execution records are still awaited; no actual
`raj-noise` outputs were accessed.

Run from the repository root:

```bash
python3 work/codex-api-4/t223/e3_reference_audit/run.py
cd work/codex-api-4/t223/e3_reference_audit
sha256sum -c SHA256SUMS
```

The scalar reference uses exact rational arithmetic independently of the frozen
NumPy core. Seventy-eight checks compare all point estimates and selected banks,
retain the unknown, verify the 90-cell join and tie constraints, reverse excluded
labels without changing selected seeds, and include constant and test-only-winner
fault controls. These are numerical checks, not planted-case validation.
The input CSV is the unchanged sibling `reference_audit/source/codes_named.csv`,
copied from shared commit `028723bdbe6060d161be6849b849e965b4fa5dae`; its SHA256 is
recorded in the output. No native video, noise tensor or execution hash is implied.
