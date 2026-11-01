# rog2: independent replication of raj-3's pendulum finding (msg 201, task 8)
Data: HF InternRobotics/GAUGE-Dataset data/rigid/pendulum/{json,video}/1-20 (dev; measured only). Run from a dir where
`../data/gauge/data/rigid/pendulum` holds the download.

- `mocap_rog2.py` (+ `mocap_rog2_lib.py`): 3D sphere fit -> pivot, signed swing angle in the PCA swing plane,
  parabolic-refined turning points, period = same-side turning-point spacing; compared with the exact
  finite-amplitude period 4√(L/g)K(sin²(θ0/2)). Output `mocap_rog2.json`.
- `video_rog2.py`: **no blob tracking**. Decode at 832x468 (Cosmos letterbox scale), drop duplicate frames (25 fps clock),
  first 7.875 s; ROI pixel stack -> PCA, PC1 time series; release = sustained frame-diff energy rise;
  period = upward zero-crossing spacing of PC1 and a damped-sine fit. Reference: mocap mean period over the same
  post-release duration. Output `video_rog2.json`. Not planted-validated (it's a review cross-check only).

Results (n=20, mean ± sd):
- mocap: θ0 = 84.4 ± 0.3°, first-8-s period 1.1721 ± 0.0014 s, first period 1.1974, late (2° amplitude) 1.0392 ± 0.0007 s,
  whole-record mean period 1.0657 ± 0.0005 s. Sphere-fit L = 0.2758 m; L_eff from the late period = 0.268 m (physical pendulum).
- video/mocap matched: PC1 zero crossings 0.9976 ± 0.0085 (SE 0.0019), damped sine 0.9931 ± 0.0061; max |err| 1.4%.
