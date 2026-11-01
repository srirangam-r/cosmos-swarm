# Task 276 (child of #273): Nano-Phys pendulum benchmark. FROZEN before any clip (dk2)

**Held-out first frames:** frame 0 of GAUGE pendulum real_09, 12, 16, 17, 18 and 19 (codex-api-4 t8 clips; GAUGE-Dataset@f95bb06).
- Excluded: pend10 and pend11 (ro-3's design frames, #5315) and real_13 (measure_pend fails on the real clip).
- All six are near-vertical mid-swing frames, like the design frames.
- Pivot and bob pixel positions (832x480) were hand-annotated on gridded 3x crops (inputs/annot_grid_*.png), ±3 px. My reading of real_10 matches ro-3's pend10 numbers within 4 px.
- frames.json holds the annotations and the real periods from my frozen e6x/real.json: measure_pend at --fps 24 on the 25 Hz real clip, divided by 25 to give s.

**Arms** (names t276_<real_XX>_<arm>_s<seed>.mp4, 93 f @ 24 fps, 832x480, noise.device=cpu):
- plain: Nano with the E6 pendulum base prompt (work/raj-noise/e6/pend_base.txt), seeds 1-3.
- nphys: dk1's Nano-Phys CLI (#273) with `--period P_real_s` from frames.json, defaults otherwise, seeds 1-3.
- nphys_x17: the same with `--period 1.7*P_real_s`, the wrong-physics control (does the output follow the proxy?), seed 1 only.
- Total 6x3 + 6x3 + 6 = 42 clips on q8, once the servers run the frame-0-safe latent.py.

**Readout:** `python3 -I analyze_t276.py <clip_dir> <out_dir>`. It writes t276_results.json, t276_table.md and strip_<arm>.jpg.
- A clip is clean (Raj's v2 rule) if pend_acf says ok, flicker < 0.08 and measure_pend is within 10% of pend_acf.
- Pre-registered readings are in the script docstring.

**Dry-run check:** real_09 and real_12 read at --fps 24 give P/P_real = 1.042 with measure_pend, which is exactly 25/24, as they should. flicker = 0.005.

**Caveat (also in #5703):** --period is supplied by the user. A pass shows that Nano-Phys renders a given period cleanly on new frames (copy-through, like ProxyUp). It does not show that Nano infers the period from the image.
