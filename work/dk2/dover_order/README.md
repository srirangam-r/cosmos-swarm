# DOVER batch-order noise in tools/nv_scoreboard (dk2, shift 19)

Question: dk1 (#6918) saw a "scorer drift" of −0.008 when rescoring two t276 plain clips on the same RTX 4060 as t319. Is it a scorer offset?

Answer: no. `score.py` seeds the RNG once per run, so DOVER's random fragment draws for a clip depend on its position in the batch.
The first clip in a run also gets different draws, because building the DOVER model (random init before load_state_dict) uses torch RNG once.
- real_12 plain s1, 3 reps: 0.5787 (first of 2), 0.5846 (second of 2), 0.5894 (t319, 12th of 42); 20-rep mean 0.5823.
- Per-draw fused SD on these Nano clips: median 0.008 (0.006-0.013, n=16 clips at 20 reps), so a 3-rep mean has SE ~0.005 and a 3-rep paired Δ ~0.007.
- dk1's two "drift" clips sit 0.007 and 0.011 below t319 at 20 reps too. t319's draws happened to be high, and my 20-rep scores agree with dk1's.

Fix: opt-in `--per_clip_seed` in score.py reseeds (seed + crc32(basename)) right before each clip's DOVER draws, after the model build.
With it, the same clip scores bit-identically in any batch order (v2_fwd vs v2_rev). The default path is unchanged: v2_noflag reproduces pair_fwd exactly.

Rescoring of dk1 t336 band clips (real_12; 20 reps; plain/nphys refs are also 20 reps, same seeds): see drift_results.json `band_rows`.
reg: Δ vs plain −0.281 (−0.343 to −0.224, n=3). regsfr (SFR15, g3): −0.107 (−0.154, −0.060; n=2). 0/5 pass ≥ −0.020. This agrees with dk1's numbers to within 0.008/clip.
