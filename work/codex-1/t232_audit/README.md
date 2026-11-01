# Task 232: partial audit of finding 4569

Independent aggregation of the author's `results.json` at shared commit 26ee1a4. Run `python3 work/codex-1/t232_audit/audit.py` from repo root. Same clips and tracker outputs; not an independent tracker, fresh-seed replication, or planted validation. Paired bootstrap samples the 10 seeds as clusters, 20,000 draws, RNG seed 232; interval is descriptive for these seeds and one scene.

Orig/L70/L50 G4 passes: 8/10, 7/10, 1/10. L50 minus orig: -0.70 [−1.00, −0.40] paired bootstrap; seven lose and none gain G4, exact two-sided sign/McNemar p = 0.015625. L70 minus orig: -0.10 [−0.40, 0.20], one gain and two lose. G4 is tracker coverage, not a direct measure of physical breakage. All-gate passes 3/1/0 and no seed passes both orig and either edited arm. Consequently the preregistered primary is inconclusive, and the gate-passing sample cannot supply a paired period comparison.

G4-qualified L70 median lengths vary 86.4–129.2 px (n=7); 93.4 is their median, not a measurement over all ten outputs. Low coverage and the tracker’s possible attachment to the wrong structure prevent translating that number alone into actual regrowth. At L50 only seed 26 passes G4; its pivot gate and period fit fail. High R² alone does not establish a rigid oscillation.

Unblinded review of the author's reduced-resolution six-frame strips shows large bob-like appearances in several L50 clips (e.g. seed 29 f24 and seed 21 f30), relative to same-seed original; seed 23 appears to have multiple bright irregular structures by f54. Perspective, continuity and rod attachment are unresolved from strips. This is illustrative qualitative QC, no independently coded frequency or full-resolution pixel tracking. Inputs differ in both length and editing artifacts; neither a scene prior nor general behaviour on real unedited pendulums follows. Author's period-law conclusion remains open.

Outstanding for task 232: original native clips in an authorized shared location, independent per-frame rod/bob tracking and reference validation, and an independent blinded audit. This partial result is not the requested complete replication.
