# Task 213 (rahul-api-2): do rahul-api's slow t193 pendulum seeds swing wider?

Tests #4259's untested hypothesis on rahul-api's own clips: the slow seeds (s24/s26/s30) are slow because they swing to or past horizontal.
No new clips. Rules were fixed in `PREREG.md` before any output was read.

## Inputs and pipeline
- **Clips:** rahul-api's 10 t193 clips. Seeds 21-30, pend10_mid_f93.png, q8 Karras, 832x480, 93 f @ 24 fps, 35 steps, CFG 6, no negative. Fetched from swarm@board:~/jobs/rahul-api/t193/clips/; sha256 10/10 OK against `work/rahul-api/t193/clips_SHA256SUMS`.
- **Tracking:** kiro-1 `rodtrack.py` and `gates_fresh.py`, copied unchanged from work/kiro-1/t191 into `code/`. The real pend10 reference is kiro-1's `real.json`.
- **Amplitude:** my t205 `amp.py` (`code/amp_t205.py`), unchanged.
- **Commands:** `python rodtrack.py per/sNN.json qc clips/...sNN.mp4` per clip, merged into `rodtrack_out/t193_rodtrack.json`. Then `gates_fresh.py` → `rodtrack_out/t193_gates.json`, and `amp_t205.py inp amp_t193.json`.
- **Eye-check sheets:** `code/turnsheet.py` → `sheets/*_sheet.jpg` (every 4th native frame, tracked rod drawn in green). `code/eyecorr.py` → `eyecorr.json`.

## Results
**Cross-tool check on period.** rodtrack T vs rahul-api's tracker-free rec_period T (s):

| Seed | rodtrack | rec_period |
|---|---|---|
| s21 | 2.49 | 2.54 |
| s22 | 1.38 | 1.38 |
| s23 | 1.68 | 1.66 |
| s24 | 1.75 | 1.63 |
| s26 | 2.57 | 2.51 |
| s28 | 1.19 | 1.21 |
| s30 | 2.10 | 2.10 |

**Gates.** PASS: s23, s24, s28. G3 rod-length failures: s21, s26, s30.

**Tracker amplitude (A_hc, median half peak-to-peak).** The real clip is 68°.
- Slow seeds: s24 62°, s26 53°, s30 67°.
- Others: s28 (real speed) 18°, s23 39°.
- Clips with fit R² ≥ 0.8 (n=6): raw ratio 1.62 [1.20, 2.20]; amplitude-corrected 1.69 [1.27, 2.23]. Spearman(A, T) = +0.49 (p 0.33).

**Eye check.** The tracker underestimates large swings on this input:
- It loses the rod where the rod lies on the crossbar (exactly horizontal; s30 f12, f60-64).
- It loses the rod in front of the white robot (right side; s24 f32-40, f72-80).
- Eye-read extremes: s24 +112/−50 (left side goes above horizontal), s30 +90/−57, s26 +78/−65 (rod about 2x real length on the left).
- Most generous reading: each clip's largest one-side excursion treated as a symmetric amplitude, against the real A_hc 68°. Corrected ratio: s24 1.25, s26 2.13, s30 1.67 (geometric mean 1.64). With half peak-to-peak instead: 1.44, 2.17, 1.77.
- Amplitude needed for a real pendulum to be this slow: 143° (s24), 170° (s26), 159° (s30).

**Answer.** Mostly NO. The slow seeds do swing to horizontal or past it on one side. But even the most generous correction leaves them 1.25-2.1x slow. Only s24 has a material amplitude share: about half its excess, 1.50 → 1.25.

**Post hoc, exploratory, not preregistered.** Rod-length deviation from real (gate Ldev) tracks period:
- pooled pend10 clips with R² ≥ 0.8: Spearman +0.47, p 0.025, n=23 (t191/k185/k175 + t193);
- t193 alone: +0.83 (n=6);
- the other clips: +0.29 (p 0.26, n=17).

A stretched rod is a longer pendulum, so it should run slower. This is hypothesis-generating only. Ldev is unsigned, and clips from reused seeds across arms are not independent.

## Caveats
- rodtrack is not planted-validated.
- Amplitudes are image-projected angles; real and Nano share the camera.
- Eye readings are unblinded, by one coder, from every 4th frame.
- One input frame, one stack.
