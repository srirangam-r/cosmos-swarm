# Fresh-input pendulum replication — attributed demo readout

dk1 reports that Nano-Phys transferred a supplied period on one fresh GAUGE input across three new seeds. On the second input, every Nano-Phys attempt failed the frozen motion-quality gate.

The frozen-gate totals are **3/6 Nano-Phys outputs within 10% of the supplied period**, versus **0/6 plain outputs within 10%**; plain has 1/6 clean outputs overall. All three Nano-Phys successes come from real_06. The accepted-output ACF median is 1.004807× the supplied period, with source bootstrap 95% interval [1.000645, 1.005342]. This interval resamples only the three accepted seeds from that one take; it is not uncertainty over new scenes or rigs.

For real_06, the wrong-period control follows the supplied 1.7× period on seeds 101–103 (ACF 1.725/1.697/1.700, measure_pend 1.716/1.679/1.706). These are ungated numerical readings: the frozen gate rejects all three because ACF flags check. Overall x17 remains 0/6 clean. Keep the numerical control observation and gate rejection together.

real_14 Nano-Phys is 0/3 clean. ACF ratios near 1 disagree with measure_pend; R² is 0.27–0.48. The source attributes the failure to a small-amplitude scaffold, but this addendum does not establish its cause. Task329 is a separate amplitude experiment owned by dk1. One still frame does not determine angular velocity; any supplied amplitude/direction is additional information.

The target periods (1.199895 and 1.187767 s) are measured from later real video under an assumed 25 Hz clock. This is conditional period transfer on two fresh inputs from one GAUGE rig, not period inference from the first frame or a general first-frame-only recipe. Manual geometry is ±6 px. The shipped release-from-rest proxy uses the visible angle (about74° or4°), and a harmonic large-angle swing does not establish correct nonlinear dynamics.

Setup: unchanged task276 contract/analyzer, Cosmos3-Nano, q8 server04e8e0de81, UniPC, sigma_start0.89844/start19, 832×480, 93frames at24fps, 35steps, CFG6, CPU noise; seeds101–103. Gate: ACF flag ok, luminance flicker<0.08, and reader period agreement within10%; it does not require measure_pend flag ok. The source's plain clean row has measure_pend flag check. Historical crossing reader289/rawFAIL and proposed non-rest state296 are separate and were not used here.

No NVIDIA scores were measured for task277. The separate task319 cohort reports a DOVER cost of about0.057; its seed1-only x17 control is consistent with a common proxy-path cost, without proving equivalence or cause. Plausibility judge, robot prediction and new rigs remain untested. See ../t328/ for that attributed quality scorecard.

This page reuses dk1's saved results, two input images and three contact sheets byte for byte. It is presentation and source verification, not another replication, planted validation or playback test. All18 generated clips have saved hashes; only3 native real06 Nano-Phys MP4s are committed in the source. Other clips stay with dk1. The source contact sheets crop/resize eight frames per clip; labels are the author's frozen gate labels.

Source: https://github.com/srirangam-r/cosmos-swarm/tree/124b6d5b6abbabcf09dfbb256f4a7559cdda56b0/work/dk1/t277_rep
Board review6700 and task277 receipts: board_receipts.json

Review6730 independently reaggregates the same saved results: only real_06 seed102 is clean in both plain and Nano-Phys. Selected arm medians are not a six-pair estimate of improvement. Real14 rejection is unresolved reader disagreement, not proof that the rendered swing failed or that amplitude caused it.
