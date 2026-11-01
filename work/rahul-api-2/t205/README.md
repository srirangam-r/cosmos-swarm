# Task 205: does swing amplitude explain Nano's "slow" pendulum? (rahul-api-2)

**Answer: no.** Analysis only, no new clips. Input = kiro-1's published rod-angle series
(`work/kiro-1/t191/{nano,fresh,real}.json`, commit 2693411; gate verdicts `gates*.json`, unchanged).
My own refit + amplitude code: `amp.py` (rules in its docstring, fixed before any amplitude was computed;
the side/peak sensitivity was added after seeing the primary result, in the same run).

Rigid pendulum: T(A) = T0 * F(A), F = (2/pi) K(sin^2(A/2)). If Nano's slowness came from swinging wider than the
real pendulum, R_corr = (T_nano/F(A_nano)) / (T_real/F(A_real)) would be ~1.

| set (clips) | R_raw = T/T_real | R_corr (half p-p, primary) | R_corr (per-side) | R_corr (peak) | Nano A (half p-p) | Spearman A vs R_raw |
|---|---|---|---|---|---|---|
| kiro-1 gate PASS, pend10 (n=6) | 1.67 [1.42, 1.97] | **1.74 [1.47, 2.05]** | 1.73 [1.48, 2.02] | 1.67 [1.34, 2.07] | 51 deg [41, 63] | -0.03 (p 0.96) |
| refit R2>=0.8, pend10 (n=18, incl. gate fails) | 1.55 [1.35, 1.78] | 1.59 [1.38, 1.83] | 1.58 | 1.50 [1.27, 1.77] | 56 deg | -0.25 (p 0.31) |
| refit R2>=0.8, all (n=20) | 1.52 | 1.56 [1.33, 1.83] | 1.54 | 1.46 | 54 deg | -0.13 (p 0.58) |

Geometric means, log-t 95% intervals over clips (seed = clip; descriptive, selection by gates/fit).
Real continuation (same tracker): pend10 T 1.17 s, half p-p amplitude 68 deg (turning points +84/-65 deg); pend12 1.18 s, 69 deg.

- Nano's gate-passing swings are *smaller* than the real one (51 vs 68 deg half peak-to-peak), so correcting for
  amplitude makes the ratio slightly *larger* (x1.04). To produce 1.67x by amplitude alone Nano would need ~152 deg
  amplitude; the widest measured peak is 114 deg (s24, one side only).
- Period is uncorrelated with amplitude across clips. rahul-api's #4259 hypothesis (slow seeds = wide swings) is not
  supported on these 20 tracks.
- Side observation: several gate-PASS swings are lopsided about a tilted centre (fit centre c: real 3-4 deg; s12 24,
  s24 23, r_s6 15 deg; turning points e.g. s12 +92/-13, s24 +114/-27). The only gate-PASS pend12 clip (s13, the one
  *fast* gate-pass, T 0.76 s) oscillates between +30 and +110 deg about c = 74 deg, i.e. around a near-horizontal
  "equilibrium". The gates do not check that the swing is centred on vertical, so gate-PASS != physical pendulum.

Caveats: amplitudes are image-projected angles from kiro-1's tracker (period part matches mocap to 0.4%; amplitude
is NOT planted-validated: planted cases test period only). Same camera/first frame for Nano and real, so projection
affects both alike. One prompt, one stack (q8 Karras), two inputs. Selected clips. No new clips.
Files: `amp.py`, `amp_results.json` (per-clip turning points, fits, ratios), `amp_stdout.txt`.
