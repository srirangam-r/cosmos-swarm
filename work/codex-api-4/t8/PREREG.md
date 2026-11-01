# Task 8 continuation calibration, frozen 2026-11-01 ~12:09 UTC

Claim/protocol board #4045. Existing results #201/#205/#211/#219 and real pend10
#3984 are known. No generated clips are analyzed here. Twenty original real
GAUGE videos + mocap, dev measurement only, never training.

Primary: unchanged measure_pend v1 (2e26463; existing referee PASS) on distinct
frames [93,186), at 25 Hz, letterbox to 832x468 within 832x480. No intermediate
MP4 encoding; this matches t182's in-memory real control. All 20 retained;
report all and tool flag=ok, paired ratios with recording SE, not seed SE.
200 residual-block-bootstrap replicates, default RNG0; no fit changes.

Reference: independent 3D mocap PCA projection, same-direction interpolated
zero-crossing full cycles within aligned window. Also quadratic-refined maxima
and minima for independent turning-point full cycles. Record each cycle.
Alignment: full first10s image-centroid release detector (original trk.blobs +
measure_pend.release, >3px for4frames) aligned to mocap >5mm sustained4frames
relative initial3positions. Reference same window as tool's post-release fit,
and report full93-frame window separately, ±1 distinct frame sensitivity.
This shared onset is a limitation, so turning points and window sensitivity
provide checks. Reference code is independent, no mp.zc_period call.

Positive control real motion capture; compare fit and crossing values. Byte
verify planted-PASS source files and source t182 real10 output. Frozen tool
flags are fit checks, not identity validity or physical proof on Nano.
No referee resubmission; no mechanism or improvement claim. If computation
exceeds five minutes it runs as recorded background work and this shift ends.
