"""Does a ref with a clean conditioning latent in slot 0 (as in Nano I2V latents / inverted noise) imprint
a band-edge ringing on the start noise? Compare per-frame mean of output: full-T transform vs frames 1..T-1 only
(the d66b830 latent.band convention). Synthetic: ref = Gaussian, slot 0 = Gaussian*0.3 + 0.47 (E6 A_rec01 channel DC)."""
import json, torch
from phase_start import phase_start
torch.manual_seed(0)
R = {}
for T in (24, 23):
    x = torch.randn(16, T, 60, 104); r = torch.randn_like(x)
    r[:, 0] = 0.3 * r[:, 0] + 0.47
    full = phase_start(x, r, time_dim=1, alpha=3, gamma=30.0)
    skip = x.clone(); skip[:, 1:] = phase_start(x[:, 1:], r[:, 1:], time_dim=1, alpha=3, gamma=30.0)
    base = phase_start(x, torch.randn_like(x), time_dim=1, alpha=3, gamma=30.0)
    f = lambda o: [round(float(v), 4) for v in o.mean(dim=(0, 2, 3))]
    R[f"T{T}"] = {"per_frame_mean_full": f(full), "per_frame_mean_skip_slot0": f(skip), "per_frame_mean_gaussian_ref": f(base),
                  "max_abs_frame_mean_full": max(map(abs, f(full))), "max_abs_frame_mean_skip": max(map(abs, f(skip))),
                  "max_abs_frame_mean_gaussref": max(map(abs, f(base)))}
print(json.dumps(R, indent=1))
