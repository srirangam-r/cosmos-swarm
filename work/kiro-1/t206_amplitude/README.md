# t206: does Nano's own swing amplitude explain its slow pendulum? (kiro-1, task 206)

No new clips. Re-analyses the rodtrack theta(t) series from task 191 (pend10_mid_f93 input, q8, 832x480, 93 f @ 24 fps,
35 steps, CFG 6, Karras; 17 clips with fit R^2 >= 0.8, 13 distinct seeds; k175 clips include Rule R / neutral suffix arms).
Real anchor: GAUGE pend10 continuation from f93, same camera, same tracker: T = 1.170 s.

Prediction for a real rigid pendulum at the clip's amplitude a: T_pred = 1.170 * F(a)/F(a_real), F(a) = 2K(sin^2(a/2))/pi.
Three amplitude definitions (projected image degrees): half peak-to-peak, max side, damped-fit A0.

Result (results.json): Nano amplitudes are not larger than real (mean half_p2p 66.8 vs real 70.2 deg; fit_A0 68.6 vs 74.0).
T is uncorrelated with amplitude (Spearman -0.04, p 0.89, n=17; seed means -0.04, n=13).
Amplitude-corrected ratio T/T_pred = 1.66 +- 0.08 (clip SE, n=17); seed-mean 1.69 +- 0.11 (n=13); gate-PASS subset 1.75 +- 0.12 (n=6).
To get the mean 1.64x from amplitude alone the swing would need ~153 deg amplitude.

Caveats: rodtrack is not planted-validated (planted pendulums are string pendulums); amplitudes are projected angles,
shared camera so the bias is common to real and Nano; R^2 >= 0.8 selection excludes the stretched-rod/irregular clips.
Run: python3 amp.py inputs results.json  (needs nano.json, fresh.json, real.json, gates*.json from t191)
