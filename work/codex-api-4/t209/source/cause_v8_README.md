# v8: prompt-switch window probe (task 22; scout #2337a/#2549/#3912)
Base text = GAUGE F prompt. The conditional CFG pass uses the QT text ("bounces only twice ... comes to rest ... within about one and a half seconds, staying still") only for denoising steps lo<=i<hi of 35. Everything else is the same as cause_v5: ball1 dd33 mid-fall, 832x480, 93 f @ 24, 35 steps, cfg 6, no negative, ro-1 :8021 diffusers (UniPC + Karras sigmas, so flow_shift is a no-op).
Hook check: SWfull (0-35) is pixel-identical to cause5_QT at s3 and s5 (maxabs 0).
Approx. sigma_flow on the Karras grid: step0 .995, 3 .993, 7 .987, 10 .979, 17 .93, 25 .69, 34 .13.
Eye codes (UNBLINDED, coder ro-1, from strips/ every 3rd frame): eye_codes.csv. last20 = mean |dgrey| over the last 20 frames, corridor crop (analyze7.py).
v9 (jobs_v9.jsonl): seeds 1,2,4 for e3/e7/l7/l17 + a 7-17-only arm at seeds 1-5.
