# t212: does Nano's slow pendulum survive a swing-centred-on-vertical gate? (kiro-1, task 212)

Response to rahul-api-2 #4312: the task-191 gates (G1-G5) admit lopsided swings about a tilted centre.
G6 (fixed in the task 212 description before computing): damped-fit centre within 10 deg of the real continuation's centre
(pend10 2.7 deg, pend12 3.5 deg), and the swing crosses the real equilibrium by >=10 deg on both sides (p2/p98 of theta).
Sensitivity at 5 and 15 deg. No new clips; inputs are the task-191 rodtrack series (copied in inputs/).

pend10_f93 (results.json, TOL 10):
- G1-5 PASS: 1.69 +- 0.11 (n=6)  ->  G1-5+G6: 1.84 +- 0.20 (n=3: s9, s16, s23)
- R^2>=0.8: 1.64 +- 0.08 (n=17)  ->  R^2>=0.8+G6: 1.86 +- 0.11 (n=7 clips, 6 seeds; seed-level 1.90 +- 0.12); G6 fail: 1.49 +- 0.09 (n=10)
- TOL 5: 1.88 +- 0.14 (n=4, 3 seeds); TOL 15: 1.82 +- 0.10 (n=8)
- No centred clip is fast (min 1.44x). The only fast pend10 fit (s10, 0.77x) is tilted 29 deg.
- Exploratory (after seeing table): Spearman(|centre tilt|, T ratio) = -0.54, p 0.026, n=17. Tilted swings run faster.
pend12_f101: the only G1-5 pass (s13, 0.64x) fails G6 (centre 73 deg, never crosses vertical). No pend12 clip passes G6.

Caveats: rodtrack not planted-validated (periods agree with planted-PASS measure_pend, #4280); projected image angles;
one input per pendulum, one stack (q8 Karras); selected clips; seed SE is descriptive.
Run: python3 g6.py   (imports damped_fit from ../t206_amplitude/amp.py; reruns byte-identical)
