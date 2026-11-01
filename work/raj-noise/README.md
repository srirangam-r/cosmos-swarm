# Program N (Raj via Claude): does Nano's motion come from the initial noise, not the text?
- `make_jobs.py`: every job file (E0-E5), all with `extra_params.noise.device = "cpu"`. Inputs are the real GAUGE frames
  and the exact task-154 / task-191 prompts. Queue owners raj-noise, raj-noise-b..i, raj-noise-e20..e22.
- `analyze.py <clips_dir> <E0|E1|E2|E4>`: the analysis, fixed before the clips were fetched. Pendulum periods come from
  tools/pend_acf (ro-3) run unchanged.
- E0: does a seed carry across GPU types once its noise is drawn on the CPU (#4786: yes)?
- E1: T2V pendulum, colour words x speed words x 16 seeds. E2: real frames x {F, R, N, QT} x seeds.
- E3: pendulum seed bank on 3 real frames. E4/E5: one band or region of the noise taken from a second seed.

## Results (all clips drawn with `noise.device = "cpu"`, real GAUGE frames unless noted)
- **E0, seeds across GPU types:** with the noise drawn on the CPU, one seed gives the same clip on three GPU types: mean pixel difference 0.97, against 3.04 with GPU-drawn noise (#4786).
- **E1, text-to-video pendulum (colour words × speed words × 16 seeds):** the text sets the bob's colour (63/64 clips) and how much moves. It doesn't set the swing period: seed η² 0.69, speed words 0.002 (#4935).
- **E2, real pendulum frames × 4 prompt variants × seeds (144 clips):** the same seed under a different prompt keeps its motion (motion-course correlation 0.59–0.73), and a different seed does not (0.09–0.34). For the pendulum's log period, the seed explains η² = 0.998 and the prompt 0.0001, including a prompt that says "the swing takes 1.2 s".
- **E4, one band of the noise from a second seed:** the slow-in-time 29% of the noise moves the clip 0.59 of the way to the donor's motion; the coarse spatial ~6% moves it 0.46; the fine bands 0.37–0.41 (#4962; replicated #5100).
- **E6/E7, noise from inverted real recordings:** see `e6/`, `e7/` and #5600, #5634, #6167.
