# ro-1: bounce-decay check on ball_E_ball1_fps12_93f_s1 (review of finding 476)
Clip: Nano I2V from raj-3's GAUGE ball-1 mid-fall frame (dd33), exact GAUGE prompt, no negative,
832x480, 93 f @ fps 12 (stated 7.75 s), 35/6/10, seed 1, ro-1 :8021 (sidecar in work/ro-1/fps_sweep/out or ro-rtx6000).
- crops.py: zoomed crops (x 180-420, y 40-420, y ticks every 50 px) -> crops_0_24.jpg, crops_69_93.jpg.
- track_dark.py: median-background dark-blob tracker. FAILED here (median has a ball ghost near the plank;
  ball against black curtain is invisible), so numbers below are read by eye from the crops. UNVALIDATED.
Readout (by eye): first apex f4-5 at y~195-200; contact y~320-335 => rise ~130 px.
Last apexes f69 ~215, f72 ~235, f76 ~255, f80 ~235, f85-86 ~245, f89-90 ~240 => rise ~90-115 px.
Ball still bouncing at the final frame 92 (7.7 s stated). ~20 impacts. Contact depth jumps between plank and table edge.
