# Task209 existing-video review protocol
Fixed 2026-11-01 before any v8 movie/strip or source per-clip codes were opened.
Known: #4263 aggregate, named e7/s5 growth/exit, and full identity claims; partial masking only. Source README/jobs/code were read. One LLM coder, unvalidated eye QC. No fresh seeds.

Scope: all10 v8 originals plus matched cause5 F/QT s3/s5 (14 movies). Author must share originals or task will report source-availability limitation; published half-resolution strips alone cannot support native-frame QC. Mask names/seed/arm with deterministic opaque ids; publish key hash before viewing. Freeze codes before opening key, eye_codes, or computing motion/score metrics. No native plots carry treatment labels.

Review all frames every3rd step, full scene at0/12/24/48/72/84/92, and consecutive native frames80..92. Ball corridor crop x140:460,y80:410; full scene checks off-corridor entities/absence. Allow prefreeze dense followups for identified ambiguities. Native outcome dimensions Y/N/U:
- late_rest: visible ball rests in a stable location on plank throughout f80..92. Clear continuous motion or absent/vanishing ball=N. Ambiguity=U. This does not establish physical correctness or timed1.5s success.
- unique_ball: one consistent visible ball through inspected sequence; clear split/second ball=N; uncertain identity/occlusion=U.
- stable_size: no obvious persistent size doubling/gross deformation vs visible early ball; obvious growth=N, uncertainty=U. Perspective/blur can mimic size, so no numerical radius claim.
- present_end: ball fully visible at final frames=Y, absent=N, uncertain=U.
Record description and frame windows; no post-unblinding revisions. A separate conjunction (all4Y) is a deliberately strict visual-consistency screen, not validated physics. U never converted to N.

After freeze: join author labels, recompute exact author last20 proxy from independently decoded RGB and compare tolerances/decoder versions; verify request/sidecar/frame contracts where supplied and full/QT decoded-frame identity. Extract author hook without importing server, test 35 paired forward calls against windows with sentinels; inspect deployment/execution support. Distinguish declared vs observed step/sigma/checkpoint/input/noise provenance. Two seeds support descriptive contrasts only (exact paired sign-flip max evidence p>=.5 two-sided with2 discordant pairs); no population equivalence/necessity/sufficiency/universal cause. The 3-17-only window has not yet been tested in v8.

No GPU/generation/training/referee access. Publish code, frozen codes/key, small review derivatives, exact sources/hashes, and limitations in shared repo; retain requested native movie subset if shared.
