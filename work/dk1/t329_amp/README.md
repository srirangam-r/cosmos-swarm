# Task 329 (dk1): amplitude cause test for Nano-Phys failures on near-vertical frames. FROZEN before any clip.
Cause under test (#6682, #6700): the 276 contract builds the proxy with release_from_rest=True, so the swing amplitude is |theta0| of the frame.
On near-vertical frames the proxy barely moves (moving-pixel count: real_16 9, real_09 693, vs 2938-5401 in passing scenes) and nphys is 0/9 clean
(276 real_09 s1-3, real_16 s1-3; 277 real_14 s101-103).
Intervention (one parameter): `generate_pendulum_proxy(..., release_from_rest=False, amplitude_deg=18, direction="inward")` (18 = proxy.py's own default).
New proxies' moving-pixel counts: 6518-7113. Everything else is identical to 276/277 (same images, pivot/bob, P_real, prompt, k19, CPU noise, q8),
and seeds are PAIRED with the failed clips (09/16: 1-3, 14: 101-103), so the only change vs the failed clips is the proxy.
Arms: nphys (P_real) and nphys_x17 (1.7 P_real control), 3 seeds per scene, 18 clips. Readout: 276 analyzer (prefix only changed), Raj v2 gate.
Pre-registered reading: amplitude is the cause if nphys clean >= 6/9 with ratios within 10% (vs 0/9 paired), and x17 reads ~1.7 on both readers.
If nphys stays <= 2/9 clean, amplitude is not sufficient (scene/tracking causes, as #6447 proposed, remain).
