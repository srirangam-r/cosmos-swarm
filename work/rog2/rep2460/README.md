# rog2 replication of ro-1 #2460 (timed prompt QT vs F, mid-fall inputs)
- jobs.jsonl: 12 jobs queued (owner rog2, 08:15Z): arms F/QT x ball1(dd33)/ball2(dd35) x seeds 6-8 (ro-1 used 1-5), prompts copied from ro-1 jobs_v5.
- track_ct.py: seeded CoTracker3 (3x3 grid, ±6px). ball1 seed (296,159) for the dd33 frame (ball = dark blob under gripper). ball2 seed NOT yet determined.
  CoTracker visibility is ~0.02-0.06 for the black ball on the black curtain, so the vis>=0.85 gate is useless here; overlay QC (ov.py) is the check.
- Pilot on ro-1's existing clips (ball1): F s3 locks the ball, contacts every ~8 f to f83 (never rests); QT s3 locks, one contact f7 then rest (71 rest windows). Consistent with #2460 for s3.
- ana.py / summ.py: contacts, late lift, rest windows (copied from ct92_seeded).
Run: python3 track_ct.py cpu out clips/*.mp4; python3 ana.py; python3 summ.py; python3 ov.py <name>
Fetch clips: python3 agentic_colab/scripts/cosmos_queue.py fetch --owner rog2 --out clips
