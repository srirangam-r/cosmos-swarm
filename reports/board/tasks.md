# Task list from the message board

| # | status | title |
|---|---|---|
| 1 | completed | Free-fall/pendulum measurement tool that passes the referee's planted cases |
| 2 | open | Cosmos3-Nano I2V running locally on the 5090 (24GB, offload) for GAUGE-style prompt/setting sweeps |
| 3 | completed | What exact settings/prompts did GAUGE use for Nano (fps, frames, neg prompt), so our sweeps match? |
| 4 | open | NVIDIA-scoreboard harness: DOVER + VBench dynamic degree, CPU-runnable, with seed-noise baseline on real dev clips |
| 5 | open | Robot-clip prediction harness: held-out DROID/Bridge clips + scorer for Nano action-conditioned forward dynamics (NVIDIA scoreboard item 4) |
| 6 | open | Cosmos-ready ball-drop measurer: single-clip CLI with free onset time, bootstrap CI and R², re-validated on planted |
| 7 | completed | Do the planted-passing trackers recover g≈9.81 on real PISA drop videos (real-footage validation)? |
| 8 | completed | Does a planted-passing pendulum-period tool recover the mocap period on real GAUGE pendulum video at Cosmos resolution? |
| 9 | completed | Does Nano stretch the prompted events to fill the clip? Measured ball g vs clip duration (num_frames 61/93/189) |
| 10 | completed | Plausibility-judge harness (NVIDIA scoreboard item 3): Cosmos-HUE questions + a fixed local VLM judge, with judge-noise and corruption controls |
| 11 | completed | Synthetic real-g ball-drop/bounce training set (+ wrong-g control set) in vision_sft_nano JSONL format, for a LoRA fix |
| 12 | completed | Independent replication of the pendulum-period finding (msg 201): mocap 8 s period and video period at Cosmos resolution |
| 13 | completed | Is Nano's slow plastic-slope slide (GAUGE 0.58 vs real 2.57 m/s²) caused by GAUGE's released plastic slope prompt being the turntable prompt? |
| 14 | completed | Independent replication of finding 159: real-GAUGE dynamic-degree reference with the original VBench code + RAFT-things checkpoint |
| 15 | completed | Is Nano's ball gravity slow once the release problem is removed? I2V from a real mid-fall frame (ball already let go) |
| 16 | completed | Independently check the GAUGE plastic slope prompt mismatch (finding 234) |
| 17 | completed | Independently test hover-induced bias in a ball-drop gravity fit (finding 116) |
| 18 | completed | Independently review the DROID frozen-frame prediction baseline (finding 121) |
| 19 | completed | Independently review GAUGE slope-video time base (finding 285) |
| 20 | completed | Third Cosmos3-Nano I2V endpoint on ro-rtx6000 GPU 1 (48 GB, no offload), same API as raj-1/GB10 servers |
| 21 | completed | Third Cosmos3-Nano endpoint on ro-rtx6000 GPU 1 (RTX 6000 Ada 48 GB, no offload) to cut the shared I2V queue |
| 22 | completed | Does the fps conditioning change Nano's motion speed? An fps sweep on GAUGE pendulum and mid-fall ball (a possible recipe fix) |
| 23 | completed | Independently test impact-frame bias in gravity fitting (finding 109) |
| 24 | completed | Run the sim_drop LoRA A/B (real-g vs wrong-g) on Cosmos3-Nano and measure g on GAUGE-style first frames |
| 25 | completed | Does the conditioned fps change Nano's pendulum period? (fps 12/24/48 sweep + duration-template-off arm, GAUGE official pendulum frame) |
| 26 | completed | Independently test median-background ghosts in slope tracking (review 338) |
| 27 | completed | Does the NVIDIA scoreboard comparison handle paired seeds and uncertainty correctly? |
| 28 | completed | Does NVIDIA's documented I2V recipe (JSON caption with timed actions + official JSON negative, templates off) give Nano real ball-drop timing and release, vs the plain-text GAUGE prompt? |
| 29 | completed | Independent check of finding 369 (ro-2 pipeline audit): negative-prompt inverse templates, JSON prompt recipe, and whether NVIDIA's reference I2V path uses the vision_encoder |
| 30 | completed | Make firstfall return a failure flag for short tracks |
| 31 | completed | Does NVIDIA's reference CFG negative (cosmos-framework JSON negative + SAME metadata) change Nano's ball fall/release vs the swarm default ("" + INVERSE metadata)? |
| 32 | completed | Independently verify the robot input resize and its baseline impact (finding 420) |
| 33 | completed | Independently review the plausibility judge's temporal corruption results (finding 441) |
| 34 | completed | Independently check the single-clip rebound gravity in finding 476 |
| 35 | completed | Independent replication of Nano's constant-velocity slope glide (finding 434) with an independent tracker and kinematic fit |
| 36 | completed | Bounce-decay measurer (multi-bounce restitution from flight-time ratios, time-to-rest), validated on synthetic multi-bounce clips + planted g/e |
| 37 | completed | Independent check of pendulum clip-length dependence in finding 525 |
| 38 | completed | Independent replication of pend_acf validation and Nano pendulum period scaling (finding 525) |
| 39 | completed | Independently check persistent bouncing in the mid-fall Nano clip |
| 40 | completed | Independently check ball-2 bounce timing in finding 564 |
| 41 | completed | Independently check long-run restitution in finding 612 |
| 42 | completed | Does chaining short Nano clips improve bounce decay over a single long clip? |
| 43 | completed | Does a 2-step Nano sample release the held ball more often than the matched 35-step sample? |
| 44 | completed | Does reducing inference steps (PhaseLock 2/4/8/15 vs 35) or CFG enable Nano to release held objects from GAUGE frame 0? |
| 45 | completed | Which fps channel sets Nano's motion speed: RoPE temporal spacing or the "N FPS" text? (decoupled 2x2 + RoPE-extrapolation arm) |
| 46 | completed | Independent replication of Nano's seed-robust slope speed ceiling (finding 766) and mid-fall ball rebound g / zero-damping (finding 698) |
| 47 | completed | Independently audit the bounce-decay tracker failure in review 870 |
| 48 | completed | Does Nano's own denoising loss prefer forward over time-reversed real decaying-bounce clips (arrow-of-time / LikePhys-style probe)? |
| 49 | completed | Independent replication and review of bounce_decay (finding 600), seed-2 mid-fall ball cycle/tether (finding 674), and 8B/32f HUE judge temporal blindness (finding 601) |
| 50 | open | Does restricting CFG to a noise interval (vLLM-Omni guidance_interval) change Nano's held-ball release? |
| 51 | completed | Does a Nano VAE encode-decode round trip preserve the bounce decay (e_T) of real GAUGE bounce clips? |
| 52 | completed | Does Nano's bounce decay (e_T) depend on impact speed? |
| 53 | completed | Does Nano's bounce restitution and held-ball release hold across seeds 1-4? (19-clip A100 multi-seed evaluation) |
| 54 | completed | Independent replication and review of Finding 550 (pendulum duration-template ablation) and Finding 621 (pendulum period across clip lengths & seeds) |
| 55 | completed | Independent review of HUE baseline seed-noise threshold in finding 1178 |
| 56 | completed | Independent replication and review of Finding 1188 (slope slide-speed ceiling across CFG, fps12, 189f, and materials) |
| 57 | completed | Does the negative-prompt motion finding survive matched-unit analysis? |
| 58 | completed | Independent replication and review of Finding 1172 (multi-seed bounce restitution e_T, held-ball release modes, and pendulum period on Brev A100 clips) |
| 59 | completed | Does a scene-specific negative prompt that describes the undamped bounce lower Nano's bounce decay ratio e_T? |
| 60 | completed | Does multi-frame (video-to-video) conditioning on a real bounce change Nano's bounce decay e_T compared with I2V from the same last frame? |
| 61 | completed | Independent replication and review of Finding 1175 (negative metadata SAME vs INVERSE and JSON quality negative on held-ball dynamics) |
| 62 | completed | Independent replication and review of Finding 1283 (bounce restitution e_T vs impact velocity ladder and low-drop levitation) |
| 63 | completed | Independent review of Task 50 CFG noise-interval pilot: quantitative multi-ROI tracking, object identity, and phantom cloning audit on GAUGE held ball |
| 64 | completed | Independent replication and review of Finding 1373 (Wan2.2 VAE round-trip preservation of bounce decay and impact timing) |
| 65 | completed | Independent replication and review of Finding 1373 (Wan2.2 VAE round-trip preservation of bounce decay on real GAUGE clips) |
| 66 | completed | Independent replication and review of Finding 1448 (fps conditioning parameter and text channel on Nano dynamics) |
| 67 | completed | Does the VAE round-trip evidence establish a DiT-only cause of bounce failure? |
| 68 | completed | NVIDIA scoreboard before/after evaluation: DOVER visual quality and dynamic degree on GAUGE ball (held baseline vs mid-fall release recipe, seeds 1-4) |
| 69 | completed | Independent blind evaluation of Task 24 LoRA eval clips (release rate, first-fall g, restitution e_T, and time-to-rest across 66 blinded clips) |
| 70 | completed | Deliverable 2: What was wrong and why (authoritative synthesis of replicated findings, numbers, uncertainties, controls, and evidence links) |
| 71 | completed | Does guidance scale (CFG) or flow shift control Nano's undamped bounce (e_T) and allow settling to rest? |
| 72 | completed | Independent review and replication of Finding 1616: planted-validated g on all 16 A100 clips, real-video f0 vs f33 DOVER/DD input control, and MC metric resolution |
| 73 | completed | Response to rog-cc challenge on Finding 1616: referee-validated firstfall g on 16 clips, DOVER input control, and MC penalty correction |
| 74 | completed | Revise Deliverable 2 report with qualified VAE bounds and Task 24 LoRA sim-to-real negative result (Finding 1661) |
| 75 | completed | Does task 71's bounce-decay finding use a planted-validated successive-flight estimator? |
| 76 | completed | Deliverable 1: The Improved Cosmos3-Nano Recipe (Dynamic Mid-Event Conditioning, Exact Runnable Instructions, and Replication Harness) |
| 77 | completed | Deliverable 1: The Improved Nano Recipe (Exact Instructions to Reproduce) |
| 78 | completed | Deliverable 3: Before/After on Both Scoreboards (Physics Scoreboard & NVIDIA Scoreboard Dev Sets Synthesis) |
| 79 | completed | Does the mid-event recipe demonstrate DOVER non-inferiority on fixed inputs? |
| 80 | completed | Deliverable 3: Before/After on Both Scoreboards (Physics and NVIDIA Benchmarks with Seed-Noise Baselines and Controls) |
| 81 | completed | Master Deliverables Portal: Root README.md and Scoreboard Qualification Harmonization |
| 82 | completed | Can the published detached-state recipe be reproduced end to end? |
| 83 | completed | Harmonize Deliverable 1 reports and qualify kinematic and scoreboard claims |
| 84 | completed | Harmonize Deliverable 1 into a single authoritative report and tool, qualifying physical fits and DOVER bounds |
| 85 | completed | Does firstfall actually force zero initial velocity in the reported mid-fall fits? |
| 86 | completed | Independent replication and review of Finding 1661: Task 24 blinded LoRA eval clips (release rate, gripper retention, phantom cloning, and resting state) |
| 87 | completed | Fix recipe reproducibility blockers (Task 82 audit), provide assets, and correct kinematic/DOVER attributions (#1843, #1846, #1856) |
| 88 | completed | Integrate empirical PREREG A3 plausibility judge results into Deliverable 3 and incorporate sampler findings into Deliverable 2 |
| 89 | completed | Do detached-state recipe clips preserve ball identity and plausible motion throughout? |
| 90 | completed | Does scaling RoPE spatial (height/width) frequencies by 0.7 in early denoising steps break the frame-0 held-ball release deadlock? |
| 91 | open | Does scaling RoPE spatial frequencies by 0.7 in early denoising steps enable held-ball release from frame 0? (arXiv 2609.23658) |
| 92 | completed | Does editing Nano's temporal RoPE frequencies (RIFLEx-style) change bounce decay on mid-fall GAUGE inputs? |
| 93 | completed | Harmonize Deliverable 3 & Master README with complete peer review qualifications (#1843, #1847, #1856, #1871, #1882, #1930) and architectural contact-transition synthesis (#1950) |
| 94 | completed | Integrate 3-draw DOVER/DD re-score (rog-cc Finding #2012) and seed cluster sensitivity into Deliverable 3 & README |
| 95 | completed | Harmonize Deliverable 1, 3 & Master README with SNF-Bench Dynamic Degree decomposition (scout-1 #2094), 3-draw DOVER matrix, and complete DROID status |
| 96 | completed | Does the reported robot prediction score test the final conditioning recipe? |
| 97 | completed | Does Nano's bounce decay depend on the surface or the ball? (surface/object swap; image-vs-text material cue) |
| 98 | completed | Does noising Nano's I2V conditioning frame (condition-noise, arXiv 2406.15735) let the held ball release from GAUGE frame 0? |
| 99 | completed | Does starting Nano mid-swing (real GAUGE pendulum frame, bob at the bottom with motion blur) give a closer-to-real period than starting at release from rest? |
| 100 | completed | Address rog-cc Peer Review #2238 & ro-1 Refutation #2211 across Master README and Deliverables 1-3 |
| 101 | completed | Does the fast05 temporal-RoPE damping (#2239) hold on fresh seeds, and is the j=0 pair alone enough (dose 0.25/0.5)? |
| 102 | completed | Integrate same-box baseL HUE judge (#2350) and cross-domain pendulum release (#2361) into Deliverables 1-3 & README |
| 103 | completed | Independent replication and review of Finding 2402: RoPE spatial scaling 0.7x on GAUGE held ball |
| 104 | completed | Independent replication and review of Finding 2407: Chaining short I2V clips vs long control and seam kinematics |
| 105 | completed | Harmonize Deliverables 1-3 & Master README with event-script pendulum (#2432), chained I2V (#2407), and temporal RoPE fast05 (#2396, #2419) |
| 106 | completed | Independent replication and review of Finding 2460: Prompt timing clause for bounce settling |
| 107 | completed | Does early-step low-pass of the conditioning latent (ALG, arXiv 2506.08456) release the pendulum from the rest frame? |
| 108 | completed | Does timed-settle text generalize to an independent real-photo drop scene? |
| 109 | completed | Independent replication and review of Finding 2432: Pendulum event-script prompting vs mid-swing start and geometric distortion |
| 110 | completed | Independent replication of Finding 2475/2499 (condition-noise) and test of DiT token quantization (scout-1 #2519) on phantom ball diameters |
| 111 | completed | Integrate prompt-timed settling clause (#2460, #2553) and complete 5-arm LoRA scoreboard (#2562) into Deliverables 1-3 & README |
| 112 | completed | Integrate Prompt-Timed Settling (#2460, #2553, #2577) & Audit Corrections (#2493, #2562, #2575) into Deliverables 1-3 & README |
| 113 | completed | Is the QT timed-settle HUE-judge drop (#2577) a question-set artifact? Predeclared mid-fall question set + truncation/static controls |
| 114 | completed | Does the timed-settle clause (#2460) still hold the ball at rest over 189 frames (7.9 s), on fresh GAUGE recordings? |
| 115 | completed | Under mid-swing conditioning, does a timed period clause set Nano's pendulum period (1.2 s vs wrong 2.5 s)? |
| 116 | completed | Independent replication and review of Finding 2622: Temporal RoPE fast05 multi-seed evaluation (s4-7 vs s1-3, settle rate, energy dissipation, and tracker survivorship) |
| 117 | completed | Independent replication and review of Finding 2562: 5-arm Task 24 LoRA scoreboard on HUE T2V and DOVER/DD |
| 118 | completed | Independent replication and review of Finding 2668: HUE judge window split (early f0-35 vs late f46-92) on timed-settle prompt QT |
| 119 | completed | Integrate replicated LoRA robot collapse (Review #2697), RoPE null (#2687), and HUE windowed split (#2668) into Deliverables 1-3 |
| 120 | completed | Independent replication and review of Finding 2720: Recipe prompt timed-settle clause (RECT vs REC, settle rate, artifact suppression, and scoreboard impact) |
| 121 | completed | Independent replication and review of Finding 2720: Timed-settle clause on Deliverable 1 recipe prompt (RECT vs REC) |
| 122 | completed | Harmonize Deliverables 1–3 with v7 recipe test (#2720), blind replication (#2726), windowed HUE audit (#2731), and fix run_recipe prompt substitution |
| 123 | completed | Independent replication and review of Finding 2577: Full-clip HUE plausibility judge on prompt-timed settling (QT vs F, category breakdown, distance-to-real, QS control) |
| 124 | completed | Fix recipe sidecar stage_2 flag and clarify default prompt vs Stage 1 baseline (rog-cc audit #2775) |
| 125 | completed | Fix run_recipe sidecar stage_2 metadata detection, add DEFAULT_PROMPT_REC constant, and expand test suite (#2775) |
| 126 | completed | Harmonize Deliverables 1–3 & README with full-clip HUE replication (#2802), recipe settle replications (#2753, #2769), and Two-Stage CLI docs |
| 127 | completed | Does weakening attention to the conditioning frame (conditioning.attention_scale) free the held ball from frame 0? |
| 128 | completed | Is there an activation direction for 'settle' or 'release' that changes Nano's dynamics without changing the prompt? (capture + steer) |
| 129 | completed | Empirical test of Scout-1 hypotheses: Mode interpolation vs motion demand on artifacts (#2814) & ball2 dd33 settling (#2781) |
| 130 | completed | Deliverable harmonization for Task 113 HUE audit (#2885), Task 48 Arrow-of-Time, and tools/bounce_decay staging |
| 131 | completed | Does an end-state sentence make Nano release the held ball from frame 0? (Raj #2930 open question) |
| 132 | completed | Harmonize Deliverables 1-3 & README: rog-cc ratio/RoPE audits (#2905, #2943), poornima-1 189f challenge (#2925), raj-api-3 T48 control (#2952) |
| 133 | open | Does the recipe's end-state rule, as a generic sentence appended to unseen HUE T2V prompts, regress NVIDIA's scoreboard (HUE judge, DOVER, DD)? |
| 134 | completed | Does the task-48 probe_loss reverse−forward sign flip when the clip start is shifted by 1–3 frames? |
| 135 | completed | Harmonize Deliverables 1-3 & recipe runner with Raj #2930 requirements: generic end-state rule R, frame-0 user specification, sampler documentation, and test suite |
| 136 | completed | Does Rule R (generic end-state sentence) bring non-ball objects to rest? Block/top/cart/disc T2V, base vs R vs length-matched neutral N, seeds 4-6, tracked tail-motion readout |
| 137 | completed | Does the settle clause still settle the mid-fall GAUGE ball without its bounce count ("bounces only twice")? Count-free clause and Rule R vs QT vs F |
| 138 | completed | Generate Task 137 QT-component ablation clips on q8 |
| 139 | completed | Does Nano drop the GAUGE ball from frame 0 once the gripper is painted out of the image? (holder vs still-frame lock) |
| 140 | completed | Does the recipe generic Rule R cause dissipation and rest on GAUGE slope and pendulum dev scenes (Raj #2930 req. 8)? |
| 141 | completed | How much of Nano's physical outcome is fixed by the noise seed, versus the input image and the prompt? |
| 142 | completed | At which denoising step is Nano's outcome (settle, bounce, re-tether, phantom) committed? |
| 143 | completed | Does Nano's own loss prefer a real ball that comes to rest, or the same real frames retimed into a bounce that never decays? |
| 144 | completed | Why does Nano keep a held object held: missing velocity in a still frame, or the holder in the picture? |
| 145 | completed | Is there one "comes to rest" direction inside Nano that works across scenes, not just for the ball? |
| 146 | completed | Does the Rule R runner send a sealed-test-compliant frame-0 request in every supported mode? |
| 147 | completed | Does Finding 3009 refute conditioning dominance, or only uniform attention attenuation? |
| 148 | completed | Does a midpoint between two adjacent Nano-VAE latents of a real GAUGE fall decode as two faint balls rather than one ball in between? |
| 149 | completed | Does Task 131 support the claim that Nano almost always releases held balls under the plain prompt? |
| 150 | completed | Do Task 131's clean-drop codes establish prompt independence or seed templating? |
| 151 | completed | What does the artifact-aware evidence establish about clean held-ball release from frame 0? |
| 152 | completed | Does a Nano clip's overall playback speed (PhyFPS) predict the g measured on its ball? |
| 153 | completed | Can blinded native-video coding replicate task 136's object loss and spawn artifacts? |
| 154 | completed | Does Rule R settle the mid-fall GAUGE ball on fresh seeds, beyond a length-matched neutral sentence? (replication of #3316) |
| 155 | completed | Under Rule R, do non-ball objects actually come to rest in view, or does the stillness come from the object leaving or vanishing? |
| 156 | completed | Harmonize Deliverables 1-3 with Task 146 CLI contract, Task 139 holder resolution, Task 136 non-ball scope/artifacts, and Task 137 Mechanism P |
| 157 | completed | On GAUGE's held-ball frame, does Nano's clone rate rise with guidance scale while staying low with the robot removed? |
| 158 | completed | Does guidance strength (CFG 2/4/6/8) set the clone rate on the held-ball frame? (scout X vs MI/B, #3418) |
| 159 | completed | Independent blind native-video QC for task 145 steering transfer |
| 160 | completed | Does #3397's holder lock replicate on other GAUGE recordings, fresh seeds and an independent edit, and does a large edit that keeps the holder stay held? |
| 161 | completed | Harmonize Deliverables 1-3 with Task 154 non-replication (#3458), optical-flow endpoint caveats (#3495), Task 133 A2 HUE spawn/gone rates (#3480), and VAE latent-interpolation limits (Finding #3481) |
| 162 | completed | Inside one Nano clip, do the fall from rest and the rebound flights share one parabola curvature (one clock), or does each event run on its own clock? |
| 163 | completed | Are the latents Nano generates at vanish/faint-ball moments blends of their neighbours, or ball-free background? |
| 164 | completed | Harmonize Deliverables 1-3 & README with VAE vs clone guidance scope (#3573, #3547), pendulum stack confound (#3582), and referee PASS of oneclock (#3587) |
| 165 | completed | Do the frozen HUE non-inferiority conclusions survive independent reanalysis? |
| 166 | completed | Harmonize Deliverables 1-3 & README with Holder Recode #3652, HUE Reanalysis #3605/#3654, Softened Cause Claims #3648, Retracted Stack Attribution #3632, and Wood QC #3622 |
| 167 | completed | Does the chronometer failure on real GAUGE survive recording-clustered reanalysis? |
| 168 | completed | Do identical fresh jobs reproduce across two q8 endpoints? |
| 169 | completed | Harmonize Deliverables 1-3 with HUE Visual Integrity exploratory status (#3692, #3731), Chronometer same-recording reanalysis (#3726), and Steering vs Settling blind QC (#3669, #3687, #3712) |
| 170 | completed | Does the v12 settle steer act through late denoising steps only (late-only arm reproduces the all-steps late-motion drop, still with no rest)? |
| 171 | completed | Does the frame-0 proxy (VAE round trip) explain why t139's no-robot input falls while mine hovers? (#3767 caveat) |
| 172 | completed | Do task 140's saved measurements support its pendulum deadlock and slope runoff claims? |
| 173 | completed | Harmonize Deliverables 1-3 & README: steering settling calibration (#3790), t140 dev scene limits (#3810), holder hover/clones (#3767, #3801), and oneclock/t115/t168 readouts (#3782, #3793, #3815) |
| 174 | completed | Does input softness (blur) turn Nano's hover into a fall on a no-robot frame? (#3827 follow-up) |
| 175 | completed | Replicate #3810 with fresh seeds: does Rule R fail to bring GAUGE slope/pendulum objects to rest (seeds 4-7, q8 only)? |
| 176 | completed | Does the oneclock analysis support its conclusions about post-impact clock changes? |
| 177 | completed | Does an independent visual audit support the VAE midpoint-swap result (#3481)? |
| 178 | completed | Harmonize Deliverables 1-3 & README: Task 133 provenance (#3876/#3886/#3888), Task 140 motion audit (#3841/#3846), and Task 162 audit (#3855/#3874) |
| 179 | completed | Does attention attenuation actually refute conditioning-frame dominance (#3009)? |
| 180 | completed | Does a paired-seed and independent blind audit support the H100 CFG sweep (#3900)? |
| 181 | completed | Harmonize Deliverables 1-3 & README: Task 175 fresh-seed slope/pendulum replication & retraction (#3918/#3950/#3955), Task 170 late steering diagnostic (#3929), and cross-stack guidance clone refutation (#3900/#3932) |
| 182 | completed | What period does measure_pend (planted PASS) give on Nano's mid-swing GAUGE pendulum clips vs the real continuation? |
| 183 | completed | From existing frozen codes (t157, t158, t160): how much of the clone/fall/hold outcome does the seed fix, versus CFG and the image edit? |
| 184 | completed | Do native pendulum motion and fit eligibility support the mid-swing slow-clock estimate (#3984)? |
| 185 | completed | Does Nano's slow mid-swing pendulum period (#3984, ratio 1.54) hold on new seeds and a second real pendulum input at a different phase? |
| 186 | completed | Does independent paired-seed analysis support the claimed seed dominance in task 183? |
| 187 | completed | Do matched T2V artifact codes support Rule R vs neutral equivalence (#3480)? |
| 188 | completed | Harmonize Deliverables 1-3 & README: Task 180 CFG Audit (#3973/#3992), Task 179 Attention (#3972), Task 182/184 Pendulum (#3984/#4010), and Task 183 Seed Lottery (#3994) |
| 189 | completed | Does the mixed-stack late-motion analysis support a shared-noise effect (#4040)? |
| 190 | completed | Does the cross-stack seed-concordance contrast survive independent-stack uncertainty and missing labels? |
| 191 | completed | Do the Nano mid-swing pendulum periods (#3984/#4072) survive a quantitative rigidity check and a bob-angle tracker? |
| 192 | completed | Does independent native-video QC and paired uncertainty support the input-blur negative result (#4104)? |
| 193 | completed | Replicate #4072: is Nano's mid-swing pendulum period ~1.76x real on fresh seeds with a tracker-free estimator? |
| 194 | completed | Does the new rod-angle rigidity analysis support its selected-period claims (#4131)? |
| 195 | completed | Harmonize Deliverables 1–3 & README with Pendulum Rigidity (#4131/#4090), oneclock Close-Out (#4136), Velocity Cue Replication (#4097), and Blur Null (#4104) |
| 196 | completed | How much effect does the velocity-streak experiment actually exclude? |
| 197 | completed | Does independent blind coding support the timed-settle prompt effect in the q8 grid (#4181)? |
| 198 | completed | Do native fresh-seed pendulum videos support the rigidity eligibility claimed in #4165? |
| 199 | completed | Does the task-141 grid support ranking prompt effects above seed effects? |
| 200 | completed | Independent blind second coder for #4181 settle outcome (task 141 q8 grid END sheets) |
| 201 | completed | Is the t157 (H100) vs t158 (q8) same-seed lock gap (#4030) a coder artifact? Coder-free pixel check on the same clips |
| 202 | completed | Does seed concordant excess hold in the Task 141 q8 grid, and does prompt override seed dominance? (seedshare audit of #4181) |
| 203 | completed | Does the reported eight-clip Earth-gravity result follow from its cited evidence? |
| 204 | completed | Does NVIDIA's actual sampler (no Karras, shift 10) change pendulum mid-swing rigidity vs the board's Karras default? (matched, same GPU) |
| 205 | completed | Does swing amplitude (large-angle period stretch) explain Nano's 'slow' pendulum? Amplitude-corrected period ratio on existing tracks |
| 206 | completed | Is Nano's slow pendulum period explained by its own larger swing amplitude (large-angle period correction)? |
| 207 | completed | Harmonize Deliverables 1–3 & README: Author Corrections and Statistical Qualifications (#4138, #4146, #4163, #4175, #4184, #4190, #4192, #4246, #4259, #4272) |
| 208 | completed | Does Rule R's failure on GAUGE slope/pendulum (#3810, #3918; q8 Karras) also hold on NVIDIA's sampler (UniPC shift 10, H100)? |
| 209 | completed | Do native outcomes and hook provenance support the early rest-text window claim (#4263)? |
| 210 | completed | Does appending the D1 Rule R suffix degrade Nano's real-robot clip prediction (Bridge forward dynamics, base vs R vs N)? |
| 211 | open | Does the QT timed-settle clause still make the GAUGE ball settle under NVIDIA's sampler (no Karras, shift 10)? Matched nv vs kar on one endpoint |
| 212 | completed | Does Nano's slow pendulum period survive a swing-centred-on-vertical gate (G6), per rahul-api-2 #4312? |
| 213 | completed | Do rahul-api's slow t193 pendulum seeds (s24/s26/s30) swing wider? Amplitude-corrected period on the t193 clips |
| 214 | completed | Can the end-frame ball-width estimator overstate growth or hide misses? |
| 215 | completed | How robust is the QT settle-with-size result to missing sizes and stricter growth tolerances? |
| 216 | completed | Does the ball grow in every arm, and when? Per-frame ball diameter from an independent ball-following tracker on the task-141 q8 clips (review of #4350/#4372) |
| 217 | completed | Does the QT settle clause freeze the whole scene (robot, background) or only the ball? Regional late motion on the task-141 q8 grid |
| 218 | completed | Does Rule R's Bridge noninferiority survive seed and episode clustering? |
| 219 | completed | Does the large-angle correction independently reproduce the pendulum amplitude result, and what assumptions bound it? |
| 220 | open | Does a GENERIC timed rest sentence recover QT's settle effect? Minimal pair on the task-141 q8 grid: "Within about one and a half seconds, every object..." vs Rule R "By the end of the video, every object..." |
| 221 | completed | How sensitive is the pendulum amplitude correction to projection and off-vertical swing centers? |
| 222 | open | N1 (for codex-api-3): a validated automated 'still moving vs at rest at the end' classifier for GAUGE ball clips |
| 223 | open | N2 (for codex-api-4): pre-specified independent analysis of Program N (E0-E3) |
| 224 | open | N3 (for kiro-1): is Nano's slow pendulum a fixed time-scale error, or tied to clip length and fps? |
| 225 | open | N4 (for poornima-2 + poornima-3): does a seed bank work on contact events? |
| 226 | completed | N5 (for rahul-api + rahul-api-2): where does text control of motion end? |
| 227 | completed | Does the cited pendulum cycle-count comparison support Program N's seed-versus-text claim? |
| 228 | completed | Does Nano's pendulum period scale with rod length (T ∝ √L), or is it a fixed rhythm? Counterfactual shortened-rod first frames |
| 229 | completed | Independent pixel-level replication and metric verification of Task 210 robot forward dynamics clips |
| 230 | completed | Does the prompt settle clause freeze the whole scene or only the ball? Independent replication and review of Finding #4460 |
| 231 | completed | Independent replication and review of Finding #4505: Time to quiet on GAUGE mid-fall frames (real vs Nano, 2.6x delay, threshold sensitivity, and ball growth interaction) |
| 232 | completed | Independent review and replication of Finding #4569: Pendulum rod-shortening breakdown (Task 228) |
| 233 | completed | Independent replication and review of Finding #4569 (Pendulum rod length scaling T ∝ √L) |
| 234 | completed | Independent review of Program N classifier diagnostic #4637 |
| 235 | completed | Independent replication and review of Finding #4538: Artifact etiology (MI vs K vs B) and non-settling mechanisms (T vs A vs G) |
| 236 | completed | Does the Program N rest-candidate prototype (task 222) distinguish real GAUGE bouncing, rolling, and rest states on the known-answer pack (kap_real)? |
| 237 | completed | Independent review and replication of Finding #4577 and #4684: Bounce-decay validation, low-e cliff, and background ghost iteration |
| 238 | completed | Independent replication and review of Finding #4709: NVIDIA sampler schedule (non-Karras sigmas vs UniPC+Karras) on pendulum period, pixel fidelity, and kinematic rigidity |
| 239 | completed | With CPU noise, does the same seed give the same pendulum swing (period, phase) on a different GPU type? Replication of Raj #4786 (E0) on pend10 with t226 seeds |
| 240 | completed | Independent review of Program N dense-component diagnostic #4814 |
| 241 | completed | Independent review of Program N's blind synthetic coverage diagnostic #4856 |
| 242 | completed | Independent review of Program N seeded-tracker feasibility #4897 |
| 243 | completed | Independent review of Program N template-reset diagnostic #4939 |
| 244 | completed | Independent replication and review of Finding #4927: Full 16-seed E1 evaluation (pixel change proxy, referee-validated pendulum period, rigidity, and NVIDIA scoreboard on RTX 5090) |
| 245 | completed | Independent kinematic audit and blinded evaluation of Prompt-Switch v9 (Finding #4851 & #4956): does mid-window [7, 17] conditioning achieve physical settling? |
| 246 | completed | Independent review of multiscale tracker diagnostic #4975 |
| 247 | completed | Independent review of Program N seed-bank leakage diagnostic #4792 |
| 248 | completed | Independent blind coding and validation of Task 226 text-control strips across 79 randomized clips |
| 249 | completed | Independent replication and review of Finding #4962: Program N E4 noise component decomposition |
| 250 | open | Physics noise prior: does the coarse noise of inverted REAL recordings give Nano real physics on new frames (frozen model)? |
| 251 | open | Fine-tune so text or actions SET Nano's physics: LoRA on counterfactual pairs with an intervention-effect loss |
| 252 | completed | Port a training-free proxy or simulator method to Cosmos3-Nano and validate it against REAL ground truth (mocap) |
| 253 | open | Discovery: when during denoising does text lose control of MOTION, versus of APPEARANCE? |
| 254 | open | Discovery: does Nano internally encode the REQUESTED physics (speed, period) even though its output ignores it? Probe, then steer. |
| 255 | open | Action-conditioned Nano on the Bridge dev set: does the noise or the action decide the rollout, and what fixes it? |
| 256 | completed | Independent review and refutation of Finding #5116: HoughCircles dilation runaway divergence (d ~990px on 480p frames) and ball size audit |
| 257 | completed | Does a seed's pendulum period carry across different real pendulum frames? (analysis of Raj's finished E3 clips; seed-bank test, no new GPU) |
| 258 | completed | Run E6, the core experiment of task 250: does the coarse noise of inverted REAL pendulum recordings give Nano the real clock? (driver ready) |
| 259 | completed | Does the pendulum proxy result establish first-frame metric calibration, or supplied-period transfer? |
| 260 | completed | Does the pendulum seed-bank evidence support a reusable selection recipe? |
| 261 | completed | Does a stretched rod predict Nano's slow pendulum? Preregistered signed-stretch vs period test on fresh pend10 clips (no GPU) |
| 262 | completed | Do the counter-event results survive independent paired, coder and seed-cluster checks? |
| 263 | completed | Do the bounce-tool radius and sampling-limit explanations match the committed estimator? |
| 264 | claimed | DEMO: Phase-Noise physics transfer on Cosmos3-Nano (Phi-Noise style, no inversion) |
| 265 | open | DEMO: Physics speed dial: set Nano's pendulum period with a donor's coarse noise |
| 266 | failed | DEMO: Sim-proxy init beyond the pendulum: ball drop/bounce with real g on Nano |
| 267 | completed | DEMO: Gallery page of the swarm's physics fixes (no GPU) |
| 268 | completed | Does the nonlinear-amplitude correction establish an intrinsic Nano pendulum slowdown? |
| 269 | completed | Checked phase-only noise kernel and spectral-energy controls for the Nano demo |
| 270 | completed | Does skipping conditioning slot 0 isolate the E6 washout cause without changing the donor band? |
| 271 | completed | Finite-window phase-band controls for interpreting the Nano clock-transfer demo |
| 272 | open | Does real-video context (V2V, 1 vs 2 vs 3 conditioning latents) bring Nano's pendulum period closer to real and shrink its seed spread? |
| 273 | completed | BUILD: Nano-Phys, a training-free 'physics start' for Cosmos3-Nano that users can run from the repo |
| 274 | completed | Initial-state-correct pendulum phase helper for the Nano-Phys CLI |
| 275 | completed | Does the E7 shared-slot correction preserve the full noise covariance and matched controls? |
| 276 | claimed | Nano-Phys pendulum benchmark: plain vs Nano-Phys on 6 held-out GAUGE mid-swing frames x 3 seeds (README table) |
| 277 | open | Fresh-frame replication of5315 with an independent crossing-period readout |
| 278 | completed | Does the shipped Nano-Phys CLI reproduce its source experiment and support its benchmark claims? |
| 279 | completed | Demo gallery availability and playback smoke report from a second host |
| 280 | completed | Reviewable gallery presentation-label and paired-player correction patch |
| 281 | completed | DEMO: two placeholder clips, original vs improved Nano (for Rahul's talk) |
| 282 | completed | Source-matched native clip manifest and assembly handoff for Rahul's two placeholder demos |
| 283 | completed | Browser playback verification of the gallery's paired-player review patch |
| 284 | completed | Finite-frame impact-time bounds for task266's real-g vs half-g control |
| 285 | completed | Claim and reproducibility audit of Raj's regenerated demo a597e6f |
| 286 | completed | Delivery and browser playback evidence for Raj's two MP4/GIF demos |
| 287 | completed | Nonlinear pendulum trajectory candidate that preserves the proxy's explicit boundary state and period |
| 288 | completed | Standalone offline presentation page for the two published Nano demos |
| 289 | completed | CPU execution and planted validation of task277's independent crossing reader |
| 290 | completed | Repeated-measures analysis contract for the five-period Nano speed dial |
| 291 | completed | Native sidecar integration regression for Nano-Phys sigma selection |
| 292 | completed | Pinned first-frame input and geometry handoff for task277's two fresh scenes |
| 293 | completed | Deployed gallery integration smoke after native-demo and player adoption |
| 294 | completed | 277 input boundary-state review: do candidate image geometry and proxy start agree? |
| 295 | completed | Does f96be25 certify Nano-Phys native flow sigmas and executed-start provenance? |
| 296 | completed | Executable input/state acceptance package for task277's pinned scene images |
| 297 | completed | Runtime queue serialization and proxy attachment integration for Nano-Phys |
| 298 | completed | Executable six-pair report for the fresh-frame Nano proxy replication |
| 299 | completed | Live gallery acceptance after owner adoption of player and anchor fixes |
| 300 | completed | Rendered-proxy acceptance of pinned fresh-frame pendulum states |
| 301 | completed | Runtime publication of task290's frozen speed-dial analysis |
| 302 | completed | Preserve the original first frame in Nano-Phys analytical proxies |
| 303 | completed | Runtime acceptance of Nano-Phys native receipts and sigma input guards |
| 304 | completed | Independent review of corrected proxy boundary pixels and compositing acceptance |
| 305 | completed | Correct Nano-Phys demo benchmark labels to match native source and task status |
| 306 | completed | Correct gallery ball-demo labels after task266 failed measurement QC |
| 307 | completed | Independent acceptance of native schedule receipts and start-selector guards |
| 308 | completed | Independent threaded handler acceptance of request-local sampling receipts |
| 309 | completed | Does the sampler receipt snapshot remain request-owned under concurrent requests? |
| 310 | failed | 265 |
| 311 | failed | 266 |
| 312 | failed | 273 |
