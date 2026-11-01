"""prompt_switch on CPU: a real tiny Cosmos3OmniTransformer in a fake pipeline that runs the denoising loop like the
real one (per step: conditional pass, then unconditional). Run: CUDA_VISIBLE_DEVICES= python test_prompt_switch.py"""
import tempfile
import unittest
from pathlib import Path

import torch

import internals
import loss_probe
from fakes import C, FakePipe, hooks_left

TOKENS = {"A": [5, 6, 7, 8, 9], "B": [5, 6, 7, 8, 9, 10, 11, 12, 13]}  # B is longer: the sequence layout changes


class LoopPipe(FakePipe):
    def __init__(self):
        super().__init__(steps=4)
        self.tokenize_prompt = lambda prompt, neg, **kw: (TOKENS.get(prompt, [3, 4]), [1, 2])
        self.latents = torch.randn(1, C, 3, 4, 6, generator=torch.Generator().manual_seed(11))

    def pack_for(self, prompt):
        return loss_probe.pack(self, self.latents, prompt, 24.0, 9, 64, 96, [0])[0]

    def __call__(self, prompt, num_inference_steps=None, generator=None, **kw):
        cond, uncond = self.pack_for(prompt), self.pack_for("negative")
        outs = []
        with torch.no_grad():
            for t in self.scheduler.timesteps[: num_inference_steps or len(self.scheduler.timesteps)]:
                self._current_timestep = t
                outs.append(loss_probe.predict(self, cond, self.latents, float(t) / 1000))
                outs.append(loss_probe.predict(self, uncond, self.latents, float(t) / 1000))
        self._current_timestep = None
        return outs


def env():
    return internals.Env(num_layers=3, hidden_size=32, num_steps=4, latent_frames=3,
                         artifacts=internals.ArtifactStore(Path(tempfile.mkdtemp())))


def run_switched(pipe, base, other, step_range=None):
    raw = {"prompt_switch": {"prompt": other, **({"step_range": step_range} if step_range else {})}}
    spec = internals.parse(raw, env())
    spec.prompt_switch["pack"] = internals.capture_text_pack(pipe, {"prompt": base}, other)
    with internals.installed(pipe, spec) as rec:
        outs = pipe(base)
    return outs, rec


class PromptSwitch(unittest.TestCase):
    def setUp(self):
        self.pipe = LoopPipe()

    def test_validation(self):
        for bad in ({"prompt": ""}, {"prompt": 3}, {"prompt": "B", "extra": 1}, {"prompt": "B", "step_range": [3, 2]}):
            with self.assertRaises(internals.InternalsError):
                internals.parse({"prompt_switch": bad}, env())
        s = internals.parse({"prompt_switch": {"prompt": "B", "step_range": [1, 3]}}, env())
        self.assertEqual(s.prompt_switch["range"], (1, 3))

    def test_capture_takes_the_conditional_pack_and_leaves_no_hooks(self):
        pack = internals.capture_text_pack(self.pipe, {"prompt": "A"}, "B")
        self.assertEqual(hooks_left(self.pipe), {})
        self.assertTrue(torch.equal(pack["input_ids"], self.pipe.pack_for("B")["input_ids"]))

    def test_full_range_reproduces_the_other_prompt_on_the_conditional_pass(self):
        outs, rec = run_switched(self.pipe, "A", "B")
        ref_b, ref_a = self.pipe("B"), self.pipe("A")
        for i in range(0, len(outs), 2):  # conditional passes: exactly prompt B
            self.assertTrue(torch.equal(outs[i], ref_b[i]))
        for i in range(1, len(outs), 2):  # unconditional passes: untouched
            self.assertTrue(torch.equal(outs[i], ref_a[i]))
        self.assertEqual(rec.summary()["prompt_switch_steps"], [0, 1, 2, 3])
        self.assertEqual(hooks_left(self.pipe), {})

    def test_step_range_limits_the_switch(self):
        outs, rec = run_switched(self.pipe, "A", "B", [1, 3])
        ref_b, ref_a = self.pipe("B"), self.pipe("A")
        for step in range(4):
            want = ref_b if step in (1, 2) else ref_a
            self.assertTrue(torch.equal(outs[2 * step], want[2 * step]), f"step {step}")
        self.assertEqual(rec.summary()["prompt_switch_steps"], [1, 2])

    def test_switching_to_the_same_prompt_is_a_noop(self):
        outs, _ = run_switched(self.pipe, "A", "A")
        self.assertTrue(all(torch.equal(x, y) for x, y in zip(outs, self.pipe("A"))))

    def test_composes_with_steering_and_cleans_up_after_failure(self):
        raw = {"prompt_switch": {"prompt": "B"}, "steer": {"alpha": 1.0, "vectors": [{"layer": 1, "values": [0.1] * 32}]}}
        spec = internals.parse(raw, env())
        spec.prompt_switch["pack"] = internals.capture_text_pack(self.pipe, {"prompt": "A"}, "B")
        with self.assertRaises(ZeroDivisionError):
            with internals.installed(self.pipe, spec):
                self.pipe("A")
                1 / 0
        self.assertEqual(hooks_left(self.pipe), {})


if __name__ == "__main__":
    unittest.main()
