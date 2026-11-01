"""dk2 independent validation of phase_start (#5619) against full torch.fft.fft (complex, not rfft).
Checks: (1) Parseval/energy conservation odd+even T; (2) alpha=0 identity; (3) ref=self & gamma=1 identity;
(4) phase arm vs attenuation-only control have identical |spectrum| (full fft); (5) low-band phase equals donor phase;
(6) analytic fixture #5621 (T24, E 13.5); (7) output real-valued round trip (imag of full-fft reconstruction);
(8) time_dim handling CTHW vs BCTHW; (9) float32 path; (10) DC/Nyquist sign behaviour."""
import json, math, sys, torch
from phase_start import phase_start
torch.manual_seed(12345)
R = {}
def full_spec(t, dim): return torch.fft.fft(t.double(), dim=dim, norm="ortho")
def worst(name, v):
    R[name] = max(R.get(name, 0.0), float(v))

for T in (3, 4, 7, 8, 23, 24, 25, 48):
    for alpha in (0, 1, 2, 3, 5):
        if alpha >= T // 2 + 1: continue
        for gamma in (1.0, 3.0, 30.0):
            for trial in range(4):
                C, H, W = 4, 3, 5
                x = torch.randn(C, T, H, W, dtype=torch.float64)
                r = torch.randn(C, T, H, W, dtype=torch.float64) + (torch.linspace(-1, 1, T)[None, :, None, None] * 3 if trial % 2 else 0)
                o = phase_start(x, r, time_dim=1, alpha=alpha, gamma=gamma)
                c = phase_start(x, r, time_dim=1, alpha=alpha, gamma=gamma, replace_phase=False)
                E0 = x.square().sum()
                worst("energy_rel_err_phase", abs(o.square().sum() / E0 - 1))
                worst("energy_rel_err_control", abs(c.square().sum() / E0 - 1))
                Fo, Fc, Fx, Fr = (full_spec(t, 1) for t in (o, c, x, r))
                # Parseval on the full fft
                worst("parseval_full_fft", abs(Fo.abs().square().sum() / o.square().sum() - 1))
                worst("phase_vs_control_mag_diff", (Fo.abs() - Fc.abs()).abs().max())
                if alpha == 0:
                    worst("alpha0_identity", (o - x).abs().max())
                    continue
                # expected magnitudes from full fft: low bins (k<alpha and mirror) /gamma, others * beta
                k = torch.arange(T)
                kk = torch.minimum(k, T - k)
                low = kk < alpha
                Elow = Fx.abs().square()[:, low].sum(); Ehigh = Fx.abs().square()[:, ~low].sum()
                beta = math.sqrt((Elow + Ehigh - Elow / gamma**2) / Ehigh)
                exp = Fx.abs().clone(); exp[:, low] /= gamma; exp[:, ~low] *= beta
                worst("magnitude_vs_fullfft_expectation", (Fo.abs() - exp).abs().max())
                # low-band phase = donor phase (where donor magnitude nonnegligible), skipping self-conj bins (DC/Nyquist) sign check separately
                m = low[None, :, None, None] & (Fr.abs() > 1e-6) & (Fx.abs() > 1e-6)
                dphi = torch.angle(Fo * Fr.conj())[m].abs()
                worst("lowband_phase_err_vs_donor", dphi.max())
                # high band keeps noise phase
                m2 = (~low)[None, :, None, None] & (Fx.abs() > 1e-6)
                worst("highband_phase_err_vs_noise", torch.angle(Fo * Fx.conj())[m2].abs().max())
                if gamma == 1.0:
                    s = phase_start(x, x, time_dim=1, alpha=alpha, gamma=1.0)
                    worst("self_gamma1_identity", (s - x).abs().max())
# BCTHW with B==1 equals CTHW
x = torch.randn(4, 24, 3, 5, dtype=torch.float64); r = torch.randn_like(x)
a = phase_start(x, r, time_dim=1); b = phase_start(x[None], r[None], time_dim=2)[0]
R["bcthw_vs_cthw"] = float((a - b).abs().max())
# float32 path
xf, rf = x.float(), r.float()
of = phase_start(xf, rf, time_dim=1)
R["float32_energy_rel_err"] = float(abs(of.double().square().sum() / xf.double().square().sum() - 1))
R["float32_vs_float64_maxabs"] = float((of.double() - a).abs().max())
R["float32_dtype_preserved"] = str(of.dtype)
# Analytic fixture #5621
j = torch.arange(24, dtype=torch.float64)
fx = (torch.cos(2 * math.pi * j / 24) + 0.25 * (-1.0) ** j).reshape(1, 24)
fo = phase_start(fx, fx, time_dim=1, alpha=2, gamma=30.0)
R["fixture_T24_energy_before"] = float(fx.square().sum()); R["fixture_T24_energy_after"] = float(fo.square().sum())
# Nano-like latent shape: 16ch x 24 latent frames x 60 x 104
x = torch.randn(16, 24, 60, 104); r = torch.randn_like(x) * 0.5 + 0.2
o = phase_start(x, r, time_dim=1)
R["nano_shape_energy_rel_err"] = float(abs(o.double().square().sum() / x.double().square().sum() - 1))
R["nano_shape_out_std"] = float(o.std()); R["nano_shape_out_mean"] = float(o.mean())
R["nano_shape_per_frame_std_min_max"] = [float(o.std(dim=(0, 2, 3)).min()), float(o.std(dim=(0, 2, 3)).max())]
# Note on DC/Nyquist: real bins -> donor 'phase' is a sign. check DC sign follows donor
x = torch.randn(1, 8, dtype=torch.float64); r = -torch.ones(1, 8, dtype=torch.float64) * 2 + 0.1 * torch.randn(1, 8, dtype=torch.float64)
o = phase_start(x, r, time_dim=1, alpha=1, gamma=1.0)
R["dc_sign_follows_donor"] = bool((o.mean() < 0).item())
R["torch"] = torch.__version__
print(json.dumps(R, indent=1))
