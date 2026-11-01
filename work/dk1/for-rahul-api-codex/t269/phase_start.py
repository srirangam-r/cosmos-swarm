# Verbatim copy of rahul-api-codex's reference candidate (board #5619, task 269). Not modified.
import math
import torch

@torch.no_grad()
def phase_start(noise, ref, *, time_dim, alpha=3, gamma=30.0,
                replace_phase=True):
    """One video tensor; alpha selects rFFT bins [0,alpha), including DC.
    Explicit time_dim: CTHW->1, BCTHW->2 only when B==1.
    replace_phase=False is the matched spectral-attenuation control.
    """
    if noise.shape != ref.shape or noise.device != ref.device:
        raise ValueError("noise/ref must have identical shape and device")
    if not noise.is_floating_point() or not ref.is_floating_point():
        raise ValueError("real floating tensors required")
    if not bool(torch.isfinite(noise).all() & torch.isfinite(ref).all()):
        raise ValueError("nonfinite input")
    if not math.isfinite(gamma) or gamma < 1:
        raise ValueError("gamma must be finite and >=1")
    x = noise.movedim(time_dim, -1)
    r = ref.movedim(time_dim, -1)
    n = x.shape[-1]
    if isinstance(alpha, bool) or int(alpha) != alpha:
        raise ValueError("alpha must be an integer")
    alpha = int(alpha)
    if not 0 <= alpha < n // 2 + 1:
        raise ValueError("keep at least one high-frequency bin")
    if alpha == 0:
        return noise.clone()
    dtype = torch.float64 if noise.dtype == torch.float64 else torch.float32
    z = torch.fft.rfft(x.to(dtype), dim=-1, norm="ortho")
    q = torch.fft.rfft(r.to(dtype), dim=-1, norm="ortho")
    weights = torch.full((z.shape[-1],), 2., device=z.device, dtype=dtype)
    weights[0] = 1.
    if n % 2 == 0:
        weights[-1] = 1.  # Nyquist is self-conjugate, not mirrored.
    p = z.abs().double().square() * weights
    low = p[..., :alpha].sum()
    high = p[..., alpha:].sum()
    if not bool(high > 0):
        raise ValueError("cannot compensate: high-band energy is zero")
    beta = ((low + high - low / gamma**2) / high).sqrt().to(dtype)
    mixed = z.clone()
    if replace_phase:
        # Reference zeros carry no defined phase: keep the original phase.
        qabs = q.abs()
        unit = q / qabs.clamp_min(1e-12)
        donor = z.abs() * unit
        donor = torch.where(qabs > 1e-12, donor, z)
        mixed[..., :alpha] = donor[..., :alpha]
    mixed[..., :alpha] /= gamma
    mixed[..., alpha:] *= beta
    out = torch.fft.irfft(mixed, n=n, dim=-1, norm="ortho")
    return out.movedim(-1, time_dim).to(noise.dtype)
