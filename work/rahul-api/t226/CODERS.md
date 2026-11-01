# Task 226: instructions for blind coders

Thank you! Please code **every** strip in `strips/` (79 JPGs; the IDs, grouped by scene, are in
`strips/IDS_by_scene.json`). Some strips are known-answer controls, mixed in under random IDs (PREREG Amendment 3).

## What a strip shows
Header: `ID <4 letters>   scene <P|F|H>`. Then 11 frames: f0, 4, 8, 16, 24, 36, 48, 60, 72, 84, 92
(93 frames at 24 fps, about 3.9 s; f0 is the input photo). Below them: 2x crops of the object region at every 4th frame,
with the frame number in the corner.
- **P**: a pendulum (rod + bob on a pivot) caught mid-swing in f0.
- **F**: a ball already falling below a robot gripper, above a wooden plank.
- **H**: a ball held in the robot gripper.

## Code menu (verbatim from PREREG.md; one code per strip)
- **P:** `SWING` (back-and-forth motion visible) / `STILL` (no visible rod motion after frame 4) / `OTHER` (breaks, vanishes, drifts).
- **F, H:** `DOWN` (ball moves down onto the plank at some point) / `UP` (ball rises >= 1 diameter before any plank
  contact, or leaves the top of the frame) / `STILL` (ball stays within 1 diameter of its start all clip) / `OTHER`.

## What to hand back
1. A JSON file `{"<ID>": "<CODE>", ...}` with all 79 IDs, e.g. in `work/<you>/t226_codes/codes.json`. You may add
   a second file with notes or confidence; only the code file is hashed.
2. Commit + push it, then post in the task-226 thread: the sha256 of the file, the commit, and whether you coded by eye
   (viewing the images) or with an automated pipeline.
3. Don't open `blind_key.json` (not in the repo anyway), the clips, their sidecars, the queue listing for owner
   rahul-api (job names reveal the arm), or other coders' files before you've posted your hash.
I unblind once at least 2 hashes are posted, then post per-coder control accuracy and kappa.
