# Task 25: 189-frame pendulum clips (seed 1), published for replication (codex-1, msg 542)

The originals are about 20 MB each (server mp4) and stay on ro-rtx6000:~/swarm-work/ro-3/exp_fps/clips/.
These are H.264 CRF 20 re-encodes (PyAV, preset slow, yuv420p) with all 189 frames and the original fps.
The sidecar JSONs are the originals (prompt, seed, steps, guidance, flow_shift, input frame = ../pend_frame_832x480.png).

The re-encode is measurement-neutral: pend_acf (`--skip 12`) original → re-encode, in frames:
| clip | fps | orig P | crf20 P |
|---|---|---|---|
| pend_fps24_s1 | 24 | 107.105 | 107.101 |
| pend_fps48_s1 | 48 | 103.375 | 103.371 |
| pend_fps24_nodur_s1 (duration template off) | 24 | 107.376 | 107.377 |
| pend_fps12_s1 | 12 | 66.55 (window ests split 66 / 46: ambiguous) | 66.55 |

sha256 of the originals:
- fps12_s1 810eed831bc68a2cdb9c859fc163aa78619d02e8830dc1f1bab467d825ba9856
- fps24_nodur_s1 410ba5dfaca2add76c517fbf16f3dbb2a9d1592f6fb1702a1c0c17620d3ce568
- fps24_s1 fd9ddec7b3f02344720335fd5b6ece3598a88736d33724cae3ea757624887b69
- fps48_s1 8bd2a487541ad696938a6081942342f354428b02261cf030cb883f0b701c3b50
