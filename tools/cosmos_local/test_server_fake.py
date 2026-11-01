"""End-to-end test of server.py with a FAKE pipeline (tiny real transformer, CPU, loopback port): the real FastAPI routes,
multipart parsing, sidecar, artifact download, 400 validation and hook cleanup. No GPU, no weights, no other host touched.
Run: python test_server_fake.py"""
import importlib.util, io, json, socket, sys, tempfile, threading, time, unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import requests
import torch
import uvicorn
import diffusers
from diffusers.schedulers.scheduling_unipc_multistep import UniPCMultistepScheduler

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import internals, neg_meta
from fakes import FakePipe, hooks_left
import diffusers.models.transformers.transformer_cosmos3 as tc


ORIG = []


class ServerPipe(FakePipe):
    """FakePipe plus what server.py's request path needs: components, a real UniPC scheduler, __call__."""
    components = {}

    @classmethod
    def from_pretrained(cls, *a, **k):
        return cls()

    def __init__(self):
        super().__init__(steps=3)
        self.scheduler = UniPCMultistepScheduler(use_flow_sigmas=True, prediction_type="flow_prediction", flow_shift=10.0)
        self.calls = []
        for a in neg_meta._ATTRS + ("duration_template", "image_resolution_template", "video_resolution_template"):
            setattr(self, a, a)

    def __call__(self, prompt, num_inference_steps=3, guidance_scale=6.0, num_frames=9, height=32, width=32, **kw):
        self.calls.append(dict(prompt=prompt, steps=num_inference_steps, guidance=guidance_scale, kw=kw))
        T = (num_frames - 1) // 4 + 1
        packed, latents = self.packed(T=T)
        self.scheduler.set_timesteps(num_inference_steps)
        acc = 0.0
        with torch.no_grad():
            for t in self.scheduler.timesteps:
                self._current_timestep = t
                acc += float(self.call(packed, latents, float(t) / 1000).abs().mean())
                if guidance_scale > 1:
                    acc += float(self.call(packed, latents, float(t) / 1000).abs().mean())
        self._current_timestep = None
        # a "video" that depends smoothly on what the transformer computed, so hook effects show up in the mp4
        ramp = np.linspace(0, 1, width, dtype=np.float32)[None, None, :, None]
        v = np.clip(0.2 + 0.6 * ramp * np.ones((num_frames, height, width, 3), np.float32) + 0.3 * np.sin(200 * acc), 0, 1)
        return SimpleNamespace(video=v)


def load_server(tmp):
    import diffusers as d
    d.Cosmos3OmniPipeline = ServerPipe
    sys.argv = ["server.py", "--out", str(tmp), "--port", "0"]
    spec = importlib.util.spec_from_file_location("server_under_test", HERE / "server.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["server_under_test"] = mod
    spec.loader.exec_module(mod)

    class CpuTorch:  # server.py asks for torch.Generator(device="cuda"); everything else is the real torch
        def __getattr__(self, name):
            return (lambda device="cpu": torch.Generator()) if name == "Generator" else getattr(torch, name)
    mod.torch = CpuTorch()
    return mod


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.mod = load_server(cls.tmp.name)
        s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
        cls.server = uvicorn.Server(uvicorn.Config(cls.mod.app, host="127.0.0.1", port=port, log_level="warning"))
        threading.Thread(target=cls.server.run, daemon=True).start()
        cls.url = f"http://127.0.0.1:{port}"
        for _ in range(100):
            try:
                requests.get(cls.url + "/health", timeout=1); break
            except Exception:
                time.sleep(0.1)
        ORIG.append(tc.dispatch_attention_fn)  # server.py imported cosmos_patch, so this is its chunked wrapper

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True
        cls.tmp.cleanup()

    def post(self, extra=None, files=None, **fields):
        data = dict(prompt="a ball", size="32x32", num_frames="9", num_inference_steps="3", seed="1", **fields)
        if extra is not None:
            data["extra_params"] = json.dumps(extra)
        return requests.post(self.url + "/v1/videos/sync", data=data, files=files, timeout=300)

    def sidecar(self, r):
        return json.loads((Path(self.tmp.name) / f"{r.headers['X-Clip-Id']}.json").read_text())

    def assertClean(self):
        pipe = self.mod.pipe
        self.assertEqual(hooks_left(pipe), {})
        self.assertIs(tc.dispatch_attention_fn, ORIG[0])
        self.assertNotIn("forward", pipe.transformer.rotary_emb.__dict__)

    def test_plain_request_has_no_internals_footprint(self):
        r = self.post(extra={"client": "t"})
        self.assertEqual(r.status_code, 200, r.text)
        self.assertTrue(r.content[4:8] == b"ftyp" and "X-Artifact-Ids" not in r.headers)
        side = self.sidecar(r)
        self.assertNotIn("internals", side)
        self.assertEqual(side["extra_params"], {"client": "t"})
        self.assertClean()
        self.assertEqual(self.post().content, self.post().content)  # same seed -> same bytes through the unchanged path

    def test_capture_then_download_then_steer_from_artifact(self):
        extra = {"client": "t", "internals": {"capture": {"layers": [1], "step_range": [0, 2]}}}
        r = self.post(extra=extra)
        self.assertEqual(r.status_code, 200, r.text)
        aid = r.headers["X-Artifact-Ids"]
        side = self.sidecar(r)
        self.assertEqual(side["internals"]["artifact_id"], aid)
        self.assertEqual(side["internals"]["capture"]["n_arrays"], 2)
        self.assertNotIn("internals", side["extra_params"])
        a = requests.get(f"{self.url}/v1/artifacts/{aid}")
        self.assertEqual(a.status_code, 200)
        z = np.load(io.BytesIO(a.content))
        self.assertEqual(z["s000_cond_L01_mean"].shape, (3, 32))
        self.assertEqual(requests.get(f"{self.url}/v1/artifacts/act_00000000").status_code, 404)
        self.assertEqual(requests.get(f"{self.url}/v1/artifacts/..%2F..%2Fetc").status_code, 404)
        steer = {"steer": {"alpha": 0.0, "vectors": [{"layer": 1, "artifact": aid, "key": "s000_cond_L01_mean"}]}}
        r2 = self.post(extra={"internals": steer})
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertEqual(self.sidecar(r2)["internals"]["spec"]["steer"]["vectors"][0]["resolved"]["shape"], [3, 32])
        self.assertClean()

    def test_uploaded_vector_and_400s(self):
        v = io.BytesIO(); np.save(v, np.ones(32, np.float32))
        extra = {"internals": {"steer": {"alpha": 1.0, "vectors": [{"layer": 0, "file": "v.npy"}]}}}
        r = self.post(extra=extra, files=[("internals_files", ("v.npy", v.getvalue(), "application/octet-stream"))])
        self.assertEqual(r.status_code, 200, r.text)
        bad = io.BytesIO(); np.save(bad, np.ones(7, np.float32))
        for extra, files, frag in (
                ({"internals": {"steer": {"alpha": 1.0, "vectors": [{"layer": 0, "file": "v.npy"}]}}}, None, "internals_files"),
                ({"internals": {"steer": {"alpha": 1.0, "vectors": [{"layer": 0, "file": "v.npy"}]}}},
                 [("internals_files", ("v.npy", bad.getvalue(), "application/octet-stream"))], "expected [32]"),
                ({"internals": {"capture": {"layers": [7]}}}, None, "out of range"),
                ({"internals": {"rope": {"temporal_scale": {"1": 2}}}}, None, "not a temporal entry"),
                ({"internals": {"bogus": 1}}, None, "unknown key"),
                ({"internals": {"conditioning": {"attention_scale": {"factor": 1, "step_range": [0, 50]}}}}, None, "step_range")):
            r = self.post(extra=extra, files=files)
            self.assertEqual(r.status_code, 400, r.text)
            self.assertIn(frag, r.text)
        self.assertFalse(self.mod.STATE["busy"])
        self.assertClean()

    def test_failure_inside_the_pipeline_cleans_up_and_server_stays_usable(self):
        pipe = self.mod.pipe
        real = type(pipe).__call__
        def boom(self, *a, **k):
            self.transformer.layers[0](torch.zeros(1, 32), torch.zeros(1, 32), None) if False else None
            self._current_timestep = self.scheduler.timesteps[0] if len(self.scheduler.timesteps) else None
            raise RuntimeError("CUDA out of memory (simulated)")
        type(pipe).__call__ = boom
        try:
            extra = {"internals": {"rope": {"temporal_scale": 0.5}, "capture": {"layers": [0]},
                                   "conditioning": {"attention_scale": {"factor": 0.5}}}}
            r = self.post(extra=extra)
            self.assertEqual(r.status_code, 500)
            self.assertIn("simulated", r.text)
        finally:
            type(pipe).__call__ = real
        self.assertClean()
        self.assertFalse(self.mod.STATE["busy"])
        self.assertEqual(self.post().status_code, 200)

    def test_all_hooks_together_through_the_server(self):
        v = io.BytesIO(); np.save(v, np.ones(32, np.float32))
        extra = {"internals": {"rope": {"temporal_scale": {"0": 0.5}}, "conditioning": {"noise": {"level": 0.2}, "attention_scale": {"factor": 0.5, "step_range": [0, 2]}},
                               "capture": {"layers": [0, 2], "step_range": [0, 3], "every": 2, "full": True},
                               "steer": {"alpha": 0.5, "vectors": [{"layer": 1, "file": "v.npy"}], "frame_profile": [0, 1, 1]}}}
        r = self.post(extra=extra, files=[("internals_files", ("v.npy", v.getvalue(), "application/octet-stream"))])
        self.assertEqual(r.status_code, 200, r.text)
        side = self.sidecar(r)["internals"]
        self.assertEqual(side["capture"]["n_arrays"], 2 * 2 * 2)  # steps 0,2 x layers 0,2 x (mean, full)
        self.assertEqual(side["attention_scale_steps"], [0, 1])
        self.assertClean()

    def test_probe_endpoint(self):
        import av
        frames = (np.random.default_rng(0).random((9, 64, 96, 3)) * 255).astype(np.uint8)
        buf = io.BytesIO()
        with av.open(buf, "w", format="mp4") as c:
            s = c.add_stream("libx264", rate=24); s.width, s.height, s.pix_fmt = 96, 64, "yuv420p"; s.options = {"crf": "0"}
            for f in frames:
                for p in s.encode(av.VideoFrame.from_ndarray(f, format="rgb24")):
                    c.mux(p)
            for p in s.encode():
                c.mux(p)
        files = {"video": ("c.mp4", buf.getvalue(), "video/mp4")}
        settings = {"sigmas": [0.3, 0.7], "seeds": [1], "variants": ["forward", "reverse"]}
        r = requests.post(self.url + "/v1/probe/loss", data={"prompt": "a ball", "settings": json.dumps(settings)}, files=files, timeout=300)
        self.assertEqual(r.status_code, 200, r.text)
        j = r.json()
        self.assertEqual(len(j["rows"]), 4)
        self.assertEqual(j["fps"], 24.0)
        self.assertEqual(j["latent_shape"][2], 3)
        r2 = requests.post(self.url + "/v1/probe/loss", files=files,
                           data={"prompt": "a ball", "settings": json.dumps({**settings, "rope": {"temporal_scale": 0.5}})}, timeout=300)
        self.assertEqual(r2.status_code, 200, r2.text)
        self.assertNotEqual(j["rows"][0]["loss"], r2.json()["rows"][0]["loss"])
        self.assertEqual(r2.json()["settings"]["rope"], {"temporal_scale": 0.5})
        self.assertClean()
        # I2V with an image + 400s
        img = io.BytesIO(); __import__("PIL.Image").Image.fromarray(frames[0]).save(img, "PNG")
        r3 = requests.post(self.url + "/v1/probe/loss", data={"prompt": "a ball", "settings": json.dumps(settings)},
                           files={**files, "image": ("i.png", img.getvalue(), "image/png")}, timeout=300)
        self.assertEqual(r3.json()["conditioning_frames"], [0])
        for bad in ({"sigmas": [2]}, {"num_frames": 7}, {"size": "50x50"}, {"rope": {"temporal_scale": {"1": 2}}}):
            rb = requests.post(self.url + "/v1/probe/loss", data={"prompt": "a", "settings": json.dumps(bad)}, files=files, timeout=60)
            self.assertEqual(rb.status_code, 400, (bad, rb.text))
        rb = requests.post(self.url + "/v1/probe/loss", data={"prompt": "a"}, files={"video": ("c.mp4", b"not a video")}, timeout=60)
        self.assertEqual(rb.status_code, 400, rb.text)
        self.assertFalse(self.mod.STATE["busy"])


if __name__ == "__main__":
    unittest.main()
