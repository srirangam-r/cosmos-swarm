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

## RESULT (dk1, 2026-11-01 20:05 UTC; 18/18 on q8, server.py 04e8e0de81, UniPC, k19, CPU noise)
Frozen readout: `out/t276_table.md`, `out/t276_results.json`, strips `out/strip_*.jpg`.
- **nphys (amplitude supplied): 7/9 clean, 7/7 within 10%, median P/P_real 0.994 [0.992, 1.001] (ACF), 0.999 (MP).**
  The paired clips (same scenes, seeds, noise and P; release-from-rest proxy) in 276/277 were **0/9 clean**. Per scene: real_09 2/3, real_14 3/3, real_16 2/3.
  The two failures (real_09 s2, real_16 s3) have ACF ok at 0.99/1.00 x P_real, but MP locks onto 2.99 s / 0.59 s (R2 0.22/0.32), so the reader-agreement gate rejects them.
  Ungated, ACF reads all 9 at 0.99-1.02 x P_real.
- **x17 control: all 9 clips read 1.67-1.78 x P_real on both readers** (R2 0.99-1.00). 4/9 pass the gate; the rest are ACF 'check' at a ~2 s period.
  Copy-through of the supplied period holds at 3 seeds x 3 scenes.
- Pre-registered reading (>= 6/9 clean -> amplitude is the cause): **met**. The 276/277 failures on near-vertical frames came from the zero-amplitude
  release-from-rest proxy, not from the scenes.
- Caveats: amplitude 18 deg and direction are SUPPLIED (like P); real_09 s1 / s3 strips show some bob deformation (ring-like shape) in a few frames,
  not scored. No NVIDIA-scoreboard (DOVER etc.) check here.
Clips: the 3 first-seed nphys mp4s are committed; sha256 of all 18 in out/clips_SHA256SUMS; all sidecars, server sidecars and qc are in clips/.
