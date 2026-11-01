# task 182 (kiro-1): measure_pend v1 on Nano mid-swing GAUGE pendulum clips vs the real continuation
- Tool: tools/trk_ballfall/measure_pend.py v1, unchanged (planted PASS via v5 pendulum estimates).
- Nano clips: t175 pend10_mid_f93, base/R/N x seeds 4-7, q8 endpoints, 832x480, 93 f @ 24 fps, 35 steps, CFG 6, Karras (flow_shift ignored), empty negative. Clips are local on nail-laptop (hashes: work/kiro-1/t175/clips_SHA256SUMS).
- Real reference: GAUGE pendulum 10 (dev, measure only), dedup + letterbox 832x480, frames 93-185 (frame 93 = the Nano input). Tool 1.178 s [1.172, 1.184], mocap zero-crossing period over the same window (1.52-5.20 s after release) 1.174 s.
- Results: pend_periods.json; QC plots in qc/.
- Run: python3 run_pend.py <repo> <t175 clips dir> <gauge dir with 10.mp4/10.json> <outdir>
