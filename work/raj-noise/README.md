# Program N (Raj via Claude): does Nano's motion come from the initial noise, not the text?
- `make_jobs.py`: every job file (E0-E5), all with `extra_params.noise.device = "cpu"`. Inputs are the real GAUGE frames
  and the exact task-154 / task-191 prompts. Queue owners raj-noise, raj-noise-b..i, raj-noise-e20..e22.
- `analyze.py <clips_dir> <E0|E1|E2|E4>`: the analysis, fixed before the clips were fetched. Pendulum periods come from
  tools/pend_acf (ro-3) run unchanged.
- E0: does a seed carry across GPU types once its noise is drawn on the CPU (#4786: yes)?
- E1: T2V pendulum, colour words x speed words x 16 seeds. E2: real frames x {F, R, N, QT} x seeds.
- E3: pendulum seed bank on 3 real frames. E4/E5: one band or region of the noise taken from a second seed.
