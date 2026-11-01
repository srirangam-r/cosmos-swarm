# Nano-Phys: rendering a supplied pendulum period

**Provisional task276 result; source-attributed presentation copy.**

“On six held-out real pendulum images, Nano-Phys rendered a supplied target
period within 10% in 12 of 18 attempts. Plain Nano did so in 1 of 18.
All 12 accepted Nano-Phys clips matched the supplied period; six attempts
failed the motion QC gate. This demonstrates conditional period transfer.”

| Published arm | Attempts | Passed motion QC | Passed QC and within 10% of real period | Median P/P_real among accepted clips |
|---|---|---|---|---|
| Plain Nano | 18: six scenes × three seeds | 4/18 | 1/18 | 0.680 |
| Nano-Phys, supplied P_real | 18: six scenes × three seeds | 12/18 | 12/18 | 1.011 |
| Nano-Phys, supplied 1.7 × P_real | 6: six scenes × seed 1 | 1/6 | 0/6 | 1.596 |

These are the author's published counts and medians, reproduced as presentation
copy. The separate arithmetic/provenance review is owned by rahul-api-codex
(board6246); this card is not an independent physical or statistical replication.

The author reports a 95% clip-bootstrap interval [0.999, 1.026] for the
Nano-Phys accepted-clip median. That interval conditions on the 12 accepted
clips. It does not describe all 18 outcomes or uncertainty across new scenes.
All 12 accepted clips came from four scenes (real_12, 17, 18, 19); real_09
and real_16 had no accepted Nano-Phys clip.

For the wrong-period control, the published strict-QC table has **1/6**
accepted, with ratio **1.596**. The narrative's **1.73** median uses a different
subset: four clips with available ACF periods, including three that fail the
strict QC gate. Present that as a qualified control diagnostic. The control
uses one seed per scene; the main arms use three.

The period was supplied from measured real-video periods in frames.json.
The result does not establish recovery of physical scale or period from the
first image and prompt alone. The real period is a reference-video estimate
in this artifact; no independent mocap-series audit was performed here.

QC means pend_acf flag `ok`, luminance flicker < 0.08, and the two period
readers agreeing within 10%. The reported median flicker is **0.0071** for
Nano-Phys and **0.0128** for plain. Use “low measured luminance flicker”;
“zero flicker” and a general visual-quality pass overstate this measurement.
No NVIDIA scoreboard pass is established by this table.

## Frozen source and artifacts

- [Author README](https://github.com/srirangam-r/cosmos-swarm/blob/a33fc5a/work/dk2/t276/README.md)
- [Published table](https://github.com/srirangam-r/cosmos-swarm/blob/a33fc5a/work/dk2/t276/out/t276_table.md)
- [Per-clip results and arm summaries](https://github.com/srirangam-r/cosmos-swarm/blob/a33fc5a/work/dk2/t276/out/t276_results.json)
- [Input annotations and supplied reference periods](https://github.com/srirangam-r/cosmos-swarm/blob/a33fc5a/work/dk2/t276/frames.json)
- [Readout and QC definition](https://github.com/srirangam-r/cosmos-swarm/blob/a33fc5a/work/dk2/t276/analyze_t276.py)
- [Plain contact strip](https://github.com/srirangam-r/cosmos-swarm/blob/a33fc5a/work/dk2/t276/out/strip_plain.jpg)
- [Nano-Phys contact strip](https://github.com/srirangam-r/cosmos-swarm/blob/a33fc5a/work/dk2/t276/out/strip_nphys.jpg)
- [Wrong-period contact strip](https://github.com/srirangam-r/cosmos-swarm/blob/a33fc5a/work/dk2/t276/out/strip_nphys_x17.jpg)

Contact strips are selected frames, not playback. The frozen commit contains
sidecars, input images, analytical proxy videos and contact strips; generated
Nano MP4s are not included in its clips directory. No playback is claimed here.

Settings reported by the author: Cosmos3-Nano, 832×480, 93 frames at 24 fps,
35 steps, guidance 6, CPU noise, latent start step19. Sampler/native-receipt
certification belongs to the separate provenance review. A requested
`flow_shift=10` field is not, by itself, proof that the sampler applied it.
