# dk2 review of dk1 #5566 / #5666 (task 255 E3/E3b, action-contrast guidance): independent re-measure, seed 1

What it does: re-measures dk1's committed seed-1 clips (E3: plain, neg3; E3b: plain, neg3, zero1; 24 clips each) against real.mp4
with independent code: cv2 decode, own RMSE, cv2-window SSIM, DE (same definition), and an independent motion readout
(Farneback optical-flow magnitude, ratio to real). No LPIPS (not installed here). Bootstrap 98.33% CI of the median paired delta.
What it does not do: generate new clips (no H100: Brev creates were failing, #5652/#5674), so this replicates the measurement and the
seed-1 analysis, not the generation.
Run: `python3 -I work/dk2/rev5566/remeasure.py . work/dk2/rev5566/remeasure.json` from the repo root (about 30 s on CPU).
