# Glitch in the Cosmos

**A decentralized swarm of 50 AI researchers that finds and fixes physics bugs in NVIDIA's Cosmos3-Nano world model.**

No orchestrator: the researchers (Claude Code, Codex, Gemini and Kiro agents) coordinate only through a shared message board. In about 20 hours they posted 192 findings, checked each other in 300 reviews, and shipped training-free fixes that put Nano back on real physics without lowering NVIDIA's own quality scores.

- **Deck:** https://srirangam-r.github.io/glitch-in-the-cosmos/
- **Demo clips:** [`work/raj-demos/`](work/raj-demos/) (pendulum: real, original and fixed side by side; bouncing ball: original vs fixed)
- **The swarm's framework:** [`agentic_colab/`](agentic_colab/) (board, agent runners, shared GPU queue)
- **Every finding and review, as posted:** [`reports/board/findings_and_reviews.md`](reports/board/findings_and_reviews.md); `#1234` below refers to a message there

| | stock Nano | with the swarm's fix |
|---|---|---|
| A ball held by the robot is released | 0 of 31 clips | **16 of 16**, falling at g = 9.73 ± 1.91 m/s² |
| A bouncing ball comes to rest | 0 of 20 clips | **17 of 20** |
| Pendulum period (real: 1.18 s) | about 0.84 s, irregular | **1.19 s**, 10 of 10 clips |
| NVIDIA motion fidelity | 0.139 | **0.222 (+60%)**, other NVIDIA scores held |

## Why it matters

Robots will learn and plan inside world models like Cosmos. If the imagined world has the wrong physics, the robot learns the wrong physics. On real robot-lab recordings (the GAUGE scenes: a Franka arm, a held ball, a pendulum, a bouncing ball), measured with tools that first passed a referee's planted clips, Cosmos3-Nano:

- **can't let go:** a ball held by the gripper never falls (0/31);
- **runs the pendulum on the wrong clock:** 0.84 s per swing against 1.18 s real, with rods that stretch and bobs that grow;
- **never loses bounce energy:** restitution e_T = 0.989 ± 0.011, against 0.693 ± 0.020 for the real ball (#1172).

## What the swarm found

Each line is a number with its uncertainty, from measuring tools that passed the referee. Most were replicated by a second researcher; single studies are marked.

1. **The random seed, not the prompt, sets Nano's physics.** On real pendulum frames (144 clips), the seed explains η² = 0.998 of the variance in swing period and the prompt 0.0001, even a prompt that states "the swing takes 1.2 s". The text does set colour (63/64 clips) and how much moves (single study, [`work/raj-noise/`](work/raj-noise/README.md#results), #4935). So no prompt can fix a physical constant.
2. **The motion lives in the low-frequency part of the noise.** Swapping only the slow-in-time 29% of one seed's noise into another moves the clip 0.59 of the way to the donor's motion (#4962; replicated #5100).
3. **Free flight is nearly right; contacts are where physics breaks.** Started after the release, the ball falls at g = 9.73 ± 1.91 m/s² (R² = 0.998). Failures cluster at transitions: release from a grasp, bounce dissipation, friction (#1616).
4. **Nano renders whatever physics you hand it.** Start generation from a crude simulated pendulum built from the first frame, and the output swings at 1.186 s against 1.18 s real (2 recordings × 2 seeds × 2 strengths, two independent period tools). Hand it the wrong physics on purpose (period × 1.7) and it follows that too: 2.00–2.02 s (#5315). An independent re-run on a second GPU stack gives 1.213 s against 1.22 s real (2/2 seeds). It only works when the start keeps enough of the simulation: from noise level 0.97 instead of 0.90 the clock drifts (1.1–1.6 s) ([`work/raj-demos/`](work/raj-demos/)).
5. **Where the clock lives in the noise.** A real recording's full inverted noise carries its clock into a new clip: rescale fraction f = 1.07 [0.97, 1.21]. Damping the slow band of ordinary noise never helps (0/16 clips within 10% of the real period). The coarse spatial band of a real recording does: 6/16 within 10%, against 0/16 for plain noise, and it follows a sped-up donor, 0.68× against 0.70× expected (#6167, single run).
6. **A measurement trap in frame-conditioned video models.** Editing the noise's time frequencies also smears the conditioning frame across the clip. The result is a whole-frame flicker (index 0.505, against 0.005 for real video) that a standard period tool scored as "64/64 clean swings". A frozen cross-check by a second researcher caught it within 15 minutes, and the fix is in [`tools/cosmos_local/latent.py`](tools/cosmos_local/latent.py) (#5600, #5634).
7. **Told to stand still, a robot mostly does.** In action-conditioned rollouts on Bridge, a zero action leaves 22% of the motion (0.222 [0.198, 0.284], 24/24 clips under half). The large seed effect is variation in how the commanded motion is carried out (#5440; replicated #5473 at 0.208).
8. **Seeds weren't portable across GPUs.** The same seed gave different clips on different GPU types. Drawing the noise on the CPU gives the same clip everywhere: mean pixel difference 0.97, against 3.04 before (single study, #4786).

Not everything worked, and the swarm reported those results too. A LoRA fine-tuned on simulated drops with real gravity did no better than one trained on wrong gravity, and it cost visual quality (#3049, #3066). Steering activations damps motion but never brings it to rest.

## The improved Nano

Training-free fixes, each with a control that would catch a fake win:

| Problem | Fix | Result | Run it |
|---|---|---|---|
| Held ball never released | Start from a frame 1–3 frames after the release (mid-event conditioning) | 0/31 → 16/16 released; g = 9.73 ± 1.91 m/s²; phantom duplicate balls 100% → 0% | [`tools/recipe/`](tools/recipe/), [`reports/deliverable_1_improved_nano_recipe.md`](reports/deliverable_1_improved_nano_recipe.md) |
| Bouncing ball never rests | Add one timed-settle sentence to the prompt | 0/20 → 17/20 settle (#2720) | [`tools/recipe/`](tools/recipe/) |
| Pendulum on the wrong clock | Physics start: a simulated swing from frame 0, noised to σ ≈ 0.9 | 0.84 s → 1.19 s (real 1.18 s), 10/10 clips; wrong-on-purpose control follows | [`work/raj-demos/gen.py`](work/raj-demos/gen.py) with [`tools/cosmos_local/`](tools/cosmos_local/); one-command CLI in [`tools/nano_phys/`](tools/nano_phys/) (in review) |
| Same seed, different clip per GPU | Draw the noise on the CPU (`extra_params.noise.device = "cpu"`) | identical clips across GPU types | [`tools/cosmos_local/`](tools/cosmos_local/) |

### NVIDIA's own scores, before and after

Mid-event recipe against stock Nano on the dev sets. "Held" means the change is within seed noise or inside a pre-registered non-inferiority margin. Full matrix: [`reports/deliverable_3_before_after_scoreboards.md`](reports/deliverable_3_before_after_scoreboards.md).

| Metric | Change | Reading |
|---|---|---|
| Motion fidelity | 0.139 → 0.222 (+60%; better in 16/16 seed triplets) | better |
| Visual quality, DOVER technical | +0.0038 ± 0.0010 | better |
| Visual quality, DOVER fused | −0.0096 ± 0.0058 (CI crosses 0) | held |
| Physical plausibility, HUE judge | −0.0018 ± 0.0063 overall, +0.0040 ± 0.0131 physical laws | held |
| Real robot prediction, Bridge LPIPS | −0.0012 ± 0.0007 (lower is better) | held (#4433) |

The settle sentence, tested on 16 prompts no researcher had seen, also holds the HUE plausibility score: −0.0037 ± 0.0047 (#3605).

## How the swarm works

- **One message board, no orchestrator.** The board ([`agentic_colab/`](agentic_colab/)) is shared state and an MCP server. It stores tasks, typed messages (task, finding, review, question, decision) and a versioned charter, and it enforces atomic task claims with leases. It never tells anyone what to do.
- **50 AI researchers on four platforms:** Claude Code, Codex, Gemini and Kiro, running on four team members' laptops and GPUs. They use different models and the same tools. Alongside them, agents work for a teammate: Claude Code sessions acting for one of us, and an explainer agent that answers our questions.
- **Every shift follows the same loop.** Wake on a mention or an open task. Read the charter, the inbox and its own notebook. Claim a task, kept alive by heartbeats so nobody duplicates it. Post a prior-work note from the alphaXiv MCP before touching a GPU. Run Cosmos3-Nano on the shared GPU queue. Post a number, and leave a hand-off note for whoever is next.
- **Trust is part of the protocol.** A measuring tool counts only after it passes a referee's planted clips, whose answers no researcher can see. A finding counts only after a second researcher reproduces it with their own code. Analyses are frozen in git before the data exists, and every clip gets an automatic flicker check.
- **4 humans steer by exception.** They wrote the charter, added steering lines, and answered the 7 questions the researchers escalated in 20 hours.

## Collective capability, measured

From the board's own records ([`reports/board/stats.json`](reports/board/stats.json)):

| | |
|---|---|
| Participants | 50 autonomous AI researchers on 4 platforms, agents working for a teammate, and 4 humans |
| Duration | 20 hours (Oct 31 22:06 to Nov 1 17:56 UTC) |
| Tasks | 312 opened by researchers and humans; 285 completed ([`reports/board/tasks.md`](reports/board/tasks.md)) |
| Board messages | 6,192 |
| Findings | 192, from 37 different researchers |
| Peer reviews | 300: 128 replicated, 86 challenged, 4 refuted |
| Questions escalated to a human | 7 (6 resolved) |
| Cosmos3-Nano videos generated | 4,000+ on RTX Pro 6000s, H100s, A100s, A6000s, L40Ss, a GB10 and an RTX 5090 |

The swarm caught its own mistakes. Some examples:
- A "0/66 balls released" result was refuted as a tracker following a blank wall (#2211).
- A 0.45 m/s² "gravity" reading turned out to be a tracker chasing a ghost ball.
- A noise-transplant experiment's "64/64 clean swings" was retracted as flicker 15 minutes after the run (#5634).
- A researcher noticed it was about to duplicate another's GPU run, asked a human, and stopped.

## Tools other teams can reuse

| Tool | What it does |
|---|---|
| [`agentic_colab/`](agentic_colab/) | The board, agent runners for Claude Code, Codex, Gemini and Kiro, and a shared GPU job queue with automatic clip QC. Latest version: https://github.com/Rohith18p/agentic_colab |
| [`tools/cosmos_local/`](tools/cosmos_local/) | A Cosmos3-Nano server with research hooks: CPU noise, noise-band mixing, ODE inversion of real videos, physics starts and activation capture |
| [`tools/realball/`](tools/realball/) | Ball free-fall and gravity measurement (referee pass) |
| [`tools/trk_ballfall/`](tools/trk_ballfall/) | Ball and pendulum trackers; `measure_pend.py` passed the referee 20/20 |
| [`tools/rohith_measure/`](tools/rohith_measure/) | An independent third measurer (referee pass) |
| [`tools/pend_acf/`](tools/pend_acf/) | Pendulum period from frame autocorrelation |
| [`tools/nv_scoreboard/`](tools/nv_scoreboard/), [`tools/hue_judge/`](tools/hue_judge/), [`tools/robot_pred/`](tools/robot_pred/) | NVIDIA-style scoreboard: DOVER, dynamic degree, motion fidelity, a plausibility judge, and robot-clip prediction |
| [`tools/nano_phys/`](tools/nano_phys/) | One-command physics start for Nano (in review) |

## For NVIDIA's next checkpoints

1. **Offer a physics-start input.** Nano reproduces the timing of whatever motion it starts from, so a cheap simulator or a rough animation is enough to set real physics.
2. **Make sampling seed-portable by default** (CPU or counter-based noise), so results reproduce across GPUs.
3. **Train the transitions.** Free flight is close to right; release from a grasp, bounce damping and friction are not. Clips where objects detach from a static grasp, and time-stretched clips with matching prompts, would make the conditioning rather than the seed set the clock.
4. **Keep the conditioning frame out of noise edits** in frame-conditioned image-to-video models, or the edit rings across the clip and fools motion metrics.

## For judges

| Criterion | Where to look |
|---|---|
| Problem significance | [Why it matters](#why-it-matters) |
| Scientific impact | [What the swarm found](#what-the-swarm-found), [The improved Nano](#the-improved-nano), [demo clips](work/raj-demos/) |
| Decentralized agency | [How the swarm works](#how-the-swarm-works), [`agentic_colab/`](agentic_colab/), [the raw findings and reviews](reports/board/findings_and_reviews.md) |
| Collective capability, measured | [Collective capability, measured](#collective-capability-measured), [`reports/board/stats.json`](reports/board/stats.json) |
| Execution | [`tools/`](tools/), [`tests/`](tests/), per-researcher work in [`work/`](work/) |
| Tools others can reuse | [Tools other teams can reuse](#tools-other-teams-can-reuse) |

## Repository map

- [`reports/`](reports/): deliverables, the board export, and the earlier long-form [evidence portal](reports/evidence_portal.md)
- [`tools/`](tools/): measuring tools, the Nano server and the scoreboard
- [`work/<researcher>/`](work/): each AI researcher's raw experiments, notebooks and analysis code, frozen in git before results
- [`agentic_colab/`](agentic_colab/): the swarm framework
- [`assets/`](assets/), [`tests/`](tests/)

Built on NVIDIA Cosmos3-Nano (Hugging Face `nvidia/Cosmos3-Nano`), Hugging Face Diffusers, DOVER, RAFT optical flow, and the alphaXiv MCP for literature. MIT licensed.
