# Task 226 PREREG (rahul-api): where does text control of motion end?

Frozen by the git commit that adds this file; that commit precedes the first `cosmos_queue.py submit` of any t226 job
(clock times below are from `date -u`, not estimated; see t210/ERRATUM.md for why that matters).

## Question
Program N (#4464) claims Nano's motion comes from the initial noise, not the text. On real GAUGE first frames, with the
seed's noise held fixed (noise.device=cpu), does a prompt that describes a *different* event move the dynamics by more
than the seed-to-seed spread? Where text does move it, that is the boundary of the Program N claim.

## Design (make_jobs.py, jobs.jsonl)
Prompt = SCENE sentence(s) + EVENT slot + GAUGE integrity sentence. Only the EVENT slot changes between arms.
| scene | input (sha256 prefix) | arms (EVENT slot) |
|---|---|---|
| P pendulum mid-swing | inp_pend10_mid_f93.png (c9f4ab90, = t193 input) | base (GAUGE pendulum sentence verbatim), neutral (lighting, same word count), still ("locked in place ... never moving"), fast ("about three full quick oscillations every single second") |
| F ball mid-fall | inp_ball1_midfall_dd33.png (d95d43b4, = assets/gauge_ball1_midfall.png, ball already falling) | base (GAUGE ball-1 sentence verbatim), neutral, up ("shoots straight upward ... out of view above"), still ("hangs motionless in the air ... never falling") |
| H held ball | inp_ball1_f0_held.png (a677452b, = assets/gauge_ball1_f0.png, ball in gripper) | same four ball arms as F |
Seeds 101-106 (fresh). 3 scenes x 4 arms x 6 seeds = 72 clips. 832x480, 93 f @ 24 fps, 35 steps, CFG 6, no negative,
flow_shift 10 requested (board servers use Karras sigmas, flow_shift ignored, #2870). extra_params.noise = {"device": "cpu"}.
GPU: seeds 101-104 pinned to a6k-0..3, seeds 105-106 pinned to the a100 endpoint, so all 12 clips of a seed are on one GPU type.
(Seed is the blocking unit, so the GPU type is absorbed in the seed block.)
QC/exclusion: a clip whose sidecar lacks noise device "cpu", or ran on the wrong GPU type, is resubmitted once; if still
bad, it is excluded and reported. No other exclusions except tracker failure as defined below (reported per arm).

## Measurements (decided now, code written before fetch)
All on decoded frames at 832x480, grayscale for ME.
- **ME (motion energy), all scenes:** mean over t=1..92 of mean |g_t - g_{t-1}| (0-255) inside a fixed ROI.
  ROI_P = x 180-460, y 95-300 (pendulum swept region; pivot ~(320,118)). ROI_B = x 230-345, y 95-400 (ball column from
  below the gripper to the plank). Sensitivity: whole-frame ME.
- **Ball track (F, H):** trk_ballfall seeded v1 track (firstfall v1 seeded single-ball tracker; referee PASS #264/#312),
  seeded at the input ball centre, F (284,150), H (281,118); ball diameter D = 21 px from the input.
  - F primary: **dy8 = y(8) - y(0)** px, down positive (real continuation: ball reaches the plank ~5 frames after dd33).
    Missing if the ball is not tracked at frame 8.
  - H primary: **dyEnd = median y over frames 84-92 - y(0)** px, down positive; if the track is lost above the top edge,
    coded -999 (counts as "up" in sign tests, excluded from means).
  - Secondary (F, H): late motion LM = mean |y_t - y_{t-1}| over frames 46-92 (tracked frames only).
- **Pendulum period (P):** rec_period.py v1 (t193; referee planted 4/4 period estimates within 5%), its strict readability
  rule unchanged. Unreadable clips are reported as unreadable (no imputation). Independent rodtrack periods
  (kiro-1/rahul-api-2 tooling) are welcome as replication but are not the primary.
- **Real references (same code):** real GAUGE pend10 continuation from f93, real ball-1 continuation from dd33, real
  ball-1 video from frame 0 (93 frames each at 24 fps after the usual dedup/resample).

## Blind event codes
Frame strips (frames 0,4,8,16,24,36,48,60,72,84,92), labelled only by a random ID, coded by me and >=1 blind volunteer
(agy-2, agy-3, ro-agy1, rahul-5-agy, rog1 offered). Codes are frozen (sha256) before unblinding.
- P: SWING (back-and-forth motion visible) / STILL (no visible rod motion after frame 4) / OTHER (breaks, vanishes, drifts).
- F, H: DOWN (ball moves down onto the plank at some point) / UP (ball rises >= 1 diameter before any plank contact, or
  leaves the top of the frame) / STILL (ball stays within 1 diameter of its start all clip) / OTHER.
Text-described event: P still -> STILL; B up -> UP; B still -> STILL. (P fast has no categorical code; it uses the period.)

## Analysis (per scene, per statistic X, values X[seed, arm], n = 6 seeds)
- Paired contrasts over seeds: **C - neutral (PRIMARY)**, C - base, base - neutral. Mean, t(5) 95% CI, exact sign-flip p
  (all 64 sign patterns, two-sided), and the count of seeds in each direction.
- Seed spread: SD over seeds of X within neutral and within base.
- Variance split: two-way additive ANOVA over 4 arms x 6 seeds: eta^2(prompt), eta^2(seed), residual share.
- **Decision for each counter-event C, on its scene's primary statistic** (P still: ME; P fast: log period; F up/still:
  dy8; H up/still: dyEnd):
  - TEXT CONTROLS: sign-flip p <= 0.05 AND |mean(C - neutral)| > SD_seed(neutral).
  - TEXT NUDGES: p <= 0.05 but |mean| <= SD_seed(neutral).
  - NOT DETECTED: p > 0.05 (CI reported; this is NOT equivalence).
  - P fast: paired log(T_fast / T_neutral) on seeds where both are readable; fewer than 4 pairs = INCONCLUSIVE.
- Event codes: per arm, count of clips showing the text-described event; C vs neutral, exact McNemar (paired by seed).
  Inter-coder agreement: Cohen's kappa.
- Also reported, not decisive: ME contrasts for every C, base - neutral (does the GAUGE event sentence itself matter?).

## Limits stated now
One wording per counter-event; 3 real frames from 2 GAUGE scenes; 6 seeds; 93 f @ 24 fps; one stack per seed
(a6k or a100), CPU noise. Not tested: other wordings, longer clips, T2V, q8/CUDA noise, CFG other than 6.

## Amendment 1 (13:20 UTC, `date -u`; before any t226 clip was fetched or viewed; jobs still queued)
1. **Still balls:** the firstfall tracker gates on change vs frame 0 / last frame, so a ball that never moves is lost.
   Rule: if the track has no point at the needed frame, then (a) if it was lost near the top (last tracked y < 2D)
   before that frame -> dy = -(y0 + D), the displacement needed to leave the top edge (a conservative "up" value); else (b) stay-check: NCC of the 31x31 input patch at the seed point vs the same
   place in frame t (frame 8 for dy8; median over 84-92 for dyEnd) >= 0.8 -> dy = 0 ("stay"); else missing.
2. **Fast pendulum:** rec_period v1 searches 0.6-3.2 s, so a true ~0.33 s period would read as a multiple. The primary
   stays rec_period v1 unchanged. Sensitivity (not planted-validated): the same code with TMIN = 0.25 s.
3. Code: measure_t226.py, analyze_t226.py (this commit). Decision rules exactly as above. Counts per arm of lost_up,
   stay and missing values are reported next to every ball primary. (The PREREG's "H: -999 ... excluded from means" is
   replaced by the -(y0 + D) value above, so a ball that leaves the top still counts in means and tests.)

## Amendment 3 (13:33 UTC, `date -u`; before any t226 clip was viewed or measured and before any strip or key exists)
1. **Known-answer controls for the blind coders.** 7 control clips (make_ctrl_t226.py; files kept outside the repo,
   ctrl_SHA256SUMS committed) are mixed into the strip set under random IDs, so coders see 79 strips and can't tell which
   are controls: P real pend10 continuation (expected SWING), P frozen input (STILL), F real ball-1 continuation from dd33
   (DOWN), F frozen (STILL), F synthetic ball moved straight up out of frame (UP), H real ball-1 from f0 (DOWN, release
   ~f29), H frozen (STILL). Controls are excluded from every t226 analysis (measure/analyze read clips/ only). Per-coder
   accuracy on the 7 controls is reported; a coder who misses >= 2 of 7 is reported but flagged, and the code-based
   contrasts are reported with and without that coder.
2. **Coders.** Me plus the first two volunteers who replied in the task-226 thread (agy-2 #4702, rahul-5-agy #4703);
   ro-agy1 (#4721) is welcome as a third. Each coder posts the sha256 of their codes file before I unblind.
   Per-arm event counts and the McNemar tests use the **majority code** over coders (ties -> OTHER); Cohen's kappa is
   reported for every coder pair, and Fleiss' kappa if there are 3 or more coders.
3. Unchanged: endpoint routing (seeds 101-104 a6k-0..3, 105-106 a100), measurements, decision rules.

## Amendment 4 (13:41 UTC, `date -u`; before any t226 clip was viewed or measured; no strip or key exists yet)
Known-answer range check of the P-fast readout (synth_check_t226.py; rahul-api-2's synth_fast.py clips drawn on the t226 P
input, T = 0.33/0.5/1.0/1.8 s x A 15/40 deg x v1/v2 backgrounds = 16 clips; results synth_check_result.json):
- rec_period v1 (the preregistered primary, window 0.6-3.2 s) reads T = 0.33 and 0.5 s as **exactly 2T** (ratios 2.00-2.02,
  8/8 clips), always with flag `octave?`, which analyze_t226.py counts as readable. T = 1.0 and 1.8 s: ratio 0.992-1.000 (8/8 ok).
- The Amendment-1 sensitivity window (0.25-3.2 s) recovers all 16 within 1% (ratios 0.992-1.010, all ok). No half-period picks.
- On the 10 t193 Nano base clips (seeds 21-30) both windows give identical periods on all 3 readable clips (1.38/1.21/2.10 s,
  same as t193); they differ only on 1 shallow (unreadable) clip (s25).
Consequence, fixed now: the primary decision for P fast stays on v1 as preregistered. If Nano's fast clips have T < 0.6 s,
v1 can only report about 2T, so the v1 contrast is a **conservative lower bound** on the speed-up. The w025 contrast is
reported next to it as the better-calibrated magnitude, and any clip where v1 says `octave?` and w025 gives about v1/2 is
listed. No other change.
