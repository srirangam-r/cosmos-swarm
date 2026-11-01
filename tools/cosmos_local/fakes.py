"""CPU test doubles: a REAL tiny Cosmos3OmniTransformer (same classes, attribute names and call signature as the 15B one)
inside a fake pipeline that only has what internals.py / loss_probe.py touch. No GPU, no weights."""
import types
from functools import partial

import numpy as np
import torch
from diffusers.models.transformers.transformer_cosmos3 import Cosmos3OmniTransformer
from diffusers.pipelines.cosmos.pipeline_cosmos3_omni import Cosmos3OmniPipeline

import loss_probe

torch.set_num_threads(1)  # tiny model: threads only add contention
C, HID, LAYERS = 4, 32, 3


def tiny_transformer(seed=0):
    torch.manual_seed(seed)
    return Cosmos3OmniTransformer(hidden_size=HID, intermediate_size=64, num_attention_heads=2, num_key_value_heads=1,
                                  head_dim=128, num_hidden_layers=LAYERS, latent_channel=C, patch_latent_dim=4 * C,
                                  vocab_size=100).eval()


def fake_encode(x):
    """[1,3,T,H,W] in [-1,1] -> [1,C,(T-1)//4+1,H//16,W//16]: causal like the Wan VAE (frame 0 alone, then groups of 4)."""
    g = torch.Generator().manual_seed(7)
    proj = torch.randn(C, 3, generator=g)
    chunks = [x[:, :, :1]] + [x[:, :, i:i + 4] for i in range(1, x.shape[2], 4)]
    lat = torch.cat([c.mean(2, keepdim=True) for c in chunks], dim=2)
    lat = torch.nn.functional.avg_pool3d(lat, (1, 16, 16))
    return torch.einsum("oc,bcthw->bothw", proj, lat)


class FakePipe:
    """Has the attributes the hooks and the probe use. `run_loop` mimics the denoising loop's transformer calls:
    per step one cond call, and (cfg=True) one uncond call, with `current_timestep` set like the real pipeline."""
    vae_scale_factor_temporal = 4

    def __init__(self, transformer=None, steps=4):
        self.transformer = transformer or tiny_transformer()
        self.scheduler = types.SimpleNamespace(timesteps=torch.linspace(900, 300, steps))
        self._current_timestep = None
        self.sched_steps = steps
        self.tokenize_prompt = lambda prompt, neg, **kw: ([5, 6, 7, 8, 9], [1, 2])
        self._prepare_text_segment = partial(Cosmos3OmniPipeline._prepare_text_segment, self)
        self._prepare_vision_segment = partial(Cosmos3OmniPipeline._prepare_vision_segment, self)
        self._encode_video = fake_encode

    @property
    def current_timestep(self):
        return self._current_timestep

    def _get_execution_device(self):
        return torch.device("cpu")

    def packed(self, T=3, ph=2, pw=3, cond=(0,)):
        latents = torch.randn(1, C, T, ph * 2, pw * 2, generator=torch.Generator().manual_seed(11))
        p, noisy = loss_probe.pack(self, latents, "x", 24.0, (T - 1) * 4 + 1, ph * 32, pw * 32, list(cond))
        return p, latents

    def call(self, packed, latents, sigma=0.5):
        return loss_probe.predict(self, packed, latents, sigma)

    def run_loop(self, packed, latents, cfg=True):
        outs = []
        with torch.no_grad():
            for t in self.scheduler.timesteps:
                self._current_timestep = t
                for _ in range(2 if cfg else 1):
                    outs.append(self.call(packed, latents, float(t) / 1000))
        self._current_timestep = None
        return torch.stack(outs)


def hooks_left(pipe):
    """Every forward / forward-pre hook still registered on the transformer tree (should be {} after a request)."""
    left = {}
    for name, m in pipe.transformer.named_modules():
        n = len(m._forward_hooks) + len(m._forward_pre_hooks)
        if n:
            left[name] = n
    return left
