# rev6767: independent box-mask region swap (dk1 review of #6767)

Inputs: the same 36 t276 plain/nphys clips as t319/t331. Fetched from the queue (plain owner dk2, nphys owner rahul-5-agy); sha256 36/36 match work/dk2/t319/gen_sha256.txt. No generation.
Code: none shared with work/dk2/t331.
- `swap_box.py <gen> work/dk2/t276 <out>`: the corridor is the **t336 region-fix rectangle**: proxy (normal + x1.7) pixels with max_t|f_t−f_0|>30, plus the pivot and bob points, dilated 32 px, bounding box, 8 px linear ramp. It covers **5–9% of the frame** (t331: 20–49%), and it does not include plain's own scattered motion. Cells pp/nn/np/pn are re-encoded **losslessly** (x264 qp 0, yuv420p).
- Scorer: tools/nv_scoreboard/score.py unchanged, `--dover_reps 3 --no_dd`, RTX 4060 (dk1). This rig reads 0.008 below t319 on sha-matched clips (t336_region/results_band).
- `effects.py`: main effects, 6-scene cluster bootstrap (20000, seed 0). `bg_motion.py`: outside-box motion vs the per-clip background effect.

## Results (fused DOVER, 6 scenes × 3 seeds, paired)
| quantity | value [95% CI] | clips < 0 |
|---|---|---|
| total nn − pp | −0.063 [−0.075, −0.053] | 18/18 |
| outside-box ("background") effect | **−0.071 [−0.081, −0.063]** | 18/18 |
| pendulum-box effect | **+0.008 [+0.003, +0.014]** | 6/18 |
| interaction | −0.006 [−0.009, −0.003] | 12/18 |
| np − pp (nphys box pasted into plain) | **+0.014 [+0.011, +0.018]** | 3/18; 18/18 ≥ −0.020 |

Technical: background −0.0064, box −0.0046. Aesthetic: background −0.0227, box +0.0069.
Lossless re-encode sanity: pp − original plain −0.002 (range −0.022 to +0.014); nn − original nphys −0.008.
Outside the box, nphys moves 2.4× less than plain (mean |Δframe| 0.63 vs 1.50 grey, 18/18). That deficit does **not** predict the per-clip background effect (Pearson 0.09, Spearman 0.23).

## Reading
- Replicates the direction of #6767 with a different mask, encode and scoring run: the cost sits outside the pendulum.
- With the tight box, the attribution is ~all background (113%). The box itself is slightly *better* in nphys.
- t331's 30% corridor share likely comes from its larger mask, which takes in plain's scattered moving pixels. Plain is not static: 18–23% of pixels exceed 20 grey somewhere.
- A perfect region-wise fix (plain's background with nphys' box) would land at or above plain on DOVER. That is the ceiling a dual-clock fix (t336b) can reach.
- Limits: a composite is not a generation, so seams and coherence are not tested. One rig and one scorer (DOVER only). Shared seeds 1–3. Same 6 near-identical takes of one rig.
