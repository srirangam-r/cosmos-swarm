"""CPU test of action_cfg.py: the uncond pass gets the cond inputs with the contrast action; the CFG line then equals
v(a) + scale * (v(a) - v(a')); outside `steps` the step is unguided; the hook is removed afterwards. No diffusers needed.
Run: python3 -m unittest test_action_cfg -v"""
import types
import unittest

import torch

import action_cfg


class Linear(torch.nn.Module):
    """Stand-in transformer: velocity depends on text (input_ids), vision tokens and action tokens; records its inputs."""
    def __init__(self):
        super().__init__()
        self.seen = []

    def forward(self, input_ids=None, vision_tokens=None, action_tokens=None, **kw):
        self.seen.append(dict(input_ids=input_ids, action=action_tokens[0].clone()))
        return vision_tokens[0] * 0.5 + 0.1 * sum(input_ids) + action_tokens[0].sum() * torch.ones_like(vision_tokens[0])


def run(pipe, spec, a, steps=4, g=1.0, raw_dim=None):
    """Mimic Cosmos3OmniPipeline's loop: per step one cond call (cond text) then one uncond call (neg text), CFG combine."""
    x = torch.ones(2, 3)
    outs = []
    with action_cfg.installed(pipe, spec, raw_dim):
        for t in pipe.scheduler.timesteps:
            pipe.current_timestep = t
            c = pipe.transformer(input_ids=[5, 6, 7], vision_tokens=[x], action_tokens=[a])
            u = pipe.transformer(input_ids=[1, 2], vision_tokens=[x], action_tokens=[a])
            outs.append(u + g * (c - u))
    pipe.current_timestep = None
    return outs


def fake_pipe(steps=4):
    return types.SimpleNamespace(transformer=Linear(), scheduler=types.SimpleNamespace(timesteps=torch.linspace(900, 300, steps)),
                                 current_timestep=None)


class T(unittest.TestCase):
    a = torch.tensor([[0.2, -0.1, 0.0, 0.0], [0.4, 0.3, 0.0, 0.0]])  # [chunk=2, action_dim=4], raw width 2

    def v(self, act, ids=(5, 6, 7)):
        return torch.ones(2, 3) * 0.5 + 0.1 * sum(ids) + act.sum()

    def test_neg_contrast_all_steps(self):
        pipe = fake_pipe()
        spec = action_cfg.parse({"action_mode": "forward_dynamics", "action_cfg": {"scale": 2.0}}, 1.0, 4)
        outs = run(pipe, spec, self.a, g=1 + spec.scale)
        want = self.v(self.a) + 2.0 * (self.v(self.a) - self.v(-self.a))
        for o in outs:
            torch.testing.assert_close(o, want)
        unc = pipe.transformer.seen[1::2]
        self.assertTrue(all(s["input_ids"] == [5, 6, 7] for s in unc))  # uncond text replaced by cond text
        self.assertTrue(all(torch.equal(s["action"], -self.a) for s in unc))
        sm = action_cfg.summary(spec)
        self.assertEqual(sm["guided_steps"], [0, 1, 2, 3])
        self.assertEqual((sm["cond_calls"], sm["uncond_calls"]), (4, 4))
        self.assertFalse(pipe.transformer._forward_pre_hooks)  # removed

    def test_explicit_alt_padding_and_step_window(self):
        pipe = fake_pipe()
        spec = action_cfg.parse({"action_mode": "forward_dynamics", "action_cfg": {"scale": 1.0, "alt": [[1.0, 2.0]], "steps": [0, 2]}}, 1.0, 4)
        outs = run(pipe, spec, self.a, g=2.0, raw_dim=2)
        alt = torch.tensor([[1.0, 2.0, 0, 0], [1.0, 2.0, 0, 0]])  # repeated to chunk, zero-padded to action_dim
        torch.testing.assert_close(outs[0], self.v(self.a) + (self.v(self.a) - self.v(alt)))
        torch.testing.assert_close(outs[3], self.v(self.a))  # outside the window: unguided cond velocity
        self.assertEqual(action_cfg.summary(spec)["unguided_steps"], [2, 3])

    def test_identity_contrast_is_plain_cond(self):
        pipe = fake_pipe()
        spec = action_cfg.parse({"action_mode": "forward_dynamics", "action_cfg": {"scale": 3.0, "alt": self.a[:, :2].tolist()}}, 1.0, 4)
        outs = run(pipe, spec, self.a, g=4.0, raw_dim=2)
        for o in outs:  # a' == a  ->  guidance term vanishes exactly
            torch.testing.assert_close(o, self.v(self.a))

    def test_parse_rejections(self):
        ok = {"action_mode": "forward_dynamics"}
        bad = [({**ok, "action_cfg": {"scale": 1}}, 6.0), ({"action_cfg": {"scale": 1}}, 1.0),
               ({**ok, "action_cfg": {"scale": 0}}, 1.0), ({**ok, "action_cfg": {"scale": 1, "alt": "zero"}}, 1.0),
               ({**ok, "action_cfg": {"scale": 1, "steps": [3, 2]}}, 1.0), ({**ok, "action_cfg": {"scale": 1, "x": 1}}, 1.0),
               ({**ok, "internals": {}, "action_cfg": {"scale": 1}}, 1.0)]
        for extra, g in bad:
            with self.assertRaises(ValueError, msg=str(extra)):
                action_cfg.parse(extra, g, 4)
        self.assertIsNone(action_cfg.parse(ok, 1.0, 4))


if __name__ == "__main__":
    unittest.main()
