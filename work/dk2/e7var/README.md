# E7 / latent.band slot-0 fix: per-latent-frame noise variance (dk2, no GPU)

Both of Raj's frame-0 fixes, E7 v2 client side (`dC[:, :, 0] = fresh[:, :, 0]`, run_e7.py 9dd4fc8) and the server
(`x_k[:, :, 0] = fill[:, :, 0]`, latent.py d66b830), fill donor slot 0 from the same fill noise that also supplies the out-of-band part.
For iid unit Gaussians that shared source correlates the two parts, so the mixed noise is not unit variance near the conditioning slot.
This is rahul-4's #5680/#5683 point, computed here for each E7 band (exact linear algebra, plus a 200k-sample Monte Carlo check):

| band (E7 arms) | latent frames below 0.97 | min var (frames 1..23) | frame 0 |
|---|---|---|---|
| \|k\|<=3 (tlo_fix, tlo_phrand*, tlo_shuf*) | 1, 2, 22, 23 | 0.8717 (frames 1, 23), 0.9516 (2, 22) | 1.41 (replaced by cond) |
| \|k\|<=6 (low_C, low_W) | 1, 23 | 0.7997 | 1.50 |
| 3<=\|k\|<=6 (osc_C, osc_W) | 2, 3, 21, 22 | 0.9191 | 1.44 |

Replacing slot 0 with a separately seeded independent N(0,1) instead gives variance exactly 1 at every frame.
(*phrand and shuf use the same mask but transform the donor, so their values differ; not computed here.)

Size: the deficit is a variance dip with no mean offset, localized at latent frames 1-2 and 22-23 (video frames ~1-8 and ~85-92).
The E6 washout came from a DC offset ringing through the whole clip (rms 0.47), so this effect is much smaller and of a different kind.
It is still a difference between the donor arms and up_fresh that up_fresh does not control for. C-vs-W pairs share it, so they stay matched.

Suggested one-line change (future runs only; E7 is frozen): `dC[:, :, 0] = np.random.default_rng(10_000 + s).standard_normal(dC[:, :, 0].shape)`,
and in latent.py `x_k[:, :, 0] = randn_like_seed(shape, seed + 9999, dev)[:, :, 0]`.

Files: varprofile.py (run: `python3 -I varprofile.py > varprofile.json`), varprofile.json.
