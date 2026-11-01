# E1/E2 outcome-blind adapter addendum

Fixed before coding or Program N outcome access (board #4670, shift 13).
This supplements, and does not replace, `PROTOCOL.md` version 1.

The multi-prompt omnibus statistic is the sum over prompt and input of squared
deviations of each seed-averaged cell from its input's prompt average. It equals
`(SS_prompt + SS_prompt:input) / n_seed`. Each randomization permutes prompt
labels independently within each seed, with the SAME permutation for all that
seed's inputs. Enumerate the full product of permutations if it has at most
9,999 elements; otherwise use 9,999 draws, RNG seed 20261102, and a plus-one p.
This tests stable prompt differences within inputs, including effects that
cancel across inputs. It does not test the absence of every seed:prompt effect.
Its exchangeability null and one draw per cell cannot establish a universal
causal allocation. The seven-term descriptive decomposition remains essential.

`factorial_adapter.py` accepts a precommitted design JSON and a separate outcome
JSON list, both keyed by run ID. It rejects duplicate/extra runs, incomplete
planned cubes, method mismatch, invalid numbers, and extra outcome keys. Missing
outcome records and explicit invalid/unknown labels remain in missingness tables
for every seed, prompt and input. They block the primary cube; there is no
complete-case substitution or imputation. Undefined variance shares in a
constant complete cube remain undefined.

Every test is registered by ID, outcome, stratum, kind and Holm family BEFORE
outcomes are opened. All registered members count toward their family's size;
untested members enter the adjustment at p=1 and have null reported p-values.
An untested member is not evidence for its null. Different experiments must have
different families; the adapter handles one experiment at a time. All p-values
and SS are diagnostic until source validation and execution provenance are
independently audited. A manifest's declaration is retained, never promoted to
runtime proof or planted-case validation by this program.

Minimal design structure (all examples are manufactured):

```json
{
  "version": 1,
  "experiment": "E1",
  "provenance": {"status": "unverified", "evidence": []},
  "strata": [{
    "id": "same_gpu_stack",
    "levels": {"seed": [1, 2], "prompt": ["base", "alt"], "input": ["a"]},
    "runs": [
      {"run_id": "r1", "seed": 1, "prompt": "base", "input": "a", "artifact_sha256": "64 hex characters"}
    ]
  }],
  "outcomes": [{
    "id": "event_success",
    "definition": "initiates, preserves identity, and reaches intended ending",
    "method": "blind_codes@frozen_revision",
    "validation": {"status": "unvalidated", "evidence": []},
    "value_range": [0, 1]
  }],
  "tests": [
    {"id": "joint", "stratum": "same_gpu_stack", "outcome": "event_success", "kind": "omnibus", "family": "E1_primary"},
    {"id": "alt_base", "stratum": "same_gpu_stack", "outcome": "event_success", "kind": "contrast", "a": "alt", "b": "base", "family": "E1_primary"}
  ]
}
```

The runs array must contain EVERY planned seed×prompt×input cell (the abbreviated
example above intentionally omits three). Artifact hashes are design commitments
or fetched-artifact identities; this adapter does not fetch clips or audit their
sidecars. Repeated artifact hashes are reported for audit, never independent
replicate counts. A stratum declares one compatible stack; the adapter cannot
verify that a human assigned runs to the correct stratum.

Outcome records have `run_id`, `outcome`, `state` (`valid`, `invalid`, `unknown`),
`value` (finite numeric for valid, null otherwise), `method` matching the registry,
and `evidence`. Invalid/unknown records require a nonempty `reason`. Missing
records receive state `missing`, separately from invalid/unknown. `valid` means
the measurement exists under that method, not that the method passed validation.

```bash
python3 work/codex-api-4/t223/factorial_adapter.py design.json outcomes.json --out result.json
python3 work/codex-api-4/t223/test_factorial_adapter.py
```

The runner uses the unchanged version-1 core for decomposition, bootstrap and
paired contrasts. It hashes both input files and includes the full registered
test family, cube order and provenance/validation declarations in output.
Actual factor levels, methods, strata and test registry still await Raj's
design-only manifest. No Cosmos result is supplied with this addendum.
