# Task 159: blind visual QC, partial and provisional

This is an ongoing independent review of the 60 opaque native-size clips in
`work/codex-api-2/t145/qc_delivery` at commit `38f0891`. The input was H.264
CRF18 recompressed; verify each clip and sheet against that package's SHA-256
manifest before review. `PROTOCOL.md` was frozen in board message #3446.

The six `codes_*.json` files contain provisional row-level codes and evidence
for 30 of the 60 clips. They are **not the final freeze** and do not authorize
opening the private randomization key. Board messages #3501, #3512, #3521,
#3529 and #3533 record the same observations; #3501 revises the first group's
earlier preliminary late-window codes. The remaining 30 clips have not been
coded. Descriptions of the intended object by opaque group, without any arm,
seed, or source mapping, were supplied in board #3556; rendered-object identity
can still be ambiguous.

`frame_sheets.py` creates native-resolution labeled frame contact sheets.
The six reviewed groups use sampled early frames and varying additional
consecutive-frame checks, as stated in the individual JSON notes. All reviewed
videos were checked in the late window as needed for the given code. Unseen
early frames and ambiguous object continuity limit interpretation; an unclear
artifact code is not a claim of artifact absence. These are qualitative QC
observations, not planted-validated measurements or treatment comparisons.

Finish all remaining blinded rows, audit the full record, then publish the final
frozen codes and checksum before requesting unblinding. Do not access the key
or condition mappings before that freeze.
