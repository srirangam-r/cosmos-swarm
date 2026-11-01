Real references for t226 (PREREG "Real references"), made before any t226 Nano clip was viewed:
`python make_real_t226.py <GAUGE pendulum video dir> <GAUGE bouncing-ball video dir> <out>` then `python measure_t226.py <out> real_measures.json`.
- P: GAUGE pendulum 10 from dedup frame 93 (frame-0 vs input MAD 2.87/255, the best-matching frame among 90-96). rec_period v1 1.171 s (mocap 1.174), ME_roi 4.28.
- F: GAUGE ball 1 from dd33 (identical to the input). dy8 +74.9 px (on the plank by ~frame 5), dyEnd +156.6, LM 0.31.
- H: GAUGE ball 1 from dd0 (identical to the input). dy8 -0.8 (still held), dyEnd +196 (the real gripper releases at ~1.2 s), LM 2.33.
All resampled by nearest frame to 24 fps x 93 frames from the ~25 fps dedup sequence. The pendulum reference uses nmax=600 raw frames.
