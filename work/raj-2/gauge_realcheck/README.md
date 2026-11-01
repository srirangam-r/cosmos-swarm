# Real-footage check of tools/trk_ballfall on GAUGE real bouncing-ball videos (raj-2)
Data: HF dataset InternRobotics/GAUGE-Dataset, data/rigid/bouncing ball/{video,json}/1..22 (real 1280x720 @30 fps video + mocap z in mm @30 fps). Dev data, measured only.
Download: `curl -L https://huggingface.co/datasets/InternRobotics/GAUGE-Dataset/resolve/main/data/rigid/bouncing%20ball/video/<i>.mp4` (same for json/<i>.json).
- gauge_eval.py: runs trk.ball(F, 30, D=0.06) UNCHANGED + mocap free-fall fit -> gauge_trk_results.json
- dumptracks.py: per-frame trk.blobs(mode='ball') tracks; diag1.txt = clip 1 track
- gated.py: diagnostic release-gated quadratic fit on those tracks, 3 scale choices -> gated_results.json
Result: unchanged tool g = -1.25 ± 1.30 m/s² (sd 6.1, n=22) vs mocap 8.77 ± 0.02. Cause: ball is held in the gripper ~35 frames before release; fit starts at frame 0 and scale comes from the gripper-occluded ball (~24 px vs ~48 px free). Release-gated: 12.1 ± 1.6 (sd 7.5, n=21), still too noisy (7-10 airborne frames, duplicated frames, blob merges with shadow at impact).
