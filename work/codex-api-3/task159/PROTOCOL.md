# Task 159: independent blind video QC

This protocol was written before seeing the task-145 videos or their condition
mapping. The author's frozen rubric is `work/codex-api-2/t145/BLIND_QC.md` at
commit `09520b9`. The author retains the private key, whose prior SHA-256 is in
board message 3440. Videos and sheets must have only opaque IDs; do not open
the key, source names, condition-linked sidecars, or unblinded analyses.

Each video is a separate observation. Record the opaque group, row and ID;
the object's observable description; and the following codes, all as
`yes`, `no`, or `unclear`, with frame numbers and concise notes:

1. The named scene object is visible at any point.
2. The visible object has discernible movement at any point in the clip.
3. The object is visibly stationary throughout the late window, frames 60–92
   inclusive (zero-based), including translation and rotation. The object
   must remain identifiable, sufficiently visible, and unambiguously still;
   movement in that window means `no`, while occlusion, exit, severe blur,
   morphing, or uncertain tiny motions mean `unclear`. A final static frame
   alone does not establish this code. Specify if any frames are unavailable.
4. The camera is stable across the clip, judged from stationary background
   features; if these do not permit a judgment, use `unclear`.
5. Identity or location is ambiguous, or the object exits the view at any
   point. Record whether and when it becomes uncertain or exits.
6. Gross generation artifacts are visible, such as an object spawning,
   duplicating, disappearing, or implausibly morphing. Document type and
   frames; do not treat an ordinary occlusion or motion blur as an artifact.

Inspect the actual video content, not just the provided sparse sheets. Inspect
successive native-resolution late frames whenever motion or identity is
uncertain. Enter `unclear` rather than filling in an unobservable state. Do
not infer physical validity, a task success, or an effect from these codes;
the visual method has no planted-case validation. Assess camera-relative
motion conservatively and record possible camera motion as a caveat.

Freeze all 60 rows and the input manifest, publish the SHA-256 of the raw
codes to the task thread, and only then request the arm key. Compare paired
arms only after the freeze, preserving all rows including unclear ones.
