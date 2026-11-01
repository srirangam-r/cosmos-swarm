# ro-3 task 25, shift 5: seed 2 and 61 f break "P ≈ 0.55·N" (follow-up to findings 525/550)

| clip | N | fps | seed | pend_acf P (f) | measure_pend v1 P (f) | by eye | notes |
|---|---|---|---|---|---|---|---|
| pend_fps24_s1 (shift 1) | 189 | 24 | 1 | 107.1 | 106 | - | clean single pendulum |
| pend_fps24_s2 | 189 | 24 | 2 | 56.7 (shallow min, check) | 52.2 (check) | repeat ~54 f | INVALID physics: rod/ball duplicate, two rods splay out (sheet_fps24_s2.jpg) |
| pend_fps24_61f_s1 | 61 | 24 | 1 | fail (<1 cycle) | 79.8 [68, 117] (check) | ~88 (right extreme f30, vertical f52-53) | one slow ~90° swing; pillarbox NOT outpainted |
| ro-1 pend_A_fps24_93f_s1 | 93 | 24 | 1 | 50.8 | - | - | from finding 525 |

Real period: 1.06 s = 25.4 f at 24 fps.
All of these are UNVALIDATED readings (pend_acf: formal referee FAIL on count; measure_pend v1 is planted-PASS but flags these "check").
`clips_more/` holds the clips and sidecars. The seed-2 189 f clip was recovered from the server output after its client was stopped. The request is identical to jobs.jsonl pend_fps24_s2 (prompt byte-identical).
