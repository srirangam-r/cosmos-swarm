# Task 192: independent blur-result review

2026-11-01, codex-api-4. Fixed before opening source per-clip labels,
key, individual outcomes or movies. The aggregate finding #4104 is known.
This is a same-video review, with one unvalidated LLM coder, not new seeds
or a planted-validated physical result. Blur can remain visually recognizable.

Use exactly the 24 task174 `clips_blur` movies shared at
`swarm@board.tail0c526a.ts.net:~/jobs/rahul-api/holder_rep/`.
Download source outputs but keep their contents unopened until coding freezes.
Assign randomly permuted opaque Q01..Q24 IDs; record mapping SHA256 before
viewing panels. Preserve native scale in fixed 320x360 crops around the ball
and landing region, plus full-frame overview. Review f0,4,..,92 and consecutive
followups on ambiguous transitions before freezing all labels.

Independent QC definitions (not automatically identical to author's):
- `original_descends`: Y only when the object at the original location can be
  continuously followed downward by at least its own diameter; N if clearly
  remains near that location; U for ambiguous identity, occlusion or long gaps.
- `hover`: Y if the original object remains suspended near its initial height
  throughout, including mild drift (less than one diameter). N if original
  definitely leaves by at least a diameter in any direction; U for identity
  ambiguity/disappearance. Do not call disappearance a fall.
- `clean_fall`: Y only for original-descends Y with a continuously identifiable
  single ball and no second ball/split/obvious reattachment or major identity
  deformation through the clip. N for a definite violation; U when sampling
  or occlusion cannot settle it. This strict definition is a secondary audit,
  and agreement with author depends on operational compatibility.
- `clone`: Y for two spatially separate ball-like objects visible at once;
  N only if no duplicate is visible across reviewed frames; U if ambiguous.
  Record frame evidence and uncertainty, not just binary labels.

Freeze independent codes with a git tag and SHA256 before opening the key,
source per-clip labels or metrics. Then independently reconstruct author's
published counts, matched per-seed discordances and one-sided exact sign
tests; report paired mean difference, seed SE and descriptive t7 95% interval.
Binary exact paired tests condition on discordant pairs; do not treat a
non-significant contrast as equivalence or evidence of no useful effect.
Add a descriptive seed-cluster percentile bootstrap and exact binomial bounds
on directional discordance. Missing independent codes are not negatives.

Audit source frozen-code hashes, prompt/negative/frames/fps/steps/guidance/
sampler declaration and seed/endpoint allocation. Check decoded shapes and
frame count. Check original input blur images and actual input contrast/
Laplacian dose after coding freezes; do not infer shared initial tensors from
metadata alone. Record all scripts, source snapshots, movie hashes and panels.
No cause, recipe benefit, equivalence, NVIDIA pass or population effect claim.

Layout note before outcomes: f0 of the first transferred b05/s1 movie was
opened only to locate the ball/plank (known arm, no later frames). Fixed crop
is x150:470,y30:390. Full-frame overviews catch departures from that crop.
Because original transfer is slow, panels will be generated from originals
on the shared machine in our own jobs directory, with hashes/contracts; no
source labels or key used. One original already downloaded, others remain
fetchable from the explicitly shared source. Initial rsync was cancelled
normally (exit130) after one movie, not a failed scientific run.
