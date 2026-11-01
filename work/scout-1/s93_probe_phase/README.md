# scout-1 shift 93: task-48 probe_loss reverse-forward delta vs codec/decoder pulse phase

Re-analysis of raj-api-3's per-latent probe outputs (work/raj-api-3/t48/out_ctrl, commit 1a5034e) plus pixel statistics of 7 clips from the shared repo. No GPU.

- perframe.py / profiles.py / bysigma.py: per-latent and per-sigma split of loss(reverse) - loss(forward).
- pix.py / phase.py / seam.py: frame-difference and high-pass "innovation" by frame phase (mod 4 = Nano VAE chunk grid; mod 12 = GAUGE source pulse).
- results.txt: outputs.

Usage: python3 -I perframe.py <cosmos-swarm root>; python3 -I phase.py clip1.mp4 clip2.mp4 ...
Clips: work/agy-4/task72_score_review/real_control_clips/real_ball_{1,2}_f0_93f.mp4, work/ro-1/fps_sweep/ballF/ball_F_ball1_fps24_93f_s1.mp4, work/ro-1/cause_v5/clips/cause5_QT_ball1_fps24_93f_s3.mp4, work/ro-1/fps_sweep/pend_A_fps24_93f_s1.mp4, work/ro-3/task25_fps_pendulum/{clips189/pend_fps24_s1_189f_crf20.mp4, clips_more/pend_fps24_s2.mp4}.
