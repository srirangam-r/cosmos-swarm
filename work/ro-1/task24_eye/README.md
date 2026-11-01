# Task 24 blind eye-coding (ro-1), done before unblinding

**Input mismatch.** The 84 blinded eval clips (GB10 ~/jobs/rahul-3/eval_clips) do NOT start from the official GAUGE
frame with the Franka holding the ball (left in `input_mismatch_official_vs_eval_f0.jpg`). They start from a ball
against a white wall (right): centre (529,46), D≈47 px, content x155–676. gauge_blind v1.1 (SEED 281,119, D=22) and
agy-2's task69 evaluator (which copied the same seed) therefore tracked blank wall. Their "0 release / frozen" labels are invalid.

**Files**
- `eye_codes.csv`: per-clip codes from viewing `page0-6.jpg` (frames 0,12,24,36,48,60,92). fell = the f0 ball leaves its spot and comes down;
  artifact = none / size_jump / duplicate / tether / respawn / plank_morph / morph / vanish; end_state = rest (on plank) / air.
- `release2.py` → `release2.json`: scale-free persistence check of the f0 ball pixels (keep fraction per frame, first frame it leaves).
- `montage.py`: builds the pages.

**Blind tallies (n=84, all arms pooled):** fell 72/84; no artifact 56/84; clean fall (fell & no artifact) 53/84, of which
43 at rest and 10 in the air at f92 (often rebounds to near the start height, i.e. energy gain). Stays put: 2eecd3, 7510f5, d46f3d (+ dup/tether cases).
