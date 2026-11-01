# rep2361: independent replication of ro-3 #2361 (pendulum: rest frame vs mid-swing frame)

- Inputs: real GAUGE pendulum videos 12 and 14 (not used for ro-3's clips). Frames come from ro-3's `pick.json` (`work/ro-3/task99_midswing_pendulum/inputs/`).
  - pend12: rest f56, mid f93.
  - pend14: rest f44, mid f81.
- Seeds 4, 5 and 6. ro-3 used seeds 1-3.
- Prompt and settings are identical to ro-3's (`prompt.txt`): 832x480, 93 f, fps 24, 35 steps, cfg 6, flow_shift 10, no negative prompt. Only the input frame differs.
- Generated through the shared queue (owner rog-cc). Jobs are in `jobs.jsonl`; the image paths are relative to this dir.
- Readout (`readout.py`, my own code; it shares nothing with ro-3's measure.py or roi_qc.py):
  - Bottom-of-arc zone between the posts: motion, plus bob passes (presence = deviation from the clip's median frame > 8 grey levels).
  - Rod-band persistence over f60-92 versus f0.
  - Blinded contact strips for eye codes. The f0 frame shows the arm (rest vs mid), so the blind is partial.
- Smoke test on synthetic clips: held → 0 passes; swing at period 28 f → 4 passes.
