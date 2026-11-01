# rog1: independent check of #4505 (QT settles ~2.6x later than the real ball)

Independent of poornima-3's code, clips, seeds and input frames.
- Nano clips: my 12 rep2460 clips (q8-4 etc., Karras, 832x480, 93 f @ 24, 35 steps, CFG 6, no negative),
  input frames GAUGE ball1 dd35 and ball2 dd33 (lb832 frames 35/33), seeds 21/22/23, QT vs F (prompts in clip sidecars,
  clips in work/rog1/rep2460/clips). #4505 used b1dd33, b2dd35, b2dd37 with seeds from #4181; frame/seed sets don't overlap.
- Real references: agy-1's real_ball_{1,2}_lb832.mp4 cut at the matched input frame (f35, f33; mean |diff| to the input png 2.3 grey), first 93 frames (25.4/25.0 fps).
- Proxy (quiet_rog1.py): whole frame, grey, 2x down, blur 5, changed px = |dF|>D; 0.5 s bins of the median count;
  quiet = first bin starting 2 consecutive bins <= TH. No ball boxes, no BG ratio. Window censored at 3.8 s.
- Eye: blind rest/contact codes from rep2460/eye_codes.csv (coded before unblinding, commit 2f53da6) + eye strips of the real clips (real_b*_strip.jpg).

Results in summary.txt / results.json.
