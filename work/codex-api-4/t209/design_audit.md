# What the v8 intervention can identify

These are design deductions, fixed without seeing the v8 movies or per-clip eye codes. Source declaration: `work/ro-1/switch_probe/README.md`, server source and ten v8 job requests. Source source-hash and CPU checks are in `hook_audit.json`.

The arms use QT text for [0,35), [0,3), [0,7), [7,35), and [17,35), with F text elsewhere, on two selected seeds. These switch the whole F/QT text pack. F already says the ball eventually comes to rest. The semantic contrast bundles bounce count, decay rate, explicit deadline and persistent rest; it does not separately insert a previously absent rest concept.

Comparing [7,35) to [17,35) changes conditional text at steps7..16. The same text is supplied subsequently, but the generated latent states after step16 may differ. A resulting outcome difference would therefore be a total effect of this history contrast, with downstream propagation. It would not imply that only those steps execute rest, that later steps cannot affect it, or that [7,17) alone is sufficient. The [7,17)-only arm is absent from v8. A [0,3) failure versus [0,7) success at one seed would point to an effect of adding3..6 in that history, with the same limitations.

Dose and location change together in prefix arms (3 vs7 steps) and suffix arms (28 vs18 steps). There is no same-width late vs early matched contrast. A null on a late insertion can arise from insufficient cumulative effect or inability to overwrite an earlier trajectory; it is not evidence that every possible late prompt or activation intervention fails.

The prefix arms are QT→F deletion probes at steps3 and7; the suffix arms are F→QT insertion probes at7 and17. Insertion and deletion have different histories, and the grids are incomplete (no deletion at17, or insertion at3). Their endpoints cannot by themselves locate a universal commitment point or exclude outcome-specific windows. A window in denoising index also depends on the executed schedule; the quoted sigmas are approximations, not native step logs in the published package.

Two seeds give at most two independent paired outcome units per contrast. Even two discordant pairs in the same direction yield two-sided exact sign/McNemar p=0.5. For a descriptive success rate of2/2, the two-sided95% binomial exact interval is[0.1581,1]; for0/2 it is[0,0.8419]. These are illustrative per-arm intervals under independent random seeds, not simultaneous intervals or evidence that the selected seeds are a random representative sample. Two-sided exact intervals for1/2 are[0.01258,0.98742]. Zero observed differences do not establish equivalence.

## Source mechanism

The published hook counts transformer forward calls, assumes exactly conditional then unconditional once per denoising step, and replaces specified static text/position/index fields only for even-numbered calls in a half-open interval. The separate generator for the1-step capture avoids advancing the main seeded generator in the shown code; the scheduler is rebuilt after capture. This is consistent with the requested design under that calling contract.

Our executable CPU check extracts the exact `_fwd`, `_Cap` and `_STATIC` AST. It checks capture abort, all declared windows across70 stub forward calls, untouched dynamic arguments, nonmutation of incoming kwargs, and disabled passthrough. It proves those source-level facts only. It does not instantiate the pipeline or validate text/vision packing, real forward order, actual live deployment or GPU execution.

The source includes a server-native `prompt_switch_cond_steps` count and a deployment shell that runs an exact decoded-frame comparison of SWfull vs prior QT at both seeds. Its existence is not a completed run log. Published score files embed client-request metadata (server clip id and model label), not these native step counts or a logged sigma vector. The claimed identity control, if independently verified, supports the full-window substitution at those sampled requests; it alone cannot validate the partial windows or step indexing.

Needed for stronger execution provenance: shared untouched originals, native server sidecars with observed counts, deployment source hash/log, actual conditional/unconditional call+step records, executed sigma grid and pinned model/diffusers versions. Per-request input/noise hashes would strengthen paired stack provenance. Missing fields are uncertainty, not evidence of a malfunction.

## Later source availability update (after initial audit, before QC unblinding)

Author #4329 published f694d78: all10 v8 MP4s and client JSON records, an identical claimed executed source snapshot and chain_v8.out with deploy/health/identity lines. Matched F/QT s3 were already published; s5 controls were fetched from the exact board-shared cause_v5 location announced in task22. We independently verified both original-MP4 byte identity and decoded RGB identity for full vs QT at both seeds. All14 decoded first frames also match. This replaces the original package-availability limitation; it does not authenticate input upload bytes or initial random tensors.

The JSON records in the native folder are client request records. The published source explicitly writes a separate server-native JSON including `prompt_switch_cond_steps`, `torch`, `scheduler`, `frames_out` and `out_hw`. Those fields are absent from the shared client records. Thus the author's statement that the server does not log a used-step count conflicts with the claimed executed source. Clarification/server-native records were requested in #4374. Missing records do not demonstrate a hook failure. No executed sigma array or pinned model/diffusers revision is supplied.

## Author clarification #4383
Author confirms the shared native/*.json are client request records and the actual server-native JSONs contain the execution-count fields. They were not yet copied to the repo and will be shared next shift. The source discrepancy is therefore a provenance-availability gap, not an author claim that those fields were never written. No server-native count has been independently checked here.

Editorial correction after QC freeze: the first draft mistakenly called the prefix arms absent deletion probes. They are QT→F deletion probes at3 and7; the paragraph above corrects that statement. Frozen visual codes and protocol were unchanged.
