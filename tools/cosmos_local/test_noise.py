"""noise.py on CPU: parsing, band masks, mixing and the randn_tensor swap (no model needed)."""
import sys, types

import pytest
import torch

import noise

SHAPE = (1, 4, 13, 12, 16)


def randn(seed):
    return torch.randn(SHAPE, generator=torch.Generator().manual_seed(seed))


def test_parse_rejects_bad_specs():
    assert noise.parse({}) is None
    assert noise.parse({"noise": {"device": "cpu"}}).device == "cpu"
    for bad in ({"device": "tpu"}, {"mix": {"band": "all"}}, {"mix": {"seed": 1, "band": "temporal_low"}},
                {"mix": {"seed": 1, "band": "region", "box": [0.5, 0, 0.2, 1]}}, {"extra": 1}, "cpu"):
        with pytest.raises(ValueError):
            noise.parse({"noise": bad})


@pytest.mark.parametrize("band", ["temporal_low", "spatial_low"])
def test_empty_and_full_bands(band):
    a, b = randn(1), randn(2)
    low_none = noise.mix_noise(a, b, {"band": band.replace("low", "high"), "cut": 1.0})  # B nowhere
    low_all = noise.mix_noise(a, b, {"band": band, "cut": 1.0})  # B everywhere (radius <= 0.5 for temporal)
    assert torch.allclose(low_none, a, atol=1e-5)
    assert torch.allclose(low_all, b, atol=1e-5)


def test_complementary_bands_split_the_noise_and_stay_white():
    a, b = randn(1), randn(2)
    lo = noise.mix_noise(a, b, {"band": "temporal_low", "cut": 0.3})
    hi = noise.mix_noise(a, b, {"band": "temporal_high", "cut": 0.3})
    assert torch.allclose(lo + hi, a + b, atol=1e-4)  # each frequency comes from exactly one seed
    big = torch.randn((2, 16, 24, 30, 52), generator=torch.Generator().manual_seed(3))
    big_b = torch.randn((2, 16, 24, 30, 52), generator=torch.Generator().manual_seed(4))
    m = noise.mix_noise(big, big_b, {"band": "spatial_low", "cut": 0.4})
    assert abs(m.mean()) < 0.01 and abs(m.std() - 1) < 0.01


def test_region_takes_b_inside_the_box_only():
    a, b = randn(1), randn(2)
    m = noise.mix_noise(a, b, {"band": "region", "box": [0.5, 0.0, 1.0, 0.5]})
    assert torch.equal(m[..., :6, 8:], b[..., :6, 8:]) and torch.equal(m[..., 6:, :], a[..., 6:, :])


def test_installed_swaps_only_the_first_vision_noise():
    calls = []

    def fake_randn(shape, generator=None, device=None, dtype=None):
        calls.append(tuple(shape))
        return torch.randn(shape, generator=generator, dtype=torch.float32).to(dtype or torch.float32)

    mod = types.ModuleType("fake_pipe_mod"); mod.randn_tensor = fake_randn; sys.modules["fake_pipe_mod"] = mod
    Pipe = type("Pipe", (), {"__module__": "fake_pipe_mod"})
    spec = noise.parse({"noise": {"device": "cpu", "mix": {"seed": 9, "band": "all"}}})
    with noise.installed(Pipe(), spec):
        v = mod.randn_tensor(SHAPE, generator=torch.Generator().manual_seed(5))
        s = mod.randn_tensor((1, 8, 4), generator=torch.Generator().manual_seed(5))
    assert mod.randn_tensor is fake_randn and spec.used
    assert torch.equal(v, randn(9)) and s.shape == (1, 8, 4)
    with noise.installed(Pipe(), noise.parse({"noise": {"device": "cpu"}})):
        assert mod.randn_tensor is fake_randn  # no mix: nothing is patched
