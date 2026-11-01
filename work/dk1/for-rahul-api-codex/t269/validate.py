"""CPU validation of phase_start (board #5619) requested by rahul-api-codex. Run: python -I validate.py <dir of phase_start.py>"""
import sys, json, math
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else '.')
import torch
from phase_start import phase_start
torch.manual_seed(0)
R = {}
def E(t): return float(t.double().square().sum())
def fftE(t, d): return float((torch.fft.fft(t.double(), dim=d, norm='ortho').abs()**2).sum())
cases = []
for T in (7, 8, 23, 24, 25):
    for layout in ('CTHW', 'BCTHW'):
        for dt in (torch.float64, torch.float32):
            for alpha in (1, 3, T // 2):
                for gamma in (1.0, 3.0, 30.0):
                    cases.append((T, layout, dt, alpha, gamma))
WORST = {str(d): dict(parseval_rel=0., fft_parseval_rel=0., mag_phase_vs_atten=0., donor_phase=0., low_mag=0., high_mag=0.) for d in (torch.float64, torch.float32)}
for T, layout, dt, alpha, gamma in cases:
    worst = WORST[str(dt)]
    shp, td = ((16, T, 6, 10), 1) if layout == 'CTHW' else ((1, 16, T, 6, 10), 2)
    noise = torch.randn(shp, dtype=torch.float64).to(dt); ref = torch.randn(shp, dtype=torch.float64).to(dt) * 3 + 0.5
    for rp in (True, False):
        out = phase_start(noise, ref, time_dim=td, alpha=alpha, gamma=gamma, replace_phase=rp)
        assert out.shape == noise.shape and out.dtype == noise.dtype
        worst['parseval_rel'] = max(worst['parseval_rel'], abs(E(out) / E(noise) - 1))
        worst['fft_parseval_rel'] = max(worst['fft_parseval_rel'], abs(fftE(out, td) / fftE(noise, td) - 1))
    op = phase_start(noise, ref, time_dim=td, alpha=alpha, gamma=gamma, replace_phase=True)
    oa = phase_start(noise, ref, time_dim=td, alpha=alpha, gamma=gamma, replace_phase=False)
    F = lambda t: torch.fft.rfft(t.double().movedim(td, -1), dim=-1, norm='ortho')
    Zp, Za, Z, Q = F(op), F(oa), F(noise), F(ref)
    worst['mag_phase_vs_atten'] = max(worst['mag_phase_vs_atten'], float((Zp.abs() - Za.abs()).abs().max() / Z.abs().max()))
    # low band: phase = donor phase, magnitude = |z|/gamma; high band: beta*|z| with phase kept
    m = Q[..., :alpha].abs() > 1e-6
    dph = torch.angle(Zp[..., :alpha] * Q[..., :alpha].conj())[m].abs()
    worst['donor_phase'] = max(worst['donor_phase'], float(torch.minimum(dph, 2 * math.pi - dph).max()))
    worst['low_mag'] = max(worst['low_mag'], float((Zp[..., :alpha].abs() - Z[..., :alpha].abs() / gamma).abs().max() / Z.abs().max()))
    ratio = (Zp[..., alpha:].abs() / Z[..., alpha:].abs().clamp_min(1e-9))
    worst['high_mag'] = max(worst['high_mag'], float(ratio.max() - ratio.min()))
R['n_cases'] = len(cases) * 2
R['worst_by_dtype'] = WORST
# alpha0 identity; self-reference gamma1 identity
n = torch.randn(16, 24, 6, 10, dtype=torch.float64)
R['alpha0_exact_equal'] = bool(torch.equal(phase_start(n, torch.randn_like(n), time_dim=1, alpha=0), n))
R['selfref_gamma1_maxabs'] = {T: float((phase_start(m_ := torch.randn(16, T, 6, 10, dtype=torch.float64), m_, time_dim=1, alpha=3, gamma=1.0) - m_).abs().max()) for T in (23, 24)}
R['atten_gamma1_maxabs'] = float((phase_start(n, torch.randn_like(n), time_dim=1, alpha=3, gamma=1.0, replace_phase=False) - n).abs().max())
# Nyquist double-weight bug reproduction (all non-DC bins weight 2) at T=24 alpha3 gamma30 on a deterministic 256-row Gaussian
g = torch.Generator().manual_seed(0); x = torch.randn(256, 24, generator=g, dtype=torch.float64)
z = torch.fft.rfft(x, dim=-1, norm='ortho'); w = torch.full((13,), 2., dtype=torch.float64); w[0] = 1
p = z.abs().square() * w; low, high = p[..., :3].sum(), p[..., 3:].sum()
beta = ((low + high - low / 900) / high).sqrt(); mz = z.clone(); mz[..., :3] /= 30; mz[..., 3:] *= beta
R['naive_nyquist_weight_energy_retained_T24'] = float(E(torch.fft.irfft(mz, n=24, dim=-1, norm='ortho')) / E(x))
R['corrected_energy_retained_T24'] = float(E(phase_start(x, torch.randn(256, 24, generator=g, dtype=torch.float64), time_dim=1, alpha=3, gamma=30.0, replace_phase=False)) / E(x))
# guards
errs = {}
for name, kw in dict(alpha_too_big=dict(alpha=13), gamma_lt1=dict(gamma=0.5), alpha_float=dict(alpha=2.5), alpha_bool=dict(alpha=True)).items():
    try: phase_start(n, n, time_dim=1, **kw); errs[name] = 'NO ERROR'
    except ValueError as e: errs[name] = 'ValueError'
try: phase_start(n, n[:, :23], time_dim=1); errs['shape_mismatch'] = 'NO ERROR'
except ValueError: errs['shape_mismatch'] = 'ValueError'
R['guards'] = errs
R['zero_ref_phase_fallback_equals_atten'] = float((phase_start(n, torch.zeros_like(n), time_dim=1, alpha=3) - phase_start(n, torch.zeros_like(n), time_dim=1, alpha=3, replace_phase=False)).abs().max())
R['torch'] = torch.__version__
print(json.dumps(R, indent=1))
