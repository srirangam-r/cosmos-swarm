# Task 103: Independent Replication & Review of Finding #2402 (Task 90)

## Target Finding (#2402 by ro-agy1)
- **Claim**: Scaling RoPE spatial frequencies by 0.7x during early denoising ($t \ge 900$) does not fix the frame-0 held-ball release deadlock on GAUGE Ball 1 (0/3 physical release vs 0/3 control), while increasing Dynamic Degree ($\Delta = +3.17$) without changing DOVER fused quality.

## Replication Summary & Findings
We performed an independent multi-modal evaluation of all 6 generated clips (`gauge_b1_ctrl_s1..s3.mp4` and `gauge_b1_rope07_s1..s3.mp4`) fetched from GB10:
1. **NVIDIA Scoreboard Replicated**:
   - **Dynamic Degree (RAFT)**: Control $3.02 \pm 1.28$ vs RoPE 0.7x $6.12 \pm 2.63$, Paired $\Delta = +3.10 \pm 1.35$. Confirms substantial increase in optical flow energy under early RoPE scaling.
   - **DOVER (reps=3)**: Control fused $0.4255 \pm 0.0226$ vs RoPE 0.7x $0.4281 \pm 0.0208$, Paired $\Delta = +0.0026 \pm 0.0159$ (n.s.). Technical quality $\Delta = +0.0027 \pm 0.0014$, aesthetic quality $\Delta = -0.0011 \pm 0.0054$.
2. **Kinematic & Referee Validation (`firstfall.py`)**:
   - All 6 clips yield `flag=weak` with non-physical fits ($R^2 < 0.98$ or artifact durations $< 0.15\text{ s}$). Zero clips exhibit true parabolic Newtonian free fall ($g = 9.81\text{ m/s}^2$).
3. **Flaws & Critical Caveats in Source Artifacts**:
   - **Photographic Negative Bug**: All 6 clips are inverted in pixel space ($255 - x$), with MAE to inverted frame 0 of $7.54$ vs $171.66$ to direct frame 0. Absolute DOVER scores were computed on inverted pixels.
   - **Arm Motion vs Held Ball**: The $y \approx 147$ trajectory tracked the robotic gripper descending and rising rather than a static pinned ball.
   - **Deformation vs Pinning**: Under both control and RoPE 0.7x, seeds 2 and 3 exhibit duplicate/phantom ball spawning or unphysical morphing rather than rigid grip retention. RoPE 0.7x exacerbates structural distortions (plank morphing and gripper disintegration).

## Artifacts in this Directory
- `replicate_task90_rope_scale.py`: Complete independent evaluation pipeline (RAFT Dynamic Degree, DOVER reps=3, multi-ROI tracking, referee kinematic fitting, contact sheets).
- `task103_rope_scale_review_results.json`: Complete statistical breakdown per clip and paired differences.
- `nv_scores_task103.json`: Raw scoreboard outputs.
- `sheets/`: Contact sheets comparing control vs treatment across seeds 1 to 3.
