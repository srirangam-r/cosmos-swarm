# rog1 blind replication of ro-1 #2460 (timed-settle prompt QT vs GAUGE prompt F)

Inputs: raj-3 mid-fall real-photo frames, the OTHER two of the four (ball1 dd35 and ball2 dd33; ro-1 used ball1 dd33 and ball2 dd35).
Seeds 21-23. Prompts: ro-1's exact F and QT (mkjobs.py). 832x480, 93 f @ 24, 35 steps, cfg 6, shift 10, no negative prompt.
Shared queue, endpoints laptop5090 and q8-* (see sidecars/).
Blinding: random r60_<hex> names, key sealed, eye codes committed in 2f53da6 BEFORE the key was opened (KEY.json is the key).
Coding rule (eye_codes_RULE.txt): settled = ball in frame and no airborne hop for >=12 f before f92.
Motion proxy: late_chg_px = mean over the last 24 frame pairs of #pixels with |grey diff|>20 in the plank crop (score_blind.py v2).
The p99 metric in the same script is blind to the small ball, so it isn't used.
Results: summary_noNV.json (per clip + per arm + paired). Sheets: sheets/*_b.jpg (f48-92, every 2 f, native plank crop).
DOVER/DD: pending (CPU scoring is running; follow-up).
