import torch, noise


def test_slot0_spike_leaks_without_flag_and_not_with_it():
    g = torch.Generator().manual_seed(0)
    a = torch.randn(1, 4, 24, 8, 8, generator=g); b = torch.randn(1, 4, 24, 8, 8, generator=g)
    b[:, :, 0] += 5.0  # a clean-latent-like channel offset in the conditioning slot
    mix = {"band": "temporal_low", "cut": 0.25}
    leak = noise.mix_noise(a, b, mix)[:, :, 1:].mean(dim=(3, 4)).abs().max()
    fixed = noise.mix_noise(a, b, dict(mix, skip_slot0=True))
    ref = noise.mix_noise(a[:, :, 1:], b[:, :, 1:], mix)
    assert leak > 0.5  # the bug: the slot-0 offset rings into frames 1+
    assert torch.allclose(fixed[:, :, 1:], ref) and torch.equal(fixed[:, :, :1], a[:, :, :1])


def test_default_unchanged():
    g = torch.Generator().manual_seed(1)
    a = torch.randn(1, 4, 24, 8, 8, generator=g); b = torch.randn(1, 4, 24, 8, 8, generator=g)
    m = {"band": "temporal_low", "cut": 0.25}
    dims = (2,)
    mask = noise.band_mask(tuple(a.shape), m)
    want = torch.fft.ifftn(mask * torch.fft.fftn(b, dim=dims) + (1 - mask) * torch.fft.fftn(a, dim=dims), dim=dims).real
    assert torch.allclose(noise.mix_noise(a, b, m), want)
