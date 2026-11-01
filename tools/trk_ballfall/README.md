# trk_ballfall (raj-3)
Tracker for ball free fall (g, restitution e), incline block (a), pendulum (period).
Usage: python3 -I trk.py planted.json <clip_dir>   (writes est.json; clips named <clip_id>.mp4)
Ball: background built from first/last frame, blob via diff, scale from median minAreaRect minor side = known diameter; quadratic fit up to first impact; e=sqrt(rebound apex / drop height) on first rebound only.
Block: median-bg diff (THR=25), scale from median long side; v0=0 fit with free t0. Pendulum: damped cosine on blob x.
Referee planted check: v3 = 20/20 within 10% (PASS). Caveats: static camera only; untested on Cosmos output or real photos; block 'a' still 5-10% off.
