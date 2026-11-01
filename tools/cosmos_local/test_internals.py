"""CPU tests for internals.py on a real tiny Cosmos3OmniTransformer. Run: python -m unittest -v test_internals (any python with
torch + the pinned diffusers; no pytest needed)."""
import io, os, sys, tempfile, unittest
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).parent))
import diffusers.models.transformers.transformer_cosmos3 as tc
import internals
from internals import InternalsError
from fakes import FakePipe, hooks_left, C, HID, LAYERS

T, STEPS = 3, 4


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = internals.ArtifactStore(Path(self.tmp.name))
        self.pipe = FakePipe(steps=STEPS)
        self.packed, self.latents = self.pipe.packed(T=T)
        self.orig_dispatch = tc.dispatch_attention_fn
        self.orig_inv = self.pipe.transformer.rotary_emb.inv_freq.clone()

    def tearDown(self):
        self.tmp.cleanup()

    def env(self, uploads=None, **kw):
        base = dict(num_layers=LAYERS, hidden_size=HID, num_steps=STEPS, latent_frames=T, artifacts=self.store,
                    uploads=uploads or {}, temporal=internals.temporal_indices(self.pipe.transformer.rotary_emb))
        return internals.Env(**{**base, **kw})

    def spec(self, raw, **kw):
        return internals.parse(raw, self.env(**kw))

    def go(self, raw=None, cfg=True, **kw):
        if raw is None:
            return self.pipe.run_loop(self.packed, self.latents, cfg), None
        spec = self.spec(raw, **kw)
        with internals.installed(self.pipe, spec) as rec:
            out = self.pipe.run_loop(self.packed, self.latents, cfg)
        return out, rec

    def assertRestored(self):
        self.assertEqual(hooks_left(self.pipe), {})
        self.assertIs(tc.dispatch_attention_fn, self.orig_dispatch)
        self.assertNotIn("forward", self.pipe.transformer.rotary_emb.__dict__)
        self.assertTrue(torch.equal(self.pipe.transformer.rotary_emb.inv_freq, self.orig_inv))


class RopeTests(Base):
    def test_temporal_indices_match_the_documented_layout(self):
        t = internals.temporal_indices(self.pipe.transformer.rotary_emb)
        self.assertEqual(t, list(range(0, 60, 3)) + [60, 61, 62, 63])

    def test_scale_one_is_a_noop_and_scale_changes_output(self):
        base, _ = self.go()
        same, _ = self.go({"rope": {"temporal_scale": 1.0}})
        self.assertTrue(torch.equal(base, same))
        self.assertRestored()
        half, _ = self.go({"rope": {"temporal_scale": 0.5}})
        self.assertFalse(torch.allclose(base, half, atol=1e-4))
        self.assertRestored()
        again, _ = self.go()
        self.assertTrue(torch.equal(base, again))

    def test_matches_editing_inv_freq_in_place_like_gen92(self):
        base_pipe = FakePipe(steps=STEPS)  # same seed -> same weights
        rot = base_pipe.transformer.rotary_emb
        scales = {0: 0.5, 3: 0.5}
        for j, s in scales.items():
            rot.inv_freq[j] *= s
        ref = base_pipe.run_loop(self.packed, self.latents)
        out, _ = self.go({"rope": {"temporal_scale": {"0": 0.5, "3": 0.5}}})
        self.assertTrue(torch.allclose(ref, out, atol=1e-6))

    def test_previous_instance_forward_is_restored_and_exceptions_clean_up(self):
        rot = self.pipe.transformer.rotary_emb
        sentinel = rot.forward  # pretend group offload installed its own wrapper
        rot.forward = sentinel
        with self.assertRaises(RuntimeError):
            with internals.installed(self.pipe, self.spec({"rope": {"temporal_scale": 2.0}})):
                raise RuntimeError("boom")
        self.assertIs(rot.__dict__["forward"], sentinel)
        del rot.__dict__["forward"]
        self.assertRestored()

    def test_validation(self):
        for bad in ({"temporal_scale": {"1": 0.5}}, {"temporal_scale": {"x": 1}}, {"temporal_scale": 0}, {"temporal_scale": {}},
                    {"nope": 1}):
            with self.assertRaises(InternalsError):
                self.spec({"rope": bad})


class ConditioningTests(Base):
    def test_noise_level_zero_is_noop_and_levels_change_output(self):
        base, _ = self.go()
        z, rec = self.go({"conditioning": {"noise": {"level": 0.0}}})
        self.assertTrue(torch.equal(base, z))
        self.assertRestored()
        n, rec = self.go({"conditioning": {"noise": {"level": 0.5, "seed": 3, "step_range": [1, 3]}}})
        self.assertFalse(torch.allclose(base, n, atol=1e-5))
        self.assertEqual(rec.noise_steps, {1, 2})
        n2, _ = self.go({"conditioning": {"noise": {"level": 0.5, "seed": 3, "step_range": [1, 3]}}})
        self.assertTrue(torch.equal(n, n2))  # deterministic
        n3, _ = self.go({"conditioning": {"noise": {"level": 0.5, "seed": 4, "step_range": [1, 3]}}})
        self.assertFalse(torch.equal(n, n3))
        self.assertRestored()

    def test_noise_touches_only_the_conditioning_frame_input(self):
        seen = []
        h = self.pipe.transformer.register_forward_pre_hook(lambda m, a, kw: seen.append(kw["vision_tokens"][0].clone()), with_kwargs=True)
        spec = self.spec({"conditioning": {"noise": {"level": 1.0, "seed": 1}}})
        try:  # our pre-hook is registered after the spy, so the spy sees the un-noised input; add a second spy after it
            with internals.installed(self.pipe, spec):
                h2 = self.pipe.transformer.register_forward_pre_hook(lambda m, a, kw: seen.append(kw["vision_tokens"][0].clone()), with_kwargs=True)
                self.pipe.run_loop(self.packed, self.latents)
                h2.remove()
        finally:
            h.remove()
        before, after = seen[0], seen[1]
        self.assertTrue(torch.equal(before[:, :, 1:], after[:, :, 1:]))  # noisy frames untouched
        eps = torch.randn(before.shape, generator=torch.Generator().manual_seed(1))
        self.assertTrue(torch.allclose(after[:, :, 0], eps[:, :, 0]))  # level 1 -> pure noise in frame 0
        self.assertTrue(torch.equal(self.latents, before))  # the caller's tensor is not edited in place

    def test_attention_scale_one_is_noop_zero_blocks_conditioning_keys(self):
        base, _ = self.go()
        one, rec = self.go({"conditioning": {"attention_scale": {"factor": 1.0}}})
        self.assertTrue(torch.allclose(base, one, atol=1e-5))
        self.assertTrue(rec.attn_steps)
        self.assertRestored()
        half, _ = self.go({"conditioning": {"attention_scale": {"factor": 0.5, "step_range": [0, 2], "layers": [0, 2]}}})
        self.assertFalse(torch.allclose(base, half, atol=1e-5))
        self.assertRestored()

    def test_attention_wrapper_maths(self):
        """factor f on the key columns of frame 0 for non-conditioning queries == softmax with log(f) added there."""
        und, S, F = 4, 6, 3
        L = F * S
        g = torch.Generator().manual_seed(0)
        q, k, v = (torch.randn(1, n, 2, 8, generator=g) for n in (L, und + L, und + L))
        st = internals._State()
        st.attn_on, st.und_len, st.S, st.T, st.cond_frames, st.step = True, und, S, F, (0,), 0
        spec = internals.Spec(raw={}, cond_attn=dict(factor=0.25, range=(0, 4), layers=[0]))
        out = internals._attn_wrapper(tc.dispatch_attention_fn, spec, st, internals.Recorder())(q, k, v, enable_gqa=False)
        qq, kk, vv = (x.permute(0, 2, 1, 3) for x in (q, k, v))
        logits = qq @ kk.transpose(-1, -2) / 8 ** 0.5
        bias = torch.zeros(und + L)
        bias[und:und + S] = np.log(0.25)
        ref_scaled = (torch.softmax(logits + bias, -1) @ vv).permute(0, 2, 1, 3)
        ref_plain = (torch.softmax(logits, -1) @ vv).permute(0, 2, 1, 3)
        self.assertTrue(torch.allclose(out[:, S:], ref_scaled[:, S:], atol=1e-5))  # later frames' queries: scaled
        self.assertTrue(torch.allclose(out[:, :S], ref_plain[:, :S], atol=1e-5))  # the conditioning frame's own queries: plain
        # factor 0: changing the conditioning frame's values must not move the other queries at all
        spec0 = internals.Spec(raw={}, cond_attn=dict(factor=0.0, range=(0, 4), layers=[0]))
        w = internals._attn_wrapper(tc.dispatch_attention_fn, spec0, st, internals.Recorder())
        v2 = v.clone(); v2[:, und:und + S] += 5
        a, b = w(q, k, v), w(q, k, v2)
        self.assertTrue(torch.allclose(a[:, S:], b[:, S:], atol=1e-6))
        self.assertFalse(torch.allclose(a[:, :S], b[:, :S], atol=1e-3))

    def test_cosmos_patch_chunking_accepts_the_key_bias(self):
        os.environ["COSMOS_QCHUNK"] = "5"
        import cosmos_patch
        try:
            g = torch.Generator().manual_seed(1)
            q, k, v = (torch.randn(1, n, 2, 8, generator=g) for n in (17, 20, 20))
            bias = torch.zeros(1, 1, 1, 20); bias[..., 4:9] = -1.5
            full = cosmos_patch._orig(q, k, v, attn_mask=bias)
            chunked = cosmos_patch._chunked(q, k, v, attn_mask=bias)
            self.assertTrue(torch.allclose(full, chunked, atol=1e-6))
        finally:
            tc.dispatch_attention_fn = cosmos_patch._orig  # undo the module-level patch for the other tests
            self.orig_dispatch = tc.dispatch_attention_fn

    def test_validation(self):
        for bad in ({}, {"noise": {}}, {"noise": {"level": 2}}, {"attention_scale": {"factor": -1}},
                    {"attention_scale": {"factor": 1, "layers": [9]}}, {"attention_scale": {"factor": 1, "step_range": [3, 3]}},
                    {"attention_scale": {"factor": 1, "step_range": [0, 99]}}, {"noise": {"level": 0.1}, "x": 1}):
            with self.assertRaises(InternalsError, msg=str(bad)):
                self.spec({"conditioning": bad})


class CaptureTests(Base):
    def test_capture_keys_shapes_and_values(self):
        raw = {"capture": {"layers": [0, 2], "step_range": [1, 4], "every": 2, "passes": ["cond", "uncond"], "full": True}}
        base, _ = self.go()
        out, rec = self.go(raw)
        self.assertTrue(torch.equal(base, out))  # capture is read-only
        self.assertRestored()
        keys = sorted(k for k in rec.arrays if k.endswith("_mean"))
        want = sorted(f"s{s:03d}_{p}_L{l:02d}_mean" for s in (1, 3) for p in ("cond", "uncond") for l in (0, 2))
        self.assertEqual(keys, want)
        self.assertEqual(rec.arrays["s001_cond_L00_mean"].shape, (T, HID))
        self.assertEqual(rec.arrays["s001_cond_L00_full"].shape, (T, 6, HID))
        self.assertEqual(rec.arrays["s001_cond_L00_full"].dtype, np.float16)
        np.testing.assert_allclose(rec.arrays["s001_cond_L00_full"].astype(np.float32).mean(1), rec.arrays["s001_cond_L00_mean"], atol=2e-2)
        # independent check of the value: layer 0 output of step 1 / cond branch, taken with a plain forward hook
        grab = {}
        h = self.pipe.transformer.layers[0].register_forward_hook(lambda m, a, o: grab.setdefault("n", []).append(o[1].clone()))
        self.pipe.run_loop(self.packed, self.latents)
        h.remove()
        ref = grab["n"][2][: T * 6].view(T, 6, HID).mean(1).numpy()  # calls: step0 cond, step0 uncond, step1 cond
        np.testing.assert_allclose(rec.arrays["s001_cond_L00_mean"], ref, atol=1e-6)

    def test_default_is_cond_only_and_cfg_off_works(self):
        _, rec = self.go({"capture": {"layers": [1]}}, cfg=False)
        self.assertEqual(sorted(rec.arrays), [f"s{s:03d}_cond_L01_mean" for s in range(STEPS)])

    def test_save_and_download_roundtrip(self):
        spec = self.spec({"capture": {"layers": [1], "step_range": [0, 1]}})
        with internals.installed(self.pipe, spec) as rec:
            self.pipe.run_loop(self.packed, self.latents)
        aid = internals.save_capture(self.store, rec, spec, {"seed": 1})
        self.assertRegex(aid, r"^act_[0-9a-f]{8}$")
        z = np.load(self.store.path(aid))
        self.assertEqual(z["s000_cond_L01_mean"].shape, (T, HID))
        self.assertIn("latent_frames", str(z["_meta"]))
        self.assertIsNone(self.store.path("../etc/passwd"))
        self.assertIsNone(self.store.path("act_ffffffff"))

    def test_validation_and_budget(self):
        for bad in ({}, {"layers": []}, {"layers": [3]}, {"layers": [0], "every": 0}, {"layers": [0], "passes": ["x"]},
                    {"layers": [0], "step_range": [2, 1]}):
            with self.assertRaises(InternalsError, msg=str(bad)):
                self.spec({"capture": bad})
        with self.assertRaises(InternalsError) as cm:
            self.spec({"capture": {"layers": "all", "full": True}}, max_capture_bytes=1000)
        self.assertIn("MiB", str(cm.exception))


class SteerTests(Base):
    def vec(self, shape=(HID,), seed=0):
        return torch.randn(*shape, generator=torch.Generator().manual_seed(seed)).numpy()

    def upload(self, arr, npz_key=None):
        b = io.BytesIO()
        np.savez(b, **{npz_key: arr}) if npz_key else np.save(b, arr)
        return b.getvalue()

    def test_alpha_zero_is_noop_and_alpha_adds_to_noisy_frames_only(self):
        v = self.vec()
        up = {"v.npy": self.upload(v)}
        base, _ = self.go()
        z, rec = self.go({"steer": {"alpha": 0.0, "vectors": [{"layer": 1, "file": "v.npy"}]}}, uploads=up)
        self.assertTrue(torch.equal(base, z))
        self.assertTrue(rec.steered)
        self.assertRestored()
        # layer 0 is the first steered block, so its captured output is exactly baseline + alpha*v on the noisy frames
        raw = {"capture": {"layers": [0], "step_range": [0, 1]}}
        _, rec0 = self.go(raw)
        out, rec1 = self.go({"capture": raw["capture"], "steer": {"alpha": 2.0, "vectors": [{"layer": 0, "file": "v.npy"}], "step_range": [0, 1]}}, uploads=up)
        d = rec1.arrays["s000_cond_L00_mean"] - rec0.arrays["s000_cond_L00_mean"]
        np.testing.assert_allclose(d[0], 0, atol=1e-6)  # frame 0 is the conditioning frame: untouched
        np.testing.assert_allclose(d[1:], np.tile(2.0 * v, (T - 1, 1)), atol=1e-5)
        base2, _ = self.go()
        self.assertFalse(torch.allclose(base2, out, atol=1e-4))
        self.assertRestored()

    def test_profile_per_frame_vector_include_conditioning_and_passes(self):
        v2 = self.vec((T, HID), 1)
        up = {"v.npz": self.upload(v2, "vec")}
        raw = {"alpha": 1.0, "vectors": [{"layer": 0, "file": "v.npz"}], "step_range": [0, 1], "frame_profile": [1.0, 0.0, 2.0],
               "include_conditioning_frames": True, "passes": "cond"}
        _, r0 = self.go({"capture": {"layers": [0], "step_range": [0, 1], "passes": "both"}})
        _, r1 = self.go({"capture": {"layers": [0], "step_range": [0, 1], "passes": "both"}, "steer": raw}, uploads=up)
        dc = r1.arrays["s000_cond_L00_mean"] - r0.arrays["s000_cond_L00_mean"]
        np.testing.assert_allclose(dc, v2 * np.array([[1.0], [0.0], [2.0]]), atol=1e-5)
        np.testing.assert_allclose(r1.arrays["s000_uncond_L00_mean"], r0.arrays["s000_uncond_L00_mean"], atol=1e-6)

    def test_vector_from_capture_artifact(self):
        spec = self.spec({"capture": {"layers": [2], "step_range": [0, 1]}})
        with internals.installed(self.pipe, spec) as rec:
            self.pipe.run_loop(self.packed, self.latents)
        aid = internals.save_capture(self.store, rec, spec, {})
        s = self.spec({"steer": {"alpha": 1, "vectors": [{"layer": 2, "artifact": aid, "key": "s000_cond_L02_mean"}]}})
        self.assertEqual(tuple(s.steer["vectors"][2].shape), (T, HID))
        s = self.spec({"steer": {"alpha": 1, "vectors": [{"layer": 2, "artifact": aid, "key": "s000_cond_L02_mean", "average_frames": True}]}})
        self.assertEqual(tuple(s.steer["vectors"][2].shape), (HID,))
        self.assertIn("sha256", s.raw["steer"]["vectors"][0]["resolved"])

    def test_clear_errors(self):
        good = {"layer": 0, "file": "v.npy"}
        up = {"v.npy": self.upload(self.vec()), "bad.npy": self.upload(self.vec((7,))), "t.npy": self.upload(self.vec((5, HID))),
              "i.npy": self.upload(np.arange(HID)), "n.npz": self.upload(self.vec(), "a")}
        cases = [({"alpha": 1}, "vectors"), ({"vectors": [good]}, "alpha"),
                 ({"alpha": 1, "vectors": [{"layer": 0, "file": "bad.npy"}]}, f"[{HID}]"),
                 ({"alpha": 1, "vectors": [{"layer": 0, "file": "t.npy"}]}, f"[{T}, {HID}]"),
                 ({"alpha": 1, "vectors": [{"layer": 0, "file": "i.npy"}]}, "float"),
                 ({"alpha": 1, "vectors": [{"layer": 0, "file": "missing.npy"}]}, "internals_files"),
                 ({"alpha": 1, "vectors": [{"layer": 9, "file": "v.npy"}]}, "out of range"),
                 ({"alpha": 1, "vectors": [{"layer": 0, "artifact": "act_00000000", "key": "k"}]}, "no artifact"),
                 ({"alpha": 1, "vectors": [good, good]}, "twice"),
                 ({"alpha": 1, "vectors": [good], "frame_profile": [1, 2]}, f"{T} numbers"),
                 ({"alpha": 1, "vectors": [good], "step_range": [0, 9]}, "step_range"),
                 ({"alpha": 1, "vectors": [good], "passes": "x"}, "passes"),
                 ({"alpha": float("nan"), "vectors": [good]}, "finite"), ({"alpha": 1, "vectors": [{"layer": 0}]}, "artifact")]
        for steer, frag in cases:
            with self.assertRaises(InternalsError, msg=str(steer)) as cm:
                self.spec({"steer": steer}, uploads=up)
            self.assertIn(frag, str(cm.exception), msg=str(steer))
        s = self.spec({"steer": {"alpha": 1, "vectors": [{"layer": 0, "values": [0.5] * HID}]}})
        self.assertEqual(tuple(s.steer["vectors"][0].shape), (HID,))
        with self.assertRaises(InternalsError):
            self.spec({"steer": {"alpha": 1, "vectors": [{"layer": 0, "values": [0.5] * 5}]}})
        # an .npz with one array needs no key
        self.spec({"steer": {"alpha": 1, "vectors": [{"layer": 0, "file": "n.npz"}]}}, uploads=up)


class RestoreTests(Base):
    RAW = {"rope": {"temporal_scale": 0.7}, "conditioning": {"noise": {"level": 0.3}, "attention_scale": {"factor": 0.5}},
           "capture": {"layers": "all", "passes": "both"}, "steer": {"alpha": 1.0, "vectors": [{"layer": 1, "file": "v.npy"}]}}

    def setUp(self):
        super().setUp()
        b = io.BytesIO(); np.save(b, np.ones(HID, np.float32))
        self.up = {"v.npy": b.getvalue()}

    def test_everything_is_removed_after_success_and_after_failure(self):
        base, _ = self.go()
        out, rec = self.go(self.RAW, uploads=self.up)
        self.assertFalse(torch.allclose(base, out, atol=1e-4))
        self.assertRestored()
        spec = self.spec(self.RAW, uploads=self.up)
        with self.assertRaises(RuntimeError):
            with internals.installed(self.pipe, spec):
                self.pipe.call(self.packed, self.latents)
                raise RuntimeError("request failed mid-way")
        self.assertRestored()
        # a failure INSIDE a hook (steering vector with the wrong frame count at run time) also leaves no residue
        bad = self.spec({"steer": {"alpha": 1, "vectors": [{"layer": 0, "file": "v.npy"}]}}, uploads=self.up)
        bad.steer["vectors"][0] = torch.ones(5, HID)
        with self.assertRaises(RuntimeError):
            with internals.installed(self.pipe, bad):
                self.pipe.run_loop(self.packed, self.latents)
        self.assertRestored()
        after, _ = self.go()
        self.assertTrue(torch.equal(base, after))  # same code path, same outputs as before any request

    def test_step_outside_the_loop_is_inert(self):
        spec = self.spec({"steer": {"alpha": 5, "vectors": [{"layer": 0, "file": "v.npy"}], "step_range": [0, 1]}}, uploads=self.up)
        base = self.pipe.call(self.packed, self.latents)
        with internals.installed(self.pipe, spec) as rec:
            out = self.pipe.call(self.packed, self.latents)  # current_timestep is None -> step -1 -> no hook acts
        self.assertTrue(torch.equal(base, out))
        self.assertEqual(rec.steered, [])

    def test_unknown_and_empty_specs(self):
        for bad in ({}, {"foo": 1}, [], "x"):
            with self.assertRaises(InternalsError):
                self.spec(bad)


if __name__ == "__main__":
    unittest.main()
