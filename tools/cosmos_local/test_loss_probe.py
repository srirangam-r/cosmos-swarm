"""CPU tests for loss_probe.py (tiny real transformer in a fake pipeline). Run: python test_loss_probe.py"""
import sys, unittest
from pathlib import Path

import numpy as np
import torch
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import loss_probe as lp
from fakes import FakePipe, C

H, W, NF = 64, 96, 9  # 9 frames -> 3 latent frames; 64x96 -> 4x6 latent -> 2x3 patches


def clip(seed=0):
    g = np.random.default_rng(seed)
    base = g.integers(0, 255, (H, W, 3))
    return np.stack([np.clip(base + 8 * t, 0, 255).astype(np.uint8) for t in range(NF)])


class FlowMaths(unittest.TestCase):
    def test_flow_inputs_and_target(self):
        z, e = torch.randn(1, C, 3, 4, 4), torch.randn(1, C, 3, 4, 4)
        noisy, target = lp.flow_inputs(z, e, 0.25)
        self.assertTrue(torch.allclose(noisy, 0.75 * z + 0.25 * e))
        self.assertTrue(torch.equal(target, e - z))
        mask = torch.zeros(3, 1, 1); mask[0] = 1
        noisy, _ = lp.flow_inputs(z, e, 0.25, mask)
        self.assertTrue(torch.equal(noisy[:, :, 0], z[:, :, 0]))  # conditioning frame stays clean
        with self.assertRaises(ValueError):
            lp.flow_inputs(z.double(), e, 0.25)

    def test_frame_losses(self):
        pred, target = torch.zeros(1, C, 3, 2, 2), torch.zeros(1, C, 3, 2, 2)
        target[:, :, 1] = 1.0
        target[:, :, 2] = 2.0
        loss, per = lp.frame_losses(pred, target, [1, 2])
        self.assertAlmostEqual(loss, 2.5)
        self.assertEqual(per, [None, 1.0, 4.0])

    def test_validate(self):
        s = lp.validate({}, 21)
        self.assertEqual((s["start"], s["num_frames"]), (0, 21))
        self.assertEqual(lp.validate({}, 22)["num_frames"], 21)
        for bad, n in (({"sigmas": [0, 0.5]}, 21), ({"sigmas": [0.5, 0.5]}, 21), ({"seeds": []}, 21), ({"variants": ["x"]}, 21),
                       ({"num_frames": 8}, 21), ({"num_frames": 21, "start": 4}, 21), ({"foo": 1}, 21), ({"fps": 0}, 21)):
            with self.assertRaises(lp.ProbeError, msg=str(bad)):
                lp.validate(bad, n)

    def test_variants(self):
        f = clip()
        self.assertTrue(np.array_equal(lp.make_variant(f, "reverse")[0], f[-1]))
        self.assertTrue(all(np.array_equal(x, f[0]) for x in lp.make_variant(f, "freeze_first")))


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.pipe = FakePipe()

    def settings(self, **kw):
        return lp.validate({"sigmas": [0.3, 0.7], "seeds": [1, 2], "variants": ["forward", "reverse", "freeze_first"], **kw}, NF)

    def test_t2v_result_shape_pairing_and_determinism(self):
        r = lp.run_probe(self.pipe, clip(), 24.0, "a ball", None, self.settings())
        self.assertEqual(len(r["rows"]), 2 * 2 * 3)
        self.assertEqual(r["latent_shape"], [1, C, 3, 4, 6])
        self.assertEqual(r["conditioning_frames"], [])
        for row in r["rows"]:
            self.assertEqual(len(row["per_frame"]), 3)
            self.assertTrue(np.isfinite(row["loss"]))
            self.assertAlmostEqual(row["loss"], float(np.mean(row["per_frame"])), places=5)  # equal-sized frames
        self.assertEqual(r["determinism_preflight"][0], r["determinism_preflight"][1])
        r2 = lp.run_probe(self.pipe, clip(), 24.0, "a ball", None, self.settings())
        self.assertEqual(r["rows"], r2["rows"])  # deterministic: same noise, same model
        self.assertIn("reverse_minus_forward", r["paired"])
        self.assertEqual(len(r["paired"]["reverse_minus_forward"]["mean_delta_per_frame"]), 3)
        json_ok = __import__("json").dumps(r, allow_nan=False)
        self.assertTrue(json_ok)

    def test_identical_clips_have_zero_paired_delta(self):
        sym = np.concatenate([clip()[:5], clip()[:4][::-1]])  # a palindrome: reverse == forward frame-for-frame
        r = lp.run_probe(self.pipe, sym, 24.0, "a ball", None, self.settings(variants=["forward", "reverse"]))
        self.assertAlmostEqual(r["paired"]["reverse_minus_forward"]["mean_delta"], 0.0, places=7)

    def test_same_noise_across_variants(self):
        r = lp.run_probe(self.pipe, clip(), 24.0, "a ball", None, self.settings())
        # freeze_first differs from forward, forward vs forward-with-another-seed differs: noise really is per-seed
        by = {(x["variant"], x["sigma"], x["seed"]): x["loss"] for x in r["rows"]}
        self.assertNotEqual(by[("forward", 0.3, 1)], by[("forward", 0.3, 2)])
        self.assertNotEqual(by[("forward", 0.3, 1)], by[("freeze_first", 0.3, 1)])

    def test_i2v_conditioning_image(self):
        img = Image.fromarray(clip(5)[0])
        r = lp.run_probe(self.pipe, clip(), 24.0, "a ball", img, self.settings(variants=["forward", "reverse"]))
        self.assertEqual(r["conditioning_frames"], [0])
        self.assertTrue(all(x["per_frame"][0] is None and x["per_frame"][1] is not None for x in r["rows"]))
        self.assertIsNone(r["summary"]["forward"]["mean_per_frame"][0])
        # overall loss is the mean over the 2 noisy frames only
        for x in r["rows"]:
            self.assertAlmostEqual(x["loss"], float(np.mean(x["per_frame"][1:])), places=5)
        t2v = lp.run_probe(self.pipe, clip(), 24.0, "a ball", None, self.settings(variants=["forward", "reverse"]))
        self.assertNotEqual(r["rows"][0]["loss"], t2v["rows"][0]["loss"])

    def test_image_from_video_frame0_pairs_the_conditioning(self):
        r = lp.run_probe(self.pipe, clip(), 24.0, "a ball", None, self.settings(variants=["forward", "reverse"], image_from_video_frame0=True))
        self.assertEqual(r["conditioning_frames"], [0])

    def test_rope_spec_changes_the_loss_and_is_restored(self):
        import internals
        base = lp.run_probe(self.pipe, clip(), 24.0, "a ball", None, self.settings())
        spec = internals.Spec(raw={}, rope={j: 0.5 for j in internals.temporal_indices(self.pipe.transformer.rotary_emb)})
        with internals.installed(self.pipe, spec):
            scaled = lp.run_probe(self.pipe, clip(), 24.0, "a ball", None, self.settings())
        again = lp.run_probe(self.pipe, clip(), 24.0, "a ball", None, self.settings())
        self.assertNotEqual(base["rows"][0]["loss"], scaled["rows"][0]["loss"])
        self.assertEqual(base["rows"], again["rows"])


if __name__ == "__main__":
    unittest.main()
