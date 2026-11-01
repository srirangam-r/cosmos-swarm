# t226 F/H (+ P STILL) blind-code results: unblinded 2026-11-01 ~15:06 UTC

Frozen rules: PREREG.md Amendment 6 (F/H decision = blind-code McNemar) and Amendment 8 (4b068de, 15:01:51 UTC: 2-coder
consensus, 1-1 split -> OTHER). Run: `./run_codes_t226.sh ../../rahul-5-agy/t226_codes/codes.json ../../rahul-3/t226_codes/codes.json`.

Coders (blind; neither had seen the key, clips or sidecars):
- rahul-5-agy: codes.json @0dbbae4, sha256 d3f7d95e...dad5e (tracker pipeline + eye check)
- rahul-3: codes.json @bb16303, sha256 156924c1...fff2f (by eye)
Both hashes were recomputed before unblinding and match the board posts (#5293, #5375).

## Known-answer controls (7 hidden strips)
rahul-5-agy 6/7 (missed H_kaReal); rahul-3 6/7 (missed F_kaUp). Neither is flagged (flagging needs >=2 misses).
Cohen's kappa on the 72 clips: 0.62. Raw agreement on the 12 IDs named in #5293 was 5/12, vs 53/67 on the rest, so there is no
sign that the second coder copied #5293.

## Consensus code table (6 seeds per arm)
| scene | base | neutral | counter A | counter B |
|---|---|---|---|---|
| P (mid-swing) | SWING 6 | SWING 5, OTHER 1 | still: SWING 6 | fast: SWING 5, OTHER 1 |
| F (mid-fall) | DOWN 6 | DOWN 6 | up: DOWN 6 | still: DOWN 5, OTHER 1 |
| H (held, f0) | OTHER 4, DOWN 2 | STILL 1, OTHER 5 | up: UP 1, OTHER 5 | still: STILL 4, OTHER 2 |

## Decisions (exact McNemar vs neutral, paired by seed; TEXT CONTROLS needs a 6/0 discordant split)
| contrast | event in C | event in neutral | discordant C-only/ref-only | p | decision |
|---|---|---|---|---|---|
| P still -> STILL | 0/6 | 0/6 | 0/0 | 1.0 | NOT DETECTED |
| F up -> UP | 0/6 | 0/6 | 0/0 | 1.0 | NOT DETECTED |
| F still -> STILL | 0/6 | 0/6 | 0/0 | 1.0 | NOT DETECTED |
| H up -> UP | 1/6 | 0/6 | 1/0 | 1.0 | NOT DETECTED |
| H still -> STILL | 4/6 | 1/6 | 3/0 | 0.25 | NOT DETECTED (vs base 4/0, p 0.125) |

Pooled over the 3 mid-motion counter-event arms (P still, F up, F still), the text-described event appears in 0/18 clips
(Clopper-Pearson 95% upper bound 0.185), the same rate as in the neutral arms (0/18).

## Per-coder sensitivity (descriptive)
- rahul-3 alone gives the same picture: H still STILL 4/6 vs neutral 1/6 (3/0, p 0.25); F still STILL 1/6 vs 0/6.
- rahul-5-agy alone codes most H clips STILL in every arm (neutral 5/6, still 5/6, up 4/6, base 3/6), so H still vs neutral has
  0 discordant pairs. The H "stay held" nudge is therefore **coder-dependent**. The coders disagree on whether the held ball goes
  down (9 clips: r5 STILL vs rahul-3 DOWN), which is the main source of disagreement.

## Coder-free secondary (frozen analyze_t226.py, results.json; not decisive under Amendment 6)
H ME_roi (motion energy around the ball start): still - neutral -1.81 [-3.27, -0.34] gray levels, 6/6 seeds, p 0.031;
still - base -4.93, 6/6; base - neutral +3.12, 6/6; up - neutral -0.15 (2/4). ANOVA on H ME_roi: eta^2 prompt 0.60, seed 0.27.
So at the held-ball start, text shifts HOW MUCH moves (the GAUGE release sentence adds motion, "stays held" removes some)
in every seed, but it does not reliably change WHICH event happens (codes).
F dy8 / H dyEnd failed QC (Amendment 6) and are not reported as outcomes.

## Reading
Once motion is under way in the input frame (pendulum mid-swing, ball mid-fall), no counter-event sentence produced its
event in any of 18 clips. At a static held-ball start, text has a measurable but partial effect: the amount of motion moves
in 6/6 seeds, and the consensus STILL rate rises from 1/6 to 4/6, which is not significant at n=6 and depends on the coder.
This fits conditional-image leakage (2406.15735) and deletion-fails-early (2512.08486): text loses to the motion the frame
already implies.

Not tested: other frames or scenes, >6 seeds, NVIDIA's own sampler (all clips used board Karras sigmas), and T2V.
Seeds 105-106 ran on a100, which may ignore CPU noise (Amendment 7); pairing within a seed still holds.
