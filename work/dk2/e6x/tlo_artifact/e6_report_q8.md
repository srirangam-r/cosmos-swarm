# E6 report (task 250)

| arm | clips | period read | median P/P_real | within 10% | copy index | corr w/ target real |
|---|---|---|---|---|---|---|
| recon | 20 | 19 | 1.009 | 18 | None | 0.692 |
| base | 60 | 46 | 0.88 | 6 | None | 0.075 |
| tlo | 64 | 64 | 0.929 | 64 | -0.043 | -0.031 |
| slo | 64 | 56 | 0.998 | 30 | 0.185 | 0.093 |
| all | 32 | 27 | 1.001 | 24 | 0.213 | 0.117 |

recon = inverted real clip regenerated; base = plain Nano from the same frame; tlo/slo = donor's coarse band + fresh fill;
all = donor's full noise (copy control). copy index > 0: the clip moves like the DONOR recording rather than the target's real continuation.
