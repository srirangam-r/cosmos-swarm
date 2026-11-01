# Nano-Phys scoreboard update — attributed, provisional

dk2's completed task319 scores show a DOVER cost on the task276 pendulum grid. Source: [9e92945](https://github.com/srirangam-r/cosmos-swarm/tree/9e92945/work/dk2/t319), finding6690. This is a presentation of the author's scores, not an independent scoring or physics replication.

| Metric | Plain, n=18 | Nano-Phys, n=18 | Real references, n=6 |
|---|---:|---:|---:|
| DOVER fused | 0.5439 | 0.4867 | 0.5459 |
| Binary DD | 7/18 | 0/18 | 0/6 |
| Continuous flow proxy (dd_norm) | 4.83 | 0.44 | 1.94 |
| Approximate-DD MF, published formula | 0.238 | 1.000 | reference DD=0 |

The author reports Nano-Phys minus plain DOVER = **−0.057175**, with source-JSON 95% exact take-bootstrap interval **[−0.067451, −0.048844]**. All six take means and all18 matched pairs are negative. The board message/README quotes [−0.068, −0.049]; this addendum uses JSON precision. The author's bootstrap resamples six take means after averaging three seeds; it is conditional on these fixed shared seeds and repeated takes of one rig. Plain pooled seed SD=0.04443; estimated SD of a three-seed mean=0.02565. The entire interval is below the proposed −0.030 margin, which the source says **was never approved**. This threshold is not an official NVIDIA acceptance criterion.

**MF=1 is degenerate:** every Nano-Phys and real-reference binary DD is zero. With ddof=0 and MC's 0/0→0 policy, static output also receives MF=1. The scorer approximates original VBench DD; MF uses the published Cosmos3 formula, not an NVIDIA-identical implementation. Continuous dd_norm is a separate normalized-pixel optical-flow proxy. It undershoots real flow and cannot identify which part of the image lost motion.

The grid has six held-out input images × seeds1–3 per main arm, plus six x17 clips at seed1. The x17 minus Nano-Phys DOVER difference is −0.000898 on those six same-seed pairs; similarity is descriptive and does not identify the quality-loss cause or prove equivalence. Real/plain means being close is not an equivalence result either.

Real references are six 93-frame repeated takes of one GAUGE pendulum rig, originally nominal25fps versus generated24fps. For MF the author re-encoded them at24fps and reports the same frame sequence. Retiming changes playback time; it does not establish the camera's true clock or an independently matched physical duration. Original NVIDIA protocol used5s and about100 real references per FPS band. This grid does not establish broad real-video non-regression.

Nano-Phys here uses sigma0.90 and a proxy supplied with a period measured from later real video. The original12/18 period result is conditional transfer, not a first-frame-only recipe. Plausibility judge, robot prediction, new rigs/prompts and the cause of the DOVER drop remain untested. Task277's fresh-scene run is separate.

Suggested wording for a human to apply: “Nano-Phys transfers a supplied pendulum period, with a visual-quality cost. On six held-out input images × three seeds, the author reports a0.057 DOVER drop versus plain Nano. The higher motion-fidelity score is degenerate on these zero-DD references; a general first-frame-only recipe and full scoreboard non-regression remain unproved.”

[Interactive scorecard](index.html) · [exact source files](source/) · [board receipts](board_receipts.json) · [source hashes](source_receipt.json) · [verification](verification.json). Earlier demo artifacts, judged rootREADME and reports are preserved.
