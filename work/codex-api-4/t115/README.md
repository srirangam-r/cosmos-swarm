# Task 115 completion: timing-clause effect is not estimable under the frozen gates

**Result:** zero of 48 clips passes both preregistered gates (visually admissible rigid swing AND `measure_pend v1 flag=ok`). Both planned period contrasts have **0/16 eligible pairs**. Their effects, SEs and sign tests are undefined. This is an inconclusive timing experiment, not a null effect or a recipe improvement.

| Prompt arm | Clips | Visual Y / N / U | Tool ok | Both gates |
|---|---:|---:|---:|---:|
| B: neutral | 16 | 1 / 13 / 2 | 3 | 0 |
| T: 1.2 s / three swings | 16 | 1 / 14 / 1 | 1 | 0 |
| W: 2.5 s / 1.5 swings | 16 | 0 / 15 / 1 | 1 | 0 |

These are exact counts on a fixed batch, not calibrated population rates. Visual labels have not passed planted validation, so no physics finding is claimed. In particular, U does not mean nonrigid, and zero eligibility does not mean every clip fails to swing. The two visually admissible clips are B and T on pend10 seed 4; both fail the primary fit checks. All five automated `ok` fits belong to clips rejected by the frozen visual review. A sinusoidal fit alone therefore cannot establish admissibility for this batch.

## Setup and protocol

- Existing experiment, no new generation by codex-api-4: ro-3's 18 completed seed-1–3 jobs plus ro-api-3's 30 completed seed-4–8 jobs. Two real GAUGE mid-swing frames × 8 distinct seed values × 3 prompts.
- Inputs: `work/ro-3/task99_midswing_pendulum/inputs/pend10_mid_f93.png` and `pend11_mid_f81.png` in this repo. These later real-video frames make the experiment a diagnostic, not an eligible first-frame-only final recipe.
- Nano I2V, 832×480, 93 frames, 24 fps, 35 steps, CFG 6, requested shift 10, empty negative, no extra params. Actual announced board sampler: Karras sigmas; requested shift ignored (#2870). All primary jobs use q8-* endpoints, announced RTX Pro 6000 96 GB (#2678). This analysis does not establish a cross-stack cause.
- Sidecars confirm the timing clauses, input names, all requested settings and endpoints. All 48 videos decode to 832×480, 93 frames, 24 fps. Only 1/16 T–B pairs and 2/16 W–T pairs share the exact endpoint; seed matching is not a demonstrated bitwise pairing across endpoints. Raw sidecars do not pin a weight revision or every server-library version.
- Original preregistration: `work/ro-api-3/t115/PREREG.md` at da0c579, copied here as `ORIGINAL_PREREG.md`. Reference period 1.18 s. Primary accuracy contrast is Δ absolute log error T minus B; dose is log(W/T), both paired by input × seed. Neither can be computed under its eligibility rule.

## Blinding and validation

All 48 primary clips were randomly mapped to c01–c48 before fresh result viewing. Only the two input scenes remained recognizable. The agent read prior board results and corrections before this work, so this is not an unaware replication of the old qualitative counts. A single f0 image was viewed before masking to set layout; no subsequent frame or result was viewed then.

Full-scene sheets show f0,8,...,88,92 at half spatial resolution directly from original videos. Native crops resolved ambiguities, followed by stride-four native crops on every provisional Y and U. This denser check changed some initial Y judgments; only final codes were used. Transient errors between sampled frames can still be missed. Mild rod curvature that remained ambiguous against blur was retained as U. The strict visual rubric is subjective and needs independent review.

- Key SHA256, posted before QC (#3716): `55efdbe3783333d2a1d82b70d5b326972c697d72f77ba27cd9175fbdf1ce5257`.
- Codes SHA256, posted before arm/period unblinding (#3755): `af474cbcf5967d04cd021b0bfcedf8290c6207819122c8fe87c8f28944e7cf44`.
- Local pre-unblind freeze commit 1ff7966 became **61503b4** after pulling/rebasing other agents' changes; the code-file hash did not change. The code file has not been edited after unblinding.
- Primary tool and its `trk.py` dependency are byte-identical to planted-pass commit 2e26463. `measure_pend.py` SHA256: `ea671320010ff80ac5f9dce355590bc3e1952eeb62ad240c47e7fd783f07d120`; `trk.py`: `4de7b99dd38677a707e765d2b44d305b4fbade61b0e9e425f1dbad41549eaf2e`. Existing referee composite PASS 20/20, four pendulum estimates <5%, in `tools/trk_ballfall/referee_result_pend_v1.json`. No new referee submission was made.
- Secondary `pend_acf --skip 12` outputs are retained in the raw JSON/table, but do not override the frozen primary gates. Its README records four planted pendulums <5% with the formal composite-count threshold not met by that submission alone.

## Evidence and reproduction

- `codes.json`, `blind_key.json`, `QC_PROTOCOL.md`: complete visual decisions, masking key and protocol.
- `table.csv`, `summary.json`: all clip hashes, queue IDs, endpoints, decisions, raw periods, flags, reasons and explicit missing contrasts.
- `metrics_masked.json`: unchanged-tool outputs, including fit bootstrap intervals, retained for excluded clips as diagnostics only.
- `sidecars.json`, `queue_snapshot.json`: provenance for every primary cell.
- `blind/`, `dense_*.jpg`, `detail_*.jpg`: sheets used for review. `examples/` has the original c14 and c37 MP4s: an automated `ok` fit with bent geometry and a visually admissible clip whose primary fit fails, respectively. Their hashes appear in the table.

From a clone of this repo, with Python, OpenCV, NumPy and SciPy installed, and access to the announced shared queue:

```bash
python3 work/codex-api-4/t115/prepare_blind.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 work/codex-api-4/t115/measure_primary.py
python3 work/codex-api-4/t115/analyze.py
```

The first command fetches the existing completed jobs and uses the frozen key; it submits nothing. It needs the queue to retain those jobs. The second is incremental: remove/move `metrics_masked.json` locally for a fresh unchanged-tool rerun. The third verifies both frozen hashes, checks every sidecar and video, and recomputes counts and missingness. `prepare_blind.py` and `measure_primary.py` were corrected after code freeze only for paths/first-run directory creation; neither changes the frozen codes or measurement algorithms.

Next scientific step, if this question is pursued, is a measurement/geometry design that yields valid matched periods across ≥3 seeds, with its own predeclared controls. Relaxing acceptance rules after seeing these outcomes would not rescue the present primary test. No NVIDIA scoreboard was run because this batch establishes no candidate improvement.
