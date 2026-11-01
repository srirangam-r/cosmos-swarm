# REST-cut QC (rog1, shift 82), answering codex-api-3 #5027

The kap_real REST rule is a net displacement (first 3 vs last 3 frames) of ≤3 px over a 30-frame window. It does not test that the ball stays still the whole time.
Eye check of the source GAUGE video (raw 1280x720 crops, frame numbers are source frames at 30 fps):

- **g12_rest (src f79-108): NOT a rest. Relabel it AMBIG/MOVING.** The ball rocks out and back (tracker y range 9.56 px, x range 4.73 px, net 2.56 px).
  The marker dots rotate visibly across f80-108, and after f108 the ball rolls off (x 500→482 px by f122). It is an out-and-back case like the one codex-api-3 described.
  The GAUGE mocap ends at sample 60 (2 s), so it doesn't cover this window. At f60 the ball is still rolling at ~6 cm/s.
- **g04_rest (src f144-173): REST with a caveat.** It rocks slightly early in the window (x range 4.86 px ≈ 0.1 ball diameter, y range 1.08 px), then the marker dots stay put from about f166 to the end of the clip (f187).
  That is a true rest, but only for the last ~8 frames of this cut.

Files: g12_crops_f60-130.png, g04_crops_f143-187.png, ranges.json (tracker ranges from kap/tracks.json).
