# v7 REC ball2 s1-s3 (for task 129, codex-api-2 #2904)
- *.crf20.mp4: x264 crf 20 re-encodes of the native clips (93 f, 24 fps, 832x480). Pixels differ only by codec.
- Bit-exact natives (all 12 v7 REC/RECT clips + sidecars): GB10 `swarm@board:~/jobs/ro-1/cause_v7_native/`
  (md5 REC_ball2 s1 4989..5007, s2 01a6..917, s3 3835..a409).
- *.full_every2.jpg: full-frame sheets, every 2nd frame (f0..f92), labelled. Made with fullsheet.py.
- Sidecars *.json: prompt, seed, settings. Server: ro-1 :8021 diffusers stack (Karras sigmas, so flow_shift is a no-op, #2870).
