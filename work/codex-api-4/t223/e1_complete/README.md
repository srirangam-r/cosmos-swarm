# E1 full64: text changes image magnitude alongside a large seed association

The completed, pre-specified 16-seed analysis finds **fast−slow image-change
+0.7560 ±0.1233 seed SE gray levels per native transition**, averaged over
requested colour; seed-bootstrap 95% interval **[0.5341, 1.0036]**. The paired
average is positive in all 16 seeds. All 64 planned clips are included, with
no imputation. The prior [58-clip snapshot](../e1_diagnostic/README.md) is retained
unchanged; all its video hashes, native contracts, measurements and endpoints
match exactly in this update.

This is an **unvalidated pixel diagnostic** combining appearance and motion.
It does not measure physical speed, pendulum period, requested-colour compliance
or rigidity. It cannot validate those parts of human finding #4935.

| Diagnostic, all 16 seed clusters | Estimate | 95% whole-seed bootstrap interval |
|---|---:|---:|
| Red fast−slow M | +0.6759 | [0.4511, 0.9466] |
| Blue fast−slow M | +0.8360 | [0.5848, 1.1026] |
| Fast−slow, average over colour | +0.7560 | [0.5341, 1.0036] |
| Blue−red, average over speed | −0.0265 | [−0.1876, 0.1009] |
| Seed SS / total SS | 0.6543 | [0.1322, 0.7783] |
| Four-prompt SS / total SS | 0.2129 | [0.1242, 0.6157] |
| Seed×prompt SS / total SS | 0.1328 | [0.0775, 0.3061] |

The primary three-test family is now complete. Four-prompt omnibus, red
fast−slow and blue fast−slow each have Monte Carlo raw p=0.0001, Holm p=0.0003
(9,999 draws with plus-one correction). Independent exhaustive scalar checks
are saved separately; they do not replace the frozen Monte Carlo procedure.
The colour interval does not establish equivalence.

Across-seed SD of the four-prompt seed means is 0.6886 gray levels. A large
seed SS share and a consistent paired text association coexist. These descriptive
shares depend on the chosen seeds, prompts and outcome. They do not identify a
universal causal allocation between text and noise. In T2V the seed also changes
scene layout and appearance.

Declared Cosmos3-Nano T2V: one pendulum scene description, red/blue × three-second
or half-second swing wording, seeds 201–216, 832×480, 93 frames at 24 fps,
35 steps, CFG 6, null negative, requested CPU noise and shift 10. All clips ran
on declared q8-5/6, 32 each. Eight of 16 full seed groups share one exact endpoint;
red speed pairs match in 10/16 and blue in 14/16. Actual native sampler, noise
tensor, checkpoint and runtime authentication remain unavailable. The published
Karras default ignores requested shift. Request echoes do not authenticate
execution, so endpoint variation is not isolated from text.

64/64 request/native-video contracts pass. Three independent full-video FFmpeg
and explicit block-area traces agree within 5.56e-16. Scalar SS, contrasts,
exhaustive sign flips, covariance, full family retention, all 58 retained
measurements and saved-design/outcome numerical replay pass. These are software
checks; planted-case validation is **not yet** available for M. The inherited
sensitivity output now duplicates the primary population; it is not replication.

See [METHOD.md](METHOD.md) for exact provenance, frozen timing, scripts,
reproduction commands and limitations; [results.json](results.json) contains
per-seed values, covariance, all seven SS terms and intervals. No E2/E3 outcomes
were opened. No physics, real-photo transfer, recipe or NVIDIA improvement is
claimed; Deliverables 1–3 are unchanged.
