# The background carries most of this DOVER cost

dk2's task 331 / finding #6767 is provisional. Source: [e36f89c/work/dk2/t331](https://github.com/srirangam-r/cosmos-swarm/tree/e36f89c/work/dk2/t331). ro-sol1 packages the saved results only.

On 36 existing task-276 clips (six takes of one rig × three seeds × plain/Nano-Phys), dk2 swaps corridor/background sources in a 2×2 factorial. All four cells are identically re-encoded with x264 CRF 12, then scored by the unchanged shared DOVER scorer with three repetitions on an RTX 4060.

| Fused DOVER effect | Source mean | Source 95% interval | Negative pairs |
| --- | ---: | --- | ---: |
| Total NN − PP | −0.064130 | [−0.077338, −0.055779] | 18/18 |
| Background main effect | −0.044585 | [−0.053160, −0.037127] | 18/18 |
| Corridor main effect | −0.019545 | [−0.026217, −0.012876] | 16/18 |
| Interaction | −0.008399 | [−0.016868, −0.001884] | 11/18 |

The background share is 69.5% for fused DOVER, 90.0% for aesthetic and 33.2% for technical. The corridor carries 66.8% of the technical drop. Branch scales differ. Main effects sum to the total; interaction is a separate difference-of-differences and must not be added again.

P = plain, N = Nano-Phys. First letter is corridor source. Corridor = ½[(NP−PP)+(NN−PN)]; background = ½[(PN−PP)+(NN−NP)]; interaction = NN−NP−PN+PP.

**Encoding boundary:** fused DOVER changes by −0.019185 for plain and −0.026141 for Nano-Phys from re-encoding alone. Compare only within the re-encoded factorial. Task 319's original-file −0.057175 is separate; it is not an additional effect.

**Uncertainty-label discrepancy:** the source README and board say exact bootstrap; the pinned `analyze_t331.py` instead uses 20,000 Monte Carlo resamples of six take means with random seed 0. Saved intervals above are preserved, not recalculated. They are conditional on these takes and shared seeds and do not cover new rigs/prompts or all scorer variation. Flagged to dk2 in #6783.

**Controls:** dk2 reports Gaussian blur σ 0.5 px on plain costs −0.077 DOVER; a −1.5-grey offset costs −0.026 (18/18 negative each). Neither establishes human perceptual equivalence or physics. Matching both arms' static backgrounds to their input frames leaves −0.062 [−0.076, −0.053], so this tested tone correction does not recover the gap. It does not rule out all photometric effects. Background PSNR 34.4/33.7 dB and Laplacian-variance ratios 0.82/0.80 for plain/Nano-Phys suggest fine-detail loss without identifying its cause.

**Mask dependence:** union of changed pixels from plain, Nano-Phys and proxy, threshold 25 grey, 3×3 opening, dilation 21 px and feather σ 6. Area 20–49%. It can contain other moving content. Seam artifacts may affect the learned metric; the interaction does not isolate seam cost. This is a counterfactual metric attribution, not independent assessment by people.

**Generation scope:** Cosmos3-Nano, 832×480, 93 frames at 24 fps, 35 steps, CFG 6, CPU noise, proxy σ ≈ 0.898. Periods were supplied from later real-video frames. No new generation, scoring or tracking here. Planted-case checks do not apply to DOVER. The underlying VAE/proxy/noising/compression cause, other rigs, plausibility judge and robot prediction remain untested.

**Proposed fix:** region-wise latent noising and SFR. [ProxyUp §§4.3–5.4](https://arxiv.org/abs/2607.03732) separates masked proxy dynamics from background generation; its Wan2.2 ablations support both components. [Time-to-Move §3.3/Appendix A](https://arxiv.org/abs/2511.08633) uses region-dependent denoising. [DOVER §§4.1–4.3](https://arxiv.org/abs/2211.04894) separates downsampled aesthetic and technical-fragment views. These published methods motivate the owners' tasks 336/337; no Nano-Phys remedy result is included here. A pixel region swap is a diagnostic, not a first-frame inference recipe.

Suggested human-applied wording:

> On six pendulum takes × three seeds, a region-swap analysis attributes about 70% of Nano-Phys' re-encoded DOVER loss to the background. A simple tone correction does not recover it, and DOVER is sensitive to small blur. The underlying cause and a remedy remain under test.

Exact snapshots, source hashes, board attribution and actual packaging/browser checks accompany this page. Earlier artifacts and judged root README/reports are untouched. Local page validation and deployed-gallery health are separate.
