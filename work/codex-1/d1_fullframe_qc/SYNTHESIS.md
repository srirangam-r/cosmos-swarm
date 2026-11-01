# Paired clip QC synthesis, task 89

## Scope and method

The 16 supplied clips (two ball scenes × four seeds × held-frame control and later-real-mid-frame input) passed the supplier's SHA-256 checks and decode to 189 frames. All frames were screened in reduced-resolution grids; paired reviews used full-frame samples, mostly every six frames, and selected consecutive native-frame windows. The original input and reports reveal the arm; this is an unblinded, post-hoc qualitative review, not a prespecified exhaustive native-frame annotation or a validated event detector. Lack of a noted event is not evidence of absence. Original sidecars and hashes appear in the linked clip directories. Clip indices below are zero-based.

| Scene / seed | Held frame: observation and missingness | Later mid-event frame: observation and missingness |
|---|---|---|
| ball 1 / 1 | Large form enters top f92; its connection to indistinct initial object unknown. | Form moves from gripper region toward support f0–5 and back near gripper f8–11; later apparent enlargement may involve depth. Contact and identity unknown. [Evidence](pair_b1_s1/) |
| ball 1 / 2 | Form fades inside image f62–64, absent f65; similar form later at sampled f114. Identity unknown. | Form moves toward plank f0–6; apparent height changes sampled through f186. Contact and continuity unknown. [Evidence](pair_b1_s2/) |
| ball 1 / 3 | Large form enters top f16; connection to initial object unknown. | Form moves toward plank f0–8; sampled height changes through f186. Contact and continuity unknown. [Evidence](pair_b1_s3/) |
| ball 1 / 4 | Large form enters top f10; connection to initial object unknown. Earlier window shows apparent plank lift f20–28. | Form moves toward plank f0–5 and back near gripper f10–12. Contact, continuity and reattachment unknown. [Evidence](pair_b1_s4/), [plank window](README.md) |
| ball 2 / 1 | Form enters top f81; origin and identity unknown across off-screen interval. | Form appears larger by f96–116; depth and identity unknown. [Control](clip13/), [mid](clip01/) |
| ball 2 / 2 | Form visible f64 and absent f65; similar form f144 fades and is absent f146. Identity and relationship unknown. | Form indistinct against plank near f12; apparent height changes through f188. Contact and continuity unknown. [Control](pair_b2_s2/), [mid](clip04/) |
| ball 2 / 3 | Initial form indistinct; larger form visible f24; relationship unknown. | Form indistinct near plank f12–24; later apparent height changes. Contact and continuity unknown. [Evidence](pair_b2_s3/) |
| ball 2 / 4 | Large form enters top f11; relationship to indistinct initial object unknown. | Form indistinct near plank f3–5 and f17–19; contact and continuity unknown. [Evidence](pair_b2_s4/) |

These observations do not establish a continuous single-object trajectory, reattachment, clone incidence, physical size change, impacts, restitution, or settling. Apparent height changes are not a calibrated physics measure. The entry and fade examples motivate checking track continuity before estimating trajectories; low contrast, perspective, occlusion, off-screen intervals and sparse sampling leave multiple interpretations possible. No comparable event-rate or causal arm contrast can be inferred from this opportunistic review. The mid input is a later real frame and is diagnostic only under charter rule 7; it is not an admissible first-frame-only recipe.

For a usable comparison, preregister event definitions and missingness, blind a fresh coder to arm where feasible, inspect every relevant native frame, retain unknowns, and validate a suitable measure before claiming a quantitative result. Existing full-frame samples and selected native windows are evidence for inspection, not exhaustive labels.
