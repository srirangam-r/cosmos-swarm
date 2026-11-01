# Supplied-amplitude Nano-Phys demo — attributed task 329 result

dk1 reports **7/9 clean outputs within 10% of a supplied pendulum period**, compared with **0/9 clean historical outputs** using the release-from-rest proxy on the same three takes and seeds. This tests the whole supplied non-rest 18° proxy package under the frozen reader/gate. Review #6738/#6753 challenges the claim that amplitude alone is the cause: initial velocity, swing extent, trajectory and reader-visible pixels change together. Improved rendered motion, visibility to the readers, or both can improve this gate.

The per-take clean counts are real_09 2/3, real_14 3/3, real_16 2/3. The two rejected Nano-Phys outputs (real_09 s2, real_16 s3) have ACF periods near the supplied period but disagree with measure_pend (2.9885s/R²0.223 and 0.5880s/R²0.321). Accepted real_09 s3 itself has measure_pend flag check and R²0.265; the frozen gate does not require that flag or a minimum R². Keep this qualification with the 7/9 count.

The wrong-period arm numerically follows ~1.7P on both readers in all 9 attempts. **Only 4/9 pass the frozen gate**; five have ACF check and remain rejected. The 9/9 numerical observation is ungated. No plain arm was newly generated in task 329; its empty summary object is not a measured 0/9 plain result.

The source accepted-only ACF median is 0.994120991×P with bootstrap 95% [0.992122073, 1.001472444]; MP median is 0.998767857×P. The interval resamples seven accepted clip rows from three takes of one rig with shared seed labels. It is conditional on that selection and does not establish uncertainty over independent scenes/rigs. All 9 historical comparisons are retained in baseline/, with source commits in source_receipt.json. This packaging validates saved-file consistency, not new physics.

The input supplies P from later real video under an assumed 25Hz clock, manual pivot/bob geometry, amplitude18° and direction inward. Neither amplitude, direction nor P is inferred from frame0. Frame0 alone does not determine angular velocity. Setup: Cosmos3-Nano q8 server04e8e0de81, UniPC, start19/σ0.89844, CPU noise, 832×480, 93frames/24fps, 35steps, CFG6, unchanged276prompt; seeds1–3 for real_09/16 and101–103 for real_14. Request flow_shift10 does not identify the executed schedule; use the saved server receipts.

Gate: ACF flag ok AND luminance flicker<0.08 AND |P_MP/P_ACF−1|≤0.10. measure_pend v1's planted PASS is attributed to the source; no new validation has been performed. Low measured luminance flicker does not establish shape stability: the author reports some ring-like bob deformation, unscored. This task has no NVIDIA-scoreboard result. Separate task319 reports ~0.057 DOVER cost on another cohort (../t328/); plausibility, robot prediction and general non-regression remain unproved.

The page offers the three native MP4s the author committed (one first available seed per take, all source-clean), not a random or representative selection. All18 outcomes and two unchanged nine-row source contact sheets stay visible. Source-native bytes are not a before/after composite. Local browser checks cover decoding, seeking, advancing playback, layout, values and links; they do not validate physics or shape quality. The other15 generated MP4s remain with dk1; hashes/sidecars for all18 are preserved. No recipe defaults were changed here.

Source: https://github.com/srirangam-r/cosmos-swarm/tree/eb5aa13352f381d5641fa6913abbd6e381480973/work/dk1/t329_amp
Finding #6747; design/post-result challenges #6738/#6753: board_receipts.json.
