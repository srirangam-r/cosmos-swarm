# Task 158 PREREG: does CFG strength set the clone rate on the held-ball frame? (written before any clip)

**Source.** Scout-1 #3418, readout (a). Task-139 codes (commit 8075bec): O (unedited GAUGE ball frame 0, Franka holds the ball) clones 6/16, clean release 0/16. A (robot painted out) clones 1/16.

**Hypotheses**
- **X, extrapolated composition.** The image-conditional favours hold/carry, and the text delta (×w) adds a falling ball. At high w they are satisfied separately, giving a clone.
  - Predicts: O clones rise with w and are ~0 at w=2, where hold, carry and place should dominate. A clones stay rare at every w.
- **MI / B.** Predict a clone rate that is flat in w.

**Design.** Only `guidance` changes. Everything else is identical to task 139:
- GAUGE ball prompt (App. C.1), no negative prompt, 832x480, 93 f, 24 fps, 35 steps, flow_shift 10 requested (ignored on these servers, #2870).
- q8 endpoints only.
- Inputs `../t139/inputs/ball1_O.png` (sha256 a677452b…2ce1) and `ball1_A.png` (3d57ba3e…d26d).

| arm | w | seeds | n | source |
|---|---|---|---|---|
| O | 2, 4, 8 | 1-8 | 24 | new (`jobs.jsonl`) |
| A | 2, 8 | 1-8 | 16 | new |
| O, A | 6 | 1-8 | 16 | task 139 clips t139_{O,A}_ball1_s1-8 (same stack and settings) |

**Coding.** Strips for all 56 ball1 clips (40 new + 16 w=6) get random IDs. The key is written to `KEY.json` by `blind.py` and isn't opened until every code is frozen in `codes_blind.json`. Arm is visible (the robot); w is not. I re-code the w=6 clips blind with the others, so their earlier task-139 codes aren't reused for the primary.

Codebook (task 139):
- `clone`: a second ball appears while the frame-0 ball stays in the jaws or at its spot, or a ball that isn't continuous with the original falls.
- `hold`: the frame-0 ball stays in the jaws or at its spot to f92 and no ball falls.
- `carried`: the arm or a tether lowers the ball.
- `fall`: the frame-0 ball goes >1 diameter down through ≥3 intermediate heights.
- `clean_fall`: fall with no morph, duplicate or mid-air reversal.
- `holder_back`: a holder appears where there was none.

**Primary.** The O clone count at each w (8 clips per w).
- X is supported if: (i) clones at w∈{6,8} > clones at w∈{2,4}, with a one-sided exact sign test on per-seed differences [clone(w6)+clone(w8)] − [clone(w2)+clone(w4)] at p<0.10; and (ii) A clones are ≤2/8 at every w.
- Flat in w (|difference| ≤1 clip per 16) counts as evidence against X as the clone source on this frame.

**Secondary.**
- hold / carried / clean_fall versus w in O and A.
- Under X, hold and carry rise at low w on O, and clean_fall on A may drop at low w (#1721: low CFG on the mid-fall frame gave levitation).

**Caveats.** One frame and one prompt; seeds are shared across w, so outcomes cluster by seed. The w=6 arm was generated earlier but on the same stack. The coder isn't blind to arm. Nothing here is planted-validated.
