# kap_real (rog1): known-answer pack from real GAUGE ball drops, for end-state coding (rest/rolling/bouncing)
NOT referee planted cases and NOT eye labels. Labels come from GAUGE mocap (bounce end) + a video tracker (rolling vs rest). Use it as a calibration aid alongside the referee check, not instead of it.
Source: HF `InternRobotics/GAUGE-Dataset`, `data/rigid/bouncing ball/{video,json}/1..22` (dev data; measure only, never train on it).
Cuts: `cuts/<cut_id>.mp4`, 832x480 (1280x720 -> 832x468 + 6 px black pad, like raj-1 cosmos_local), duplicate frames removed (the source is 25 fps footage in a 30 fps container), encoded at 25 fps.
Every cut starts at source frame 30 (≈ release) and ends at `end_f` (source container frame index). See `manifest.json`: cut_id, clip, start_f, end_f, label, run (the frame span with that label), n_out_frames.
Label = the ball's state AT THE LAST FRAME of the cut:
- BOUNCING: after first impact (realball v1.1 impact frame, raj-2 json) and ≥8 frames before the earlier of two settle estimates: mocap (last sample with z > rest+5 mm, aligned at first impact; 1 container frame ≈ 1/30 s real) and video (first 15-frame run with the ball within 12 px of its on-plank height).
- ROLLING: ≥8 frames after the later settle estimate, ball tracked in ≥24 of the last 30 frames, centroid moved ≥10 px (1280x720) over those 30 frames.
- REST: same, moved ≤3 px over the last 30 frames (~1 s).
- AMBIG (`*_ambig_settle`): the cut ends between the two settle estimates ±8 frames. Small hops (<12 px) are possible here. Keep these to check how coders treat the boundary.
Counts: 20 BOUNCING, 22 ROLLING, 2 REST (g04, g12), 22 AMBIG. Clips 4 and 16 have no valid realball impact frame, so they have no BOUNCING cut.
Real-ball fact worth knowing: after bouncing stops, 20/22 real balls keep rolling at ~5-6 cm/s (mocap) and most roll off the plank or out of the tracked region. Only 2 reach a ≥1 s still state in frame. "Bouncing stopped" is not "at rest".
Caveats: the tracker is a thresholded dark-blob-vs-background diff (no SAM), not planted-validated. The mocap/video alignment uses one impact frame (±2 frames). Eye QC: g01_bouncing and g04_rest end frames only. Rolling at <10 px/s is AMBIG, not REST.
Reproduce: `hf download InternRobotics/GAUGE-Dataset --repo-type dataset --include "data/rigid/bouncing ball/*" --local-dir src`; then `code/track.py <src>/data/rigid/bouncing\ ball tracks.json`, `code/label.py <json dir>`, `code/finalize.py`, `code/cut.py <src dir> cuts` (finalize needs tools/realball gauge_realball_v11.json from work/raj-2/gauge_realcheck_v2 in the cwd).
