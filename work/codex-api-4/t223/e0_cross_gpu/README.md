# E0 independent native-video correspondence audit

Task 223. This independently decodes the owner's **same 32 original videos**
using analysis code fixed before Program N outcomes. It tests seed
correspondence in pixel motion; it does not measure a physical constant, improve
the model, or prove exact noise/output equality.

The protocol, distance implementation, bootstrap and permutation core remain
byte-identical to 077a68c. Aggregate report #4786 was known before this audit.
GPU-pair mapping was fixed in #4818 before opening individual artifacts; targets
were located from owner design files published in 1fbefbc, then fixed in #4840
before target access. That design mapping is not blind to the aggregate report.
The earlier q8-only snapshot remains in e0_partial; this follow-up adds targets
without changing that snapshot's results.

The owner generated CPU seeds 101–108 on q8, L40S and A6000; CUDA seeds 101–104
exist only on q8 and L40S. The actual 32-row design is complete, with no dropped
clips. The conservative six-member family from #4818 retains the two unplanned
A6000 CUDA comparisons as untested (display p=null, internal p=1). These are not
missing or failed generations. Four native-video comparisons are measured;
executed-noise and runtime authentication remain pending.

`results.json` contains every original video hash, queue ID, native decode
contract, seed-ordered distance matrix, per-seed contribution, seed-cluster
bootstrap interval, wrong-seed column-permutation p-value, six-member Holm
adjustment and CPU-minus-CUDA paired secondary contrast. No GPU-pair observations
are pooled into a fictitious n=24; each CPU comparison has eight seed clusters.
There are 56 ordered different-seed entries per matrix, not 56 independent seeds.

The metric is the original full-frame grayscale temporal-change MAE after area
resize to 208×120. It includes f1−f0 but does not compare frame 0 directly. Units
are fractions of full grayscale range; multiply by 255 for gray levels.
Inference uses 2000 whole-seed bootstrap draws, seed20261101, and 9999 column
permutations with plus-one p, seed20261102. Four-seed CUDA permutations are all
24 exact assignments. A separate scalar enumeration verifies that exact p.
Undefined bootstrap samples are counted. No equivalence threshold was invented.

Every request is joined to the owner's published E0 jobs and the design-only
queue snapshot. Native dimensions/frame count/fps pass on all 32 files. Three
independent FFmpeg decodes, explicit RGB luma and direct 4×4 block area averaging
check the first two changes on CPU seed101 for each GPU label. Same-GPU
different-seed matrices provide background/prevalence controls. Within-file
zero-distance checks are explicitly **not independent same-host regenerations**;
the latter are unavailable.

The queue records contain the requested noise device, not the native server's
executed-noise record. See the pinned queue implementation in e0_partial.
Original input-file hashes, sampled-noise shape/dtype/hash, native sidecars,
checkpoint/runtime revisions and actual sigma sequences have not been provided.
Image basenames and request parameters match; this alone does not authenticate
input bytes or execution. Source/charter default is Karras with flow_shift
ignored, despite request flow_shift=10. Actual sampler execution is unverified.

Consequently the analysis can corroborate **correspondence between the tested
clips submitted with CPU noise**, while tensor identity and an unrestricted
license to pair arbitrary stacks/queue endpoints do not follow. This does not
establish that all old cross-GPU disagreement came from CUDA's SM-dependent RNG,
or that GPU numerics have no effect. No physics/planted validation or NVIDIA
scoreboard conclusion is claimed. One real GAUGE ball frame and one F prompt
were tested; transfer to other scenes and tasks is untested here.

To replay, create two local artifact directories, `q8` and `targets`. For each
object in queue_records.json, fetch its video from the announced queue:
`http://100.111.167.68:8030/jobs/<id>/mp4`, verify its hash in results.json,
and write the object to `<name>.queue.json` using
`json.dumps(object, indent=2) + '\n'`. Save video bytes as `<name>.mp4` in q8
when its name contains `_q8_`, otherwise targets. No new generation is needed.

```bash
python3 run.py q8 targets --out replay
```

Requires Python, NumPy, OpenCV and FFmpeg. The frozen parent core/adapter and
e0_partial/q8_design_only.json must accompany this directory. Native videos
remain accessible through the announced shared queue; they are not copied to
other agents' private directories. Full matrices also support statistical replay
without video download. See SUMMARY.md for values and verification.json for
replay checks. No E1–E4 outcomes were opened during this unit.
