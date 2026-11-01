# Independent g check of rahul-3's sim_drop clips (task 11), raj-3

**Question.** Do the sim_drop training clips encode the g in their sidecars, as measured by planted-PASS tools that share no code with rahul-3's check.py? This was asked in the task 11 thread, msg 239.

**Clips.** rahul-3's `sim_drop/gen.py` v1 (sha256 46cbafde…f24, copied from GB10 ~/jobs/rahul-3/sim_drop on 2026-11-01 03:08 UTC). Regenerated locally with `--start 0..19` (seeds 1000-1019) in both `--g_mode real` and `--g_mode wrong`, with the same MIT-Indoor test-split backgrounds (HF keremberke/indoor-scene-classification data/test.zip).
These clips should be the same scenes as clips 0-19 of rahul-3's set. Encoder versions may differ, so the clips may not be byte-identical.

**Methods** (scale = sidecar px_per_m, fps 24):
- `firstfall` v1 (tools/realball, raj-2; referee PASS 20/20, msg 264), seeded at the sidecar's frame-0 ball centre.
- `measure_bounce` v1 `fit_track` (tools/trk_ballfall; part of the referee composite PASS, msg 246): first rebound flight on the firstfall track.
- `measure_ball` v5 + `measure_bounce` v1 on `trk.blobs` (largest change blob), to test my own tool on holder scenes.
- Truth track: the sidecar's stored per-frame centres through the same free-v0 quadratic (no tracker).

**Results** (ratio = measured / sidecar g, flag=ok only; `simdrop_check_results.json`):

| set | method | n ok / 20 | mean ± SE (sd) | off by >10% |
|---|---|---|---|---|
| real (9.81) | truth track | 20 | 1.0000 | 0 |
| real | firstfall | 15 | 1.003 ± 0.018 (0.070) | 1 (clip 16: 1.20, n_fit 6) |
| real | first rebound, seeded track | 13 | 0.996 ± 0.006 (0.022) | 0 |
| wrong (U 1.5-4) | firstfall | 19 | 1.004 ± 0.011 (0.048) | 1 (clip 1: 1.14) |
| wrong | first rebound, seeded track | 15 | 1.001 ± 0.004 (0.014) | 0 |
| real | v5 largest blob | 5 (all holder=none) | 0.95 ± 0.04 | 1 (clip 17: 0.79) |
| wrong | v5 largest blob | 7 | 0.81 ± 0.13 | 3 (incl. clip 11: **0.036, flag ok**) |

- The control is separable: on flag=ok clips, measured g ranges over 8.98-11.8 for real and 1.79-3.94 for wrong, with no overlap.
- Release timing: firstfall t0 is within -0.02 to +0.03 s of the sidecar `t_fall_start` on ok clips.
- Real-g falls are short, 4-10 fit frames at 24 fps for h 0.3-1.3 m, so single-clip first-fall g scatters ~7% (sd). The first rebound flight is tighter.

**Tool caveat (my own trk_ballfall v5).** The largest-change-blob tracker follows the gripper or hand as it lifts away (qc/simdrop_real_00001_v5_qc.png). On 0/15 real-g holder clips it gives a usable result, and on 2 wrong-g holder clips it returns **flag=ok with a wrong g** (0.036× and 0.85× truth). In wrong_00011 it fits the hand's hold phase and returns g = 0.077 m/s², R² 0.988, dAIC 12.9 (qc/simdrop_wrong_00011_v5_qc.png).
Do **not** use measure_ball v5 / measure_dir on scenes where a gripper or hand moves after release (that includes GAUGE-style Cosmos clips). Use a seeded single-ball tracker (firstfall), and use the first rebound flight on that track where one exists.

Reproduce: `python3 -I ff_simdrop.py <set_dir> <repo>/tools <out>` and `python3 -I measure_simdrop.py <set_dir> <repo>/tools/trk_ballfall <out>`.
