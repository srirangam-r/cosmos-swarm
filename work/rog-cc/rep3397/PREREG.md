# Independent re-code of task 139 (#3397, raj-opus-1): does removing the holder unlock the GAUGE ball fall?

Requested in #3397 ("native-rate re-code of O vs A by another agent, identity-continuity rule"). Written 2026-11-01 ~10:55 UTC,
before I opened any t139 clip, strip, zoom or per-clip code. What I had already seen: the README, the input preview
(`preview.jpg`), and the aggregate counts + seed-8 descriptions in #3347/#3397/#3409.

## Data
raj-opus-1's original 48 mp4s + sidecars (GB10 `~/jobs/raj-opus-1/t139_clips/`, offered for re-coders in #3409):
arms O (unedited, gripper holds ball), A (whole robot removed), G (hand+fingers removed) × ball1/ball2 × seeds 1-8.
93 f @ 24 fps, 832x480. I re-code their exact clips (not new seeds; rahul-api task 160 is doing fresh seeds + other recordings).

## Blinding (partial, stated)
- Arm can't be hidden: the edit is visible in every frame.
- `t139rc.py sheets` gives each clip a salted opaque hex, shuffles order and writes the key to `UNBLIND_key.json`, which I don't open before
  codes are committed. So seed/input pairing is hidden while coding.
- I don't open raj-opus-1's `codes.json`, `summary.json`, `strips/`, `zooms_s8/` or `ff_*` until my codes are committed.

## Sheet
Crop x190-370, y60-420 (ball at (280,116) r≈12; plank below), ×0.75. Row 1: f0-15 and row 2: f16-31, every frame (native rate).
Row 3: f32-92 every 4th frame. If a tile is ambiguous I may open the native clip frames for that hex only (still blind to pairing).

## Codes per clip (Y / N / U = can't resolve)
1. **rel_strict** (PRIMARY): the ball present at (280,116) in f0 descends > 1 diameter (> 24 px) below its start by f92, AND from its first
   visible movement until it is > 1 diameter below the start:
   (a) it is visible as one ball in every frame (every frame f0-31, every sampled frame after), with no gap or fade-out/fade-in;
   (b) no copy of the ball stays at, or reappears at, the start location during the descent;
   (c) its apparent diameter stays within ±30% of f0;
   (d) no gripper, hand, arm or tether moves down in contact with it (if so, that's carried, not a release);
   (e) it does not reverse upward in mid-air before first contact.
2. **anyfall**: any ball-like object falls continuously (≥ 3 intermediate heights) anywhere in the crop.
3. **clone**: a ball stays at the start while another ball appears lower, or two balls coexist at any time.
4. **carried**: the arm, gripper or a tether lowers the ball.
5. **holder_back** (A/G): a gripper, hand, string or arm appears and holds the ball.
6. **hover**: the ball is visible, unsupported (no holder touching it) and stationary for ≥ 24 consecutive frames.

## Automated secondary (arm-agnostic, unvalidated)
`t139rc.py depart`: NCC of the f0 ball disk (r=10 mask) at its f0 location in every frame. The departure frame is the first frame with
NCC < 0.5 for 4 consecutive frames. This measures "the ball left its start spot" only, not how. It has no planted case.

## Analysis (`t139rc.py unblind`)
- Per arm: Y/n with Wilson 95%, for every code.
- Seed-level paired: per seed, (arm − O) summed over ball1/ball2, then a sign test (two-sided). Inputs are near-identical and cluster by seed,
  so the honest n is 8 seeds.
- Agreement with raj-opus-1 per clip: my rel_strict vs their clean_fall, and my anyfall vs their any_fall, with raw agreement and Cohen's κ.
  That join is written after my codes are committed; it's only a join.
- Replicated if rel_strict A > O at seed level with ≥ 6 of 8 seeds up and 0 down (matches #3397's sign p=0.031 claim). Challenged if
  agreement on clean_fall is < 80% or the seed-level split is weaker than 5 up / 1 down.
